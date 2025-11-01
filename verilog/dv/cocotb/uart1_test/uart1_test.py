from caravel_cocotb.caravel_interfaces import test_configure, report_test, UART
import cocotb

async def wait_for_pulses(env, count, label):
    for _ in range(count):
        await env.wait_mgmt_gpio(1)
        await env.wait_mgmt_gpio(0)
    cocotb.log.info(f"[TEST] {label}")

@cocotb.test()
@report_test
async def uart1_test(dut):
    caravelEnv = await test_configure(dut, timeout_cycles=2000000)
    cocotb.log.info("[TEST] Start uart1_test")
    await caravelEnv.release_csb()
    
    uart1_pins = {"tx": 9, "rx": 8}
    uart1 = UART(caravelEnv, uart1_pins)
    uart1.baud_rate = 115200
    
    cocotb.log.info("[TEST] Wait for firmware ready")
    await wait_for_pulses(caravelEnv, 1, "firmware configuration complete")
    
    cocotb.log.info("[TEST] Wait for UART1 enabled")
    await wait_for_pulses(caravelEnv, 1, "UART1 enabled")
    
    cocotb.log.info("[TEST] Wait for UART1 transmission")
    await wait_for_pulses(caravelEnv, 1, "UART1 transmission started")
    
    cocotb.log.info("[TEST] Receiving message from UART1")
    msg = await uart1.get_line()
    cocotb.log.info(f"[TEST] Received: '{msg}'")
    
    expected_msg = "Hello UART1"
    if expected_msg in msg:
        cocotb.log.info(f"[TEST] PASS - Received expected message: '{msg}'")
    else:
        cocotb.log.error(f"[TEST] FAIL - Expected '{expected_msg}', got '{msg}'")
        assert False, f"UART1 test failed: expected '{expected_msg}', got '{msg}'"
    
    cocotb.log.info("[TEST] UART1 test completed successfully")
