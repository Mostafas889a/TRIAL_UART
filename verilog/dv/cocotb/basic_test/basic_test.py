from caravel_cocotb.caravel_interfaces import test_configure, report_test
import cocotb

async def wait_for_pulses(env, count, label):
    for _ in range(count):
        await env.wait_mgmt_gpio(1)
        await env.wait_mgmt_gpio(0)
    cocotb.log.info(f"[TEST] {label}")

@cocotb.test()
@report_test
async def basic_test(dut):
    caravelEnv = await test_configure(dut, timeout_cycles=1000000)
    cocotb.log.info("[TEST] Start basic_test")
    await caravelEnv.release_csb()
    
    cocotb.log.info("[TEST] Wait for management GPIO pulse (firmware ready)")
    await wait_for_pulses(caravelEnv, 1, "firmware configuration complete")
    
    cocotb.log.info("[TEST] Basic test passed - firmware executed successfully")
