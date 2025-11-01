# Integration Notes

## Overview

This document provides technical details about the integration of dual UART peripherals into the Caravel SoC, including clocking, reset strategy, bus architecture, interrupt routing, and verification procedures.

## Architecture

### System Block Diagram

```
Caravel Management SoC
         |
         | Wishbone B4 Bus
         |
    user_project
    +---------------------------------+
    |  Wishbone Decoder/Mux           |
    |  +---------------------------+  |
    |  | Address Decoder           |  |
    |  | (wbs_adr_i[19:16])       |  |
    |  +---------------------------+  |
    |         |              |        |
    |    +----v----+    +----v----+  |
    |    | UART0   |    | UART1   |  |
    |    | CF_UART |    | CF_UART |  |
    |    | _WB     |    | _WB     |  |
    |    +----+----+    +----+----+  |
    |         |              |        |
    +---------+--------------+--------+
              |              |
         TX0/RX0        TX1/RX1
              |              |
         mprj_io[7:6]  mprj_io[9:8]
```

## Clocking Strategy

### Clock Domain
- **Single Clock Domain**: All logic operates on `wb_clk_i` from Caravel
- **No Clock Gating**: Clock gating is disabled for simplicity and to avoid timing issues
- **No Derived Clocks**: No PLLs or clock dividers used

### Clock Specifications
- **Source**: Caravel management SoC clock (wb_clk_i)
- **Typical Frequency**: 10-50 MHz (Caravel dependent)
- **UART Baud Rate**: Configurable via prescaler register (PR)
- **Baud Rate Formula**: `baud_rate = wb_clk_i / ((PR+1) * SC)`
  - SC = 8 (samples per bit, fixed parameter)

### Clock Distribution
```verilog
// Clock routing in user_project_wrapper
wb_clk_i (from Caravel) -> user_project -> UART0 (clk_i)
                                        -> UART1 (clk_i)
```

**Important**: The CF_UART IP includes clock gating logic, but it is **disabled** in this integration by tying the GCLK register to always-on. This avoids timing closure issues during OpenLane.

## Reset Strategy

### Reset Architecture
- **Reset Type**: Synchronous reset, active-high
- **Reset Source**: Caravel management SoC (`wb_rst_i`)
- **Reset Distribution**: Direct connection to all modules

### Reset Sequence
```verilog
// Reset routing in user_project_wrapper
wb_rst_i (from Caravel) -> user_project -> UART0 (rst_i)
                                        -> UART1 (rst_i)
```

### Reset Behavior
- All UART registers reset to default values
- FIFOs are flushed
- Transmitters are disabled
- All interrupts are cleared

## Wishbone Bus Integration

### Bus Protocol
- **Standard**: Wishbone B4 (classic)
- **Data Width**: 32 bits
- **Address Width**: 32 bits
- **Byte Lanes**: 4 (`wbs_sel_i[3:0]`)

### Address Map
```
Base: 0x3000_0000 (User project space in Caravel)

0x3000_0000 - 0x3000_FFFF  UART0 (64 KB window)
0x3001_0000 - 0x3001_FFFF  UART1 (64 KB window)
0x3002_0000 - 0x30FF_FFFF  Reserved (return 0xDEADBEEF on read)
```

### Address Decoder Logic
The address decoder uses `wbs_adr_i[19:16]` to select peripherals:
- `4'b0000`: UART0 selected
- `4'b0001`: UART1 selected
- Others: Invalid (no ACK, return 0xDEADBEEF)

### Critical Implementation Rules

**RULE 1: Never gate `wbs_cyc_i`**
```verilog
// CORRECT: Route cyc_i directly to all slaves
assign uart0_cyc_i = wbs_cyc_i;
assign uart1_cyc_i = wbs_cyc_i;

// WRONG: Don't do this!
// assign uart0_cyc_i = wbs_cyc_i & uart0_sel;  // NEVER!
```

**RULE 2: Gate only `wbs_stb_i` for selection**
```verilog
// CORRECT: Use stb_i for peripheral selection
wire uart0_sel = (wbs_adr_i[19:16] == 4'b0000);
wire uart1_sel = (wbs_adr_i[19:16] == 4'b0001);

assign uart0_stb_i = wbs_stb_i & uart0_sel;
assign uart1_stb_i = wbs_stb_i & uart1_sel;
```

**RULE 3: One-hot selection**
Only one peripheral can be selected at a time. Selection is mutually exclusive.

**RULE 4: All transactions must be ACKed**
```verilog
// Combine ACKs from all slaves
assign wbs_ack_o = uart0_ack_o | uart1_ack_o | invalid_ack;

// Invalid address handling
reg invalid_ack;
always @(posedge wb_clk_i) begin
    if (wb_rst_i)
        invalid_ack <= 1'b0;
    else if (wbs_stb_i & wbs_cyc_i & ~uart0_sel & ~uart1_sel & ~invalid_ack)
        invalid_ack <= 1'b1;
    else
        invalid_ack <= 1'b0;
end
```

### Data Multiplexing
```verilog
// Read data multiplexer
always @(*) begin
    case (wbs_adr_i[19:16])
        4'b0000: wbs_dat_o = uart0_dat_o;
        4'b0001: wbs_dat_o = uart1_dat_o;
        default: wbs_dat_o = 32'hDEADBEEF;  // Invalid address
    endcase
end
```

### Bus Timing
- **Read Latency**: 1 cycle (data registered)
- **Write Latency**: 1 cycle (ACK on next cycle)
- **ACK Duration**: 1 cycle exactly

## Interrupt Routing

### UART Interrupt Sources
Each UART generates 10 interrupt sources:
1. TX FIFO Empty (TXE)
2. RX FIFO Full (RXF)
3. TX FIFO Below Threshold (TXB)
4. RX FIFO Above Threshold (RXA)
5. Line Break Detected (BRK)
6. Data Match Detected (MATCH)
7. Frame Error (FE)
8. Parity Error (PRE)
9. Overrun (OR)
10. Receiver Timeout (RTO)

### Interrupt Aggregation
Each CF_UART_WB instance provides a single IRQ output that is the OR of all enabled interrupt sources.

### Interrupt Routing to Caravel
Caravel provides 3 user interrupt lines: `user_irq[2:0]`

**Mapping**:
```verilog
assign user_irq[0] = uart0_irq;  // UART0 interrupt
assign user_irq[1] = uart1_irq;  // UART1 interrupt
assign user_irq[2] = 1'b0;       // Unused
```

### Interrupt Handling in Firmware
```c
// Enable UART0 RX interrupt
*(volatile uint32_t*)(0x30000000 + 0xFF00) = (1 << 1);  // IM register

// Check interrupt status
uint32_t status = *(volatile uint32_t*)(0x30000000 + 0xFF04);  // MIS register

// Clear interrupt
*(volatile uint32_t*)(0x30000000 + 0xFF0C) = (1 << 1);  // IC register (W1C)
```

## Power Considerations

### Power Domains
- **Core Power**: vccd1 (1.8V) - Caravel management SoC
- **User Power**: vccd2 (1.8V) - User project area
- **Ground**: vssd2 - User project ground

### Power Connections in user_project_wrapper
```verilog
`ifdef USE_POWER_PINS
    .vccd2(vccd2),
    .vssd2(vssd2),
`endif
```

### Clock Gating Status
Clock gating is **DISABLED** in this integration:
- Simplifies timing closure
- Reduces OpenLane complexity
- Power penalty is acceptable for this design

## File Structure

```
TRIAL_UART/
├── rtl/
│   └── user_project.v              # Top-level with WB decoder/mux
├── verilog/
│   └── rtl/
│       ├── user_project_wrapper.v  # Caravel wrapper with pad connections
│       └── user_project.v          # Symbolic link to rtl/user_project.v
├── ip/
│   ├── link_IPs.json               # IPM linker configuration
│   └── CF_UART/                    # Linked IP (created by ipm_linker)
```

## Dependencies

### Pre-installed IPs Used
- **CF_UART v2.0.1**: Located at `/nc/ip/CF_UART/v2.0.1/`
  - Core IP: `hdl/rtl/CF_UART.v`
  - Wishbone wrapper: `hdl/rtl/bus_wrappers/CF_UART_WB.v`
  - Firmware driver: `fw/CF_UART.h`, `fw/CF_UART.c`

### IP Linking
Use the IPM linker tool to link CF_UART into the project:
```bash
python /nc/agent_tools/ipm_linker/ipm_linker.py \
    --file /workspace/TRIAL_UART/ip/link_IPs.json \
    --project-root /workspace/TRIAL_UART
```

### Verilog Source Files
Required files for synthesis/simulation:
```
ip/CF_UART/hdl/rtl/CF_UART.v
ip/CF_UART/hdl/rtl/bus_wrappers/CF_UART_WB.v
rtl/user_project.v
verilog/rtl/user_project_wrapper.v
```

## Verification Strategy

### Verification Levels

1. **Module-Level**: Test individual UART instances
2. **Integration-Level**: Test user_project with both UARTs
3. **System-Level**: Test via Caravel-cocotb framework

### Test Cases

#### UART0 Tests
- Basic TX/RX loopback
- FIFO operations
- Baud rate configuration
- Interrupt generation
- Error conditions (parity, frame, overrun)

#### UART1 Tests
- Same as UART0
- Verify independence from UART0

#### System Integration Tests
- Concurrent operation of both UARTs
- Wishbone bus arbitration
- Interrupt priority
- Address decoding correctness
- Invalid address handling

### Verification Tools

**Caravel-Cocotb Framework**:
- Python-based testbenches
- Firmware-driven tests
- Waveform generation (VCD)
- Self-checking tests

**Directory Structure**:
```
verilog/dv/cocotb/
├── uart0_test/
│   ├── uart0_test.py
│   └── uart0_test.c
├── uart1_test/
│   ├── uart1_test.py
│   └── uart1_test.c
├── system_test/
│   ├── system_test.py
│   └── system_test.c
├── cocotb_tests.py
└── design_info.yaml
```

### Running Tests
```bash
# Run all tests
cd verilog/dv/cocotb
python cocotb_tests.py

# Run specific test
python cocotb_tests.py -t uart0_test
```

## Synthesis and PnR

### OpenLane Flow

**Two-stage process**:
1. Harden user_project (the UART integration logic)
2. Harden user_project_wrapper (includes user_project as macro)

### Stage 1: Harden user_project
```bash
openlane /workspace/TRIAL_UART/openlane/user_project/config.json \
    --ef-save-views-to /workspace/TRIAL_UART
```

### Stage 2: Harden user_project_wrapper
```bash
openlane /workspace/TRIAL_UART/openlane/user_project_wrapper/config.json \
    --ef-save-views-to /workspace/TRIAL_UART
```

### Key Configuration Parameters

**user_project/config.json**:
```json
{
    "DESIGN_NAME": "user_project",
    "FP_PDN_MULTILAYER": false,
    "CLOCK_PORT": "wb_clk_i",
    "CLOCK_PERIOD": 25,
    "VERILOG_FILES": [
        "dir::../../ip/CF_UART/hdl/rtl/CF_UART.v",
        "dir::../../ip/CF_UART/hdl/rtl/bus_wrappers/CF_UART_WB.v",
        "dir::../../rtl/user_project.v"
    ]
}
```

**user_project_wrapper/config.json**:
```json
{
    "MACROS": {
        "user_project": {
            "gds": ["dir::../../gds/user_project.gds"],
            "lef": ["dir::../../lef/user_project.lef"],
            "instances": {
                "mprj": {
                    "location": [1500, 1500],
                    "orientation": "N"
                }
            }
        }
    }
}
```

## Linting

### Verilator Lint
```bash
# Lint user_project
verilator --lint-only --Wno-EOFNEWLINE \
    -I./ip/CF_UART/hdl/rtl \
    ./rtl/user_project.v

# Lint user_project_wrapper
verilator --lint-only --Wno-EOFNEWLINE \
    -I./ip/CF_UART/hdl/rtl \
    ./verilog/rtl/user_project_wrapper.v
```

## Common Issues and Solutions

### Issue 1: Wishbone Bus Hangs
**Symptom**: Simulation hangs during bus transaction

**Cause**: Missing ACK on bus transaction

**Solution**: Ensure all transactions are ACKed, including invalid addresses

### Issue 2: Clock Gating Timing Violations
**Symptom**: OpenLane reports timing violations in clock gating cells

**Cause**: CF_UART includes clock gating logic

**Solution**: Disable clock gating by tying GCLK register high (done in this design)

### Issue 3: Interrupt Not Firing
**Symptom**: UART interrupt not reaching firmware

**Cause**: Interrupt not enabled in IM register or not routed correctly

**Solution**: 
1. Set appropriate bit in IM register (0xFF00)
2. Verify interrupt routing in user_project_wrapper
3. Check Caravel interrupt controller configuration

### Issue 4: Wrong Data on Read
**Symptom**: Reading from UART returns incorrect data

**Cause**: Data multiplexer not selecting correct source

**Solution**: Verify address decoder logic and mux case statement

### Issue 5: TX/RX Not Working
**Symptom**: No data transmitted or received

**Cause**: 
1. Pads not configured correctly
2. UART not enabled (CTRL register)
3. Wrong baud rate

**Solution**:
1. Check pad assignments in user_project_wrapper
2. Enable UART: Write 0x07 to CTRL register (EN | TX_EN | RX_EN)
3. Set correct prescaler value in PR register

## Design Checklist

Before considering the design complete, verify:

- [ ] Address map implemented correctly (no overlaps)
- [ ] `wbs_cyc_i` routed directly to all slaves (not gated)
- [ ] `wbs_stb_i` gated for peripheral selection
- [ ] All Wishbone transactions ACKed (including invalid)
- [ ] Invalid reads return 0xDEADBEEF
- [ ] One-hot selection enforced
- [ ] Read data registered (1-cycle latency)
- [ ] Byte-lane writes supported (`wbs_sel_i`)
- [ ] Interrupts routed to `user_irq`
- [ ] Pads configured correctly (TX output, RX input)
- [ ] Clock gating disabled
- [ ] Single clock domain
- [ ] Synchronous reset used
- [ ] No latches inferred
- [ ] Verilator lint clean
- [ ] All cocotb tests pass
- [ ] OpenLane synthesis clean
- [ ] Documentation complete

## References

### Internal Documentation
- [Register Map](register_map.md)
- [Pad Map](pad_map.md)
- [README](../README.md)

### External Documentation
- CF_UART IP: `/nc/ip/CF_UART/v2.0.1/README.md`
- Caravel Documentation: https://caravel-harness.readthedocs.io
- Wishbone B4 Specification: https://cdn.opencores.org/downloads/wbspec_b4.pdf

### Tools
- IPM Linker: `/nc/agent_tools/ipm_linker/`
- OpenLane: https://openlane2.readthedocs.io
- Caravel-Cocotb: https://github.com/efabless/caravel-cocotb

---
**Last Updated**: 2025-11-01
