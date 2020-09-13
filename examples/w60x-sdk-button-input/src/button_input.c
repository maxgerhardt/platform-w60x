#include "wm_include.h"

#define portTICK_PERIOD_MS			( ( portTickType ) 1000 / configTICK_RATE_HZ )

void UserMain(void)
{
    //initialize onboard LED and button on wizfi board
	tls_gpio_cfg(WM_IO_PB_07, WM_GPIO_DIR_OUTPUT, WM_GPIO_ATTR_FLOATING);
	tls_gpio_cfg(WM_IO_PB_14, WM_GPIO_DIR_INPUT, WM_GPIO_ATTR_PULLHIGH);
    u8 button_pressed = 0;

	while(1) {
        button_pressed = tls_gpio_read(WM_IO_PB_14);
        //since button is pulled-high in its normal state, when the
        //button is pressed, it reads as 0. So, invert the value here.
        button_pressed ^= 1;
        printf("button pressed: %d\n", (int) button_pressed);
		tls_gpio_write(WM_IO_PB_07, button_pressed);
		tls_os_time_delay(100 / portTICK_PERIOD_MS);
	}
}
