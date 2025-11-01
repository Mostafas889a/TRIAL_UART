# Pad Map Documentation

## Overview

This document describes the mapping of UART peripheral signals to Caravel `mprj_io` pads.

## Caravel IO Overview

Caravel provides 38 configurable GPIO pins (`mprj_io[37:0]`) for user projects. Each IO has three control signals:
- `mprj_io_in[N]`: Input data from pad
- `mprj_io_out[N]`: Output data to pad
- `mprj_io_oeb[N]`: Output Enable Bar (active-low: 0=output, 1=input)

## Reserved Pads

The following pads are typically reserved and should be avoided:
- `mprj_io[4:0]`: Often used for system functions

## Default Pad Assignments

### UART0 Pad Assignments

| Signal | Pad Index | Direction | Description |
|--------|-----------|-----------|-------------|
| UART0_RX | mprj_io[6] | Input | UART0 Receive (input only) |
| UART0_TX | mprj_io[7] | Output | UART0 Transmit (output only) |

### UART1 Pad Assignments

| Signal | Pad Index | Direction | Description |
|--------|-----------|-----------|-------------|
| UART1_RX | mprj_io[8] | Input | UART1 Receive (input only) |
| UART1_TX | mprj_io[9] | Output | UART1 Transmit (output only) |

## Connection Details

### Input-Only Pins (RX)

For UART RX pins (input only):
```verilog
// Example: UART0_RX on mprj_io[6]
assign uart0_rx = mprj_io_in[6];
assign mprj_io_out[6] = 1'b0;      // Tie output low
assign mprj_io_oeb[6] = 1'b1;      // Disable output driver (input mode)
```

### Output-Only Pins (TX)

For UART TX pins (output only):
```verilog
// Example: UART0_TX on mprj_io[7]
assign mprj_io_out[7] = uart0_tx;
assign mprj_io_oeb[7] = 1'b0;      // Enable output driver (output mode)
```

## Complete Pad Connection Table

| Pad Index | Signal | Type | mprj_io_in | mprj_io_out | mprj_io_oeb | Notes |
|-----------|--------|------|------------|-------------|-------------|-------|
| 0-5 | Reserved | - | - | - | - | Reserved for system |
| 6 | UART0_RX | Input | uart0_rx | 1'b0 | 1'b1 | UART0 Receive |
| 7 | UART0_TX | Output | - | uart0_tx | 1'b0 | UART0 Transmit |
| 8 | UART1_RX | Input | uart1_rx | 1'b0 | 1'b1 | UART1 Receive |
| 9 | UART1_TX | Output | - | uart1_tx | 1'b0 | UART1 Transmit |
| 10-37 | Unused | - | - | 1'b0 | 1'b1 | Tied for input |

## Unused Pad Configuration

All unused pads should be configured as inputs with outputs tied low:
```verilog
// For unused pads (example: mprj_io[10])
assign mprj_io_out[10] = 1'b0;
assign mprj_io_oeb[10] = 1'b1;  // Input mode
```

## Pin Configuration in Firmware

The Caravel management SoC controls pad configuration through housekeeping SPI or direct register writes. For this design, pads are configured at the RTL level in `user_project_wrapper.v`.

Example firmware configuration (if needed):
```c
// Configure UART0 pads
reg_mprj_io_6  = GPIO_MODE_USER_STD_INPUT_NOPULL;   // UART0_RX
reg_mprj_io_7  = GPIO_MODE_USER_STD_OUTPUT;         // UART0_TX

// Configure UART1 pads
reg_mprj_io_8  = GPIO_MODE_USER_STD_INPUT_NOPULL;   // UART1_RX
reg_mprj_io_9  = GPIO_MODE_USER_STD_OUTPUT;         // UART1_TX

// Apply configuration
reg_mprj_xfer = 1;
while (reg_mprj_xfer == 1);
```

## How to Change Pad Assignments

To change the default pad assignments:

1. **Edit user_project_wrapper.v**:
   - Locate the signal assignments for UART RX/TX
   - Change the pad index numbers
   - Update the corresponding `mprj_io_out` and `mprj_io_oeb` assignments

2. **Update this documentation**:
   - Update the tables above with new pad assignments
   - Update firmware examples if provided

3. **Update test firmware**:
   - Update pad configuration in test C files
   - Update cocotb testbench if it configures pads

### Example: Moving UART0_TX to mprj_io[12]

Original:
```verilog
assign mprj_io_out[7] = uart0_tx;
assign mprj_io_oeb[7] = 1'b0;
```

Modified:
```verilog
// Mark old pad as unused
assign mprj_io_out[7] = 1'b0;
assign mprj_io_oeb[7] = 1'b1;

// Assign to new pad
assign mprj_io_out[12] = uart0_tx;
assign mprj_io_oeb[12] = 1'b0;
```

## Important Notes

1. **TX and RX on Different Pads**: UART TX and RX must always be on different GPIO pads. Never use the same pad for both.

2. **No Tristate Logic**: UART signals are unidirectional (TX is output only, RX is input only). No bidirectional configuration needed.

3. **Default States**: All unused outputs should be driven low, and all unused pads should be configured as inputs.

4. **Testing**: When testing with external tools, ensure the pad assignments match the physical connections on the test board.

## Physical Connection Example

For testing with external UART device:

```
Caravel Chip          External Device
-----------          ---------------
mprj_io[7] (TX0) --> RX
mprj_io[6] (RX0) <-- TX
mprj_io[9] (TX1) --> RX
mprj_io[8] (RX1) <-- TX
GND              --- GND
```

**Note**: UART TX on Caravel connects to RX on external device and vice versa.

## Electrical Characteristics

- **Voltage Level**: 1.8V (Caravel user IO domain)
- **Drive Strength**: Configurable via pad configuration
- **Pull-up/Pull-down**: Configurable via pad configuration
- **Maximum Frequency**: Limited by UART baud rate and pad slew rate

---
**Last Updated**: 2025-11-01
