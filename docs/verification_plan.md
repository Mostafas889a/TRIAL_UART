# Verification Plan - Dual UART Integration in Caravel

**Project**: Dual UART Integration in Caravel SoC  
**Date**: 2025-11-01  
**Clock Frequency**: 40 MHz (25 ns period)  
**Verification Framework**: Caravel-Cocotb  

---

## 1. Verification Objectives

### Primary Goals
1. Verify correct Wishbone B4 (classic) bus integration for 2x UART peripherals
2. Validate address decoding and multiplexing logic
3. Confirm proper pad connections (TX/RX on separate GPIOs)
4. Verify interrupt routing to `user_irq[2:0]`
5. Ensure functional operation of both UART instances independently and concurrently

### Secondary Goals
1. Verify error handling (invalid addresses return 0xDEADBEEF)
2. Validate ACK generation for all transactions
3. Confirm no bus hangs or timeout conditions
4. Verify proper reset behavior

---

## 2. Design Under Test (DUT)

### Module Hierarchy
```
user_project_wrapper
  └── user_project
      ├── CF_UART_WB (uart0_inst) @ 0x3000_0000
      └── CF_UART_WB (uart1_inst) @ 0x3001_0000
```

### Address Map
| Peripheral | Base Address  | Address Range          | GPIO Pins (TX/RX) |
|------------|---------------|------------------------|-------------------|
| UART0      | 0x3000_0000   | 0x3000_0000-0x3000_FFFF| io[7]/io[6]       |
| UART1      | 0x3001_0000   | 0x3001_0000-0x3001_FFFF| io[9]/io[8]       |

### Interrupt Mapping
- `user_irq[0]` → UART0 interrupt
- `user_irq[1]` → UART1 interrupt
- `user_irq[2]` → Unused (tied to 0)

---

## 3. Verification Strategy

### 3.1 Test Levels

#### Level 1: Basic Connectivity Tests
- **Purpose**: Verify basic firmware execution and GPIO signaling
- **Coverage**: Management GPIO handshake, basic Wishbone access

#### Level 2: Individual Peripheral Tests
- **Purpose**: Verify each UART peripheral independently
- **Tests**:
  - `uart0_test`: Test UART0 functionality
  - `uart1_test`: Test UART1 functionality
- **Coverage**: 
  - Configuration register access
  - TX/RX data transmission
  - FIFO operations
  - Baud rate configuration
  - Interrupt generation

#### Level 3: System Integration Tests
- **Purpose**: Verify system-level integration and concurrent operation
- **Test**: `system_test`
- **Coverage**:
  - Both UARTs operating simultaneously
  - Address decoding correctness
  - No cross-talk between peripherals
  - Invalid address handling

---

## 4. Test Specifications

### 4.1 Basic Test (`basic_test`)

**Objectives**:
- Verify firmware can execute
- Verify management GPIO signaling works
- Verify user interface can be enabled
- Verify GPIO pad configuration

**Test Sequence**:
1. Firmware initializes management GPIO
2. Firmware disables housekeeping SPI
3. Firmware configures UART GPIO pads (6-9)
4. Firmware enables user interface
5. Firmware signals completion via management GPIO pulse
6. Python test waits for management GPIO pulse
7. Python test verifies GPIO configuration

**Expected Results**:
- Management GPIO pulse detected
- Test completes without timeout
- GPIO pads configured correctly

**Pass Criteria**:
- All firmware initialization steps complete
- Management GPIO handshake successful

---

### 4.2 UART0 Test (`uart0_test`)

**Objectives**:
- Verify UART0 register access via Wishbone
- Verify UART0 TX functionality
- Verify UART0 RX functionality (if loopback)
- Verify UART0 interrupt generation

**Test Sequence**:
1. Firmware configures UART0 GPIO pads (TX=7, RX=6)
2. Firmware enables user interface
3. Firmware signals ready (pulse count: 1)
4. Firmware initializes UART0:
   - Enable clock (`CF_UART_setGclkEnable`)
   - Enable UART (`CF_UART_enable`)
   - Set baud rate to 115200 (40 MHz clock)
   - Enable TX and RX
5. Firmware signals UART0 enabled (pulse count: 2)
6. Firmware transmits test message: "Hello UART0\n"
7. Python test receives message via UART class
8. Python test validates received message
9. Firmware signals test complete (pulse count: 3)

**Baud Rate Calculation**:
```
Clock Frequency: 40 MHz
Baud Rate: 115200
Prescaler = (40,000,000 / (115200 * 8)) - 1 = 42.40 ≈ 42
```

**Expected Results**:
- UART0 configuration successful
- Message "Hello UART0" received correctly
- No transmission errors

**Pass Criteria**:
- Received message matches expected string
- All handshake pulses detected
- No timeout

---

### 4.3 UART1 Test (`uart1_test`)

**Objectives**:
- Verify UART1 register access via Wishbone
- Verify UART1 TX functionality
- Verify UART1 RX functionality (if loopback)
- Verify UART1 interrupt generation

**Test Sequence**:
1. Firmware configures UART1 GPIO pads (TX=9, RX=8)
2. Firmware enables user interface
3. Firmware signals ready (pulse count: 1)
4. Firmware initializes UART1:
   - Enable clock
   - Enable UART
   - Set baud rate to 115200 (40 MHz clock)
   - Enable TX and RX
5. Firmware signals UART1 enabled (pulse count: 2)
6. Firmware transmits test message: "Hello UART1\n"
7. Python test receives message via UART class
8. Python test validates received message
9. Firmware signals test complete (pulse count: 3)

**Expected Results**:
- UART1 configuration successful
- Message "Hello UART1" received correctly
- No transmission errors

**Pass Criteria**:
- Received message matches expected string
- All handshake pulses detected
- No timeout

---

### 4.4 System Integration Test (`system_test`)

**Objectives**:
- Verify both UARTs can operate concurrently
- Verify address decoding isolates peripherals
- Verify no cross-talk between UARTs
- Verify invalid address handling

**Test Sequence**:
1. Firmware configures both UART GPIO pads
2. Firmware enables user interface
3. Firmware signals ready (pulse count: 1)
4. Firmware initializes UART0
5. Firmware initializes UART1
6. Firmware signals both UARTs enabled (pulse count: 2)
7. Firmware transmits on UART0: "UART0: Test\n"
8. Python test receives from UART0
9. Firmware signals UART0 transmission complete (pulse count: 3)
10. Firmware transmits on UART1: "UART1: Test\n"
11. Python test receives from UART1
12. Firmware signals UART1 transmission complete (pulse count: 4)
13. Firmware tests invalid address (0x3002_0000)
14. Firmware verifies read returns 0xDEADBEEF
15. Firmware signals test complete (pulse count: 5)

**Expected Results**:
- Both UARTs transmit independently
- Messages received on correct GPIO pins
- No interference between UARTs
- Invalid address returns 0xDEADBEEF
- Invalid address transaction is ACKed

**Pass Criteria**:
- All messages received correctly
- No cross-talk detected
- Invalid address handling correct
- All handshake pulses detected

---

## 5. Coverage Goals

### 5.1 Functional Coverage

| Feature                          | Coverage Target | Verification Method |
|----------------------------------|-----------------|---------------------|
| Wishbone address decode (UART0)  | 100%            | uart0_test          |
| Wishbone address decode (UART1)  | 100%            | uart1_test          |
| Wishbone read operations         | 100%            | All tests           |
| Wishbone write operations        | 100%            | All tests           |
| Invalid address handling         | 100%            | system_test         |
| UART0 TX functionality           | 100%            | uart0_test          |
| UART1 TX functionality           | 100%            | uart1_test          |
| UART0 RX functionality           | Optional        | Future enhancement  |
| UART1 RX functionality           | Optional        | Future enhancement  |
| GPIO pad configuration           | 100%            | All tests           |
| Interrupt generation (UART0)     | Optional        | Future enhancement  |
| Interrupt generation (UART1)     | Optional        | Future enhancement  |
| Concurrent operation             | 100%            | system_test         |
| Reset behavior                   | 100%            | Framework default   |

### 5.2 Code Coverage

| Metric                | Target |
|-----------------------|--------|
| Line Coverage         | >90%   |
| Branch Coverage       | >80%   |
| FSM Coverage          | 100%   |

---

## 6. Test Environment

### 6.1 Simulation Configuration

**File**: `verilog/dv/cocotb/design_info.yaml`

```yaml
CARAVEL_ROOT: "/tools/caravel/"
MCW_ROOT: "/tools/caravel_mgmt_soc_litex/"
USER_PROJECT_ROOT: "/workspace/TRIAL_UART/"
PDK_ROOT: "/tools/share/pdk"
PDK: sky130A
clk_period_ns: 25
caravan: false
emailto: [None]
```

### 6.2 HDL Include Files

**RTL Includes** (`verilog/includes/includes.rtl.caravel_user_project`):
```
-v $(USER_PROJECT_VERILOG)/rtl/user_project_wrapper.v
-v $(USER_PROJECT_VERILOG)/rtl/user_project.v
-v $(USER_PROJECT_VERILOG)/../ip/CF_UART/hdl/rtl/CF_UART.v
-v $(USER_PROJECT_VERILOG)/../ip/CF_UART/hdl/rtl/bus_wrappers/CF_UART_WB.v
-v $(USER_PROJECT_VERILOG)/../ip/CF_IP_UTIL/hdl/cf_util_lib.v
```

### 6.3 Firmware APIs

**CF_UART Firmware APIs** (from `ip/CF_UART/fw/`):
- `CF_UART_setGclkEnable(uart, enable)`
- `CF_UART_enable(uart)`
- `CF_UART_enableTx(uart)`
- `CF_UART_enableRx(uart)`
- `CF_UART_setPrescaler(uart, prescaler)`
- `CF_UART_writeChar(uart, char)`
- `CF_UART_readChar(uart)`
- `CF_UART_setTxFIFOThreshold(uart, threshold)`

---

## 7. Test Execution Plan

### 7.1 Test Sequence

1. **Setup Phase**:
   ```bash
   cd /workspace/TRIAL_UART
   python verilog/dv/setup-cocotb.py /workspace/TRIAL_UART
   ```

2. **RTL Simulation**:
   ```bash
   cd verilog/dv/cocotb
   timeout 600 caravel_cocotb -t basic_test -tag rtl_run
   timeout 600 caravel_cocotb -t uart0_test -tag rtl_run
   timeout 600 caravel_cocotb -t uart1_test -tag rtl_run
   timeout 600 caravel_cocotb -t system_test -tag rtl_run
   ```

3. **Gate-Level Simulation** (Future):
   ```bash
   timeout 600 caravel_cocotb -t basic_test -sim GL -tag gl_run
   timeout 600 caravel_cocotb -t uart0_test -sim GL -tag gl_run
   timeout 600 caravel_cocotb -t uart1_test -sim GL -tag gl_run
   timeout 600 caravel_cocotb -t system_test -sim GL -tag gl_run
   ```

### 7.2 Success Criteria

**For each test**:
- Test completes without timeout
- All assertions pass
- `sim/<tag>/<test>/passed` file is generated
- No fatal errors in `sim/<tag>/<test>/<test>.log`

**Overall**:
- All 4 tests pass in RTL simulation
- No synthesis warnings for user_project.v
- All functional coverage goals met

---

## 8. Known Limitations

1. **RX Loopback**: Current tests focus on TX functionality. RX testing requires external stimulus or loopback configuration.
2. **Interrupt Testing**: Interrupt functionality not tested in initial verification phase.
3. **FIFO Stress Testing**: FIFO overflow/underflow conditions not explicitly tested.
4. **Timing Analysis**: RTL simulation only; gate-level timing not yet verified.

---

## 9. Risk Assessment

| Risk                                  | Severity | Mitigation                                    |
|---------------------------------------|----------|-----------------------------------------------|
| Test timeout due to slow simulation   | Medium   | Use 600s timeout for caravel_cocotb commands  |
| Baud rate mismatch                    | Low      | Calculate prescaler carefully for 40 MHz clk  |
| GPIO pad configuration errors         | Low      | Verify pad configuration in basic_test        |
| Address decoding bugs                 | Medium   | Comprehensive system_test with invalid addr   |
| Wishbone protocol violations          | Low      | CF_UART_WB wrapper is pre-verified            |

---

## 10. Verification Checklist

- [ ] Verification plan reviewed and approved
- [ ] Test environment setup complete
- [ ] HDL include files configured
- [ ] All test firmware written
- [ ] All Python tests written
- [ ] All tests imported in `cocotb_tests.py`
- [ ] Basic test passes
- [ ] UART0 test passes
- [ ] UART1 test passes
- [ ] System integration test passes
- [ ] All logs reviewed for warnings/errors
- [ ] Coverage goals met
- [ ] Verification report generated

---

## 11. References

1. CF_UART IP Documentation: `/workspace/TRIAL_UART/ip/CF_UART/README.md`
2. CF_UART Firmware API: `/workspace/TRIAL_UART/ip/CF_UART/fw/`
3. Caravel-Cocotb Documentation: Microagent knowledge base
4. Wishbone B4 Specification
5. Register Map: `/workspace/TRIAL_UART/docs/register_map.md`
6. Pad Map: `/workspace/TRIAL_UART/docs/pad_map.md`
7. Integration Notes: `/workspace/TRIAL_UART/docs/integration_notes.md`

---

**Document Version**: 1.0  
**Status**: Ready for Implementation  
**Next Step**: Create test directory structure and implement tests
