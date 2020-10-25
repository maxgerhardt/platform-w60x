#include "wm_include.h"

#define portTICK_PERIOD_MS			( ( portTickType ) 1000 / configTICK_RATE_HZ )

//#define BLINKY_PIN WM_IO_PB_07
//#define BLINKY_PIN WM_IO_PB_10
#define BLINKY_PIN WM_IO_PA_00

void UserMain(void)
{
	tls_gpio_cfg(BLINKY_PIN, WM_GPIO_DIR_OUTPUT, WM_GPIO_ATTR_FLOATING);
	u8 led_val = 0;
	while(1) {
		printf("blinky2\n");
		tls_gpio_write(BLINKY_PIN, led_val);
		led_val ^= 1; 
		tls_os_time_delay(1000 / portTICK_PERIOD_MS);
	}
} 
