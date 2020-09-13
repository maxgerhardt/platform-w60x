#include <Arduino.h>
#include <pins_arduino.h>

// pin mappings in this core are extremely screwed. 
// definitions like WM_IO_PB_07 are buggy and trigger
// "NOT support the function" messages. 
// follow https://github.com/w600/arduino/tree/master/variants 
// to see what pin you need
#define BLINKY_PIN 6
//#define BLINKY_PIN WM_IO_PB_07

void setup() {
    pinMode(BLINKY_PIN, OUTPUT);
}

void loop() {
    digitalWrite(BLINKY_PIN, HIGH);
    delay(1000);
    digitalWrite(BLINKY_PIN, LOW);
    delay(1000);
}