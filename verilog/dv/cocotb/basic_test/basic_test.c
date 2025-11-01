#include <firmware_apis.h>

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

    return;
}

static void send_pulse(int count) {
    for (int i = 0; i < count; i++) {
        ManagmentGpio_write(1);
        ManagmentGpio_write(0);
    }
}
