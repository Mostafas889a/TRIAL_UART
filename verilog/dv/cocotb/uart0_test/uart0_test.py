from caravel_cocotb.caravel_interfaces import test_configure, report_test, UART
import cocotb

async def wait_for_pulses(env, count, label):
    for _ in range(count):
        await env.wait_mgmt_gpio(1)
        await env.wait_mgmt_gpio(0)
    cocotb.log.info(f"[TEST] {label}")

@cocotb.test()
@report_test
async def uart0_test(dut):
    caravelEnv = await test_configure(dut, timeout_cycles=2000000)
    cocotb.log.info("[TEST] Start uart0_test")
    await caravelEnv.release_csb()
    
    uart0_pins = {"tx": 7, "rx": 6}
    uart0 = UART(caravelEnv, uart0_pins)
    uart0.baud_rate = 115200
    
    cocotb.log.info("[TEST] Wait for firmware ready")
    await wait_for_pulses(caravelEnv, 1, "firmware configuration complete")
    
    cocotb.log.info("[TEST] Wait for UART0 enabled")
    await wait_for_pulses(caravelEnv, 1, "UART0 enabled")
    
    cocotb.log.info("[TEST] Wait for UART0 transmission")
    await wait_for_pulses(caravelEnv, 1, "UART0 transmission started")
    
    cocotb.log.info("[TEST] Receiving message from UART0")
    msg = await uart0.get_line()
    cocotb.log.info(f"[TEST] Received: '{msg}'")
    
    expected_msg = "Hello UART0"
    if expected_msg in msg:
        cocotb.log.info(f"[TEST] PASS - Received expected message: '{msg}'")
    else:
        cocotb.log.error(f"[TEST] FAIL - Expected '{expected_msg}', got '{msg}'")
        assert False, f"UART0 test failed: expected '{expected_msg}', got '{msg}'"
    
    cocotb.log.info("[TEST] UART0 test completed successfully")
