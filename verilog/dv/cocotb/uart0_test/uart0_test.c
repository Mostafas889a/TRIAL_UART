#include <firmware_apis.h>
#include "CF_UART.h"

#define UART0_BASE 0x30000000
#define UART0 ((CF_UART_TYPE_PTR)UART0_BASE)

static void send_pulse(int count);

void main(void) {
    ManagmentGpio_outputEnable();
    ManagmentGpio_write(0);
    enableHkSpi(0);

    GPIOs_configure(6, GPIO_MODE_USER_STD_INPUT_PULLUP);
    GPIOs_configure(7, GPIO_MODE_USER_STD_OUTPUT);
    GPIOs_configure(8, GPIO_MODE_USER_STD_INPUT_PULLUP);
    GPIOs_configure(9, GPIO_MODE_USER_STD_OUTPUT);
    GPIOs_loadConfigs();

    User_enableIF();
    send_pulse(1);

    CF_UART_setGclkEnable(UART0, 1);
    CF_UART_enable(UART0);
    CF_UART_setPrescaler(UART0, 42);
    CF_UART_setTxFIFOThreshold(UART0, 3);
    CF_UART_enableTx(UART0);
    CF_UART_enableRx(UART0);
    send_pulse(1);

    CF_UART_writeCharArr(UART0, "Hello UART0\n");
    send_pulse(1);

    return;
}

static void send_pulse(int count) {
    for (int i = 0; i < count; i++) {
        ManagmentGpio_write(1);
        ManagmentGpio_write(0);
    }
}
