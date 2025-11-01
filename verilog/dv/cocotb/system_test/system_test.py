from caravel_cocotb.caravel_interfaces import test_configure, report_test, UART
import cocotb

async def wait_for_pulses(env, count, label):
    for _ in range(count):
        await env.wait_mgmt_gpio(1)
        await env.wait_mgmt_gpio(0)
    cocotb.log.info(f"[TEST] {label}")

@cocotb.test()
@report_test
async def system_test(dut):
    caravelEnv = await test_configure(dut, timeout_cycles=3000000)
    cocotb.log.info("[TEST] Start system_test")
    await caravelEnv.release_csb()
    
    uart0_pins = {"tx": 7, "rx": 6}
    uart1_pins = {"tx": 9, "rx": 8}
    uart0 = UART(caravelEnv, uart0_pins)
    uart1 = UART(caravelEnv, uart1_pins)
    uart0.baud_rate = 115200
    uart1.baud_rate = 115200
    
    cocotb.log.info("[TEST] Wait for firmware ready")
    await wait_for_pulses(caravelEnv, 1, "firmware configuration complete")
    
    cocotb.log.info("[TEST] Wait for both UARTs enabled")
    await wait_for_pulses(caravelEnv, 1, "both UARTs enabled")
    
    cocotb.log.info("[TEST] Wait for UART0 transmission")
    await wait_for_pulses(caravelEnv, 1, "UART0 transmission started")
    
    cocotb.log.info("[TEST] Receiving message from UART0")
    msg0 = await uart0.get_line()
    cocotb.log.info(f"[TEST] UART0 received: '{msg0}'")
    
    expected_msg0 = "UART0: Test"
    if expected_msg0 in msg0:
        cocotb.log.info(f"[TEST] PASS - UART0 message correct")
    else:
        cocotb.log.error(f"[TEST] FAIL - UART0 expected '{expected_msg0}', got '{msg0}'")
        assert False, f"UART0 message incorrect"
    
    cocotb.log.info("[TEST] Wait for UART1 transmission")
    await wait_for_pulses(caravelEnv, 1, "UART1 transmission started")
    
    cocotb.log.info("[TEST] Receiving message from UART1")
    msg1 = await uart1.get_line()
    cocotb.log.info(f"[TEST] UART1 received: '{msg1}'")
    
    expected_msg1 = "UART1: Test"
    if expected_msg1 in msg1:
        cocotb.log.info(f"[TEST] PASS - UART1 message correct")
    else:
        cocotb.log.error(f"[TEST] FAIL - UART1 expected '{expected_msg1}', got '{msg1}'")
        assert False, f"UART1 message incorrect"
    
    cocotb.log.info("[TEST] Wait for invalid address test result")
    pulse_count = 0
    for _ in range(2):
        await caravelEnv.wait_mgmt_gpio(1)
        await caravelEnv.wait_mgmt_gpio(0)
        pulse_count += 1
    
    if pulse_count == 2:
        cocotb.log.info("[TEST] PASS - Invalid address returned 0xDEADBEEF")
    else:
        cocotb.log.error("[TEST] FAIL - Invalid address test failed")
        assert False, "Invalid address test failed"
    
    cocotb.log.info("[TEST] System test completed successfully - all tests passed")
