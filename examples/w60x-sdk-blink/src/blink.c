#include "wm_include.h"

#define portTICK_PERIOD_MS			( ( portTickType ) 1000 / configTICK_RATE_HZ )

void UserMain(void)
{
	tls_gpio_cfg(WM_IO_PB_07, WM_GPIO_DIR_OUTPUT, WM_GPIO_ATTR_FLOATING);
	u8 led_val = 0;
	while(1) {
		printf("blinky\n");
		tls_gpio_write(WM_IO_PB_07, led_val);
		led_val ^= 1;
		tls_os_time_delay(1000 / portTICK_PERIOD_MS);
	}
}
