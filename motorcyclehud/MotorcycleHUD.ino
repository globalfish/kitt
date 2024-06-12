#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "ELMduino.h"
#include "BluetoothSerial.h"

//
// Setup I2C
//
//TwoWire myWire = TwoWire(0);
const int SDAPIN = 25;  //GPIO25 = Pin 9
const int SCLPIN = 26;  //GPIO26 = Pin 10

//
// setup OLED display
//
#define SCREEN_WIDTH 128  // OLED display width, in pixels
#define SCREEN_HEIGHT 64  // OLED display height, in pixels

const bool DEBUG = true;
const int TIMEOUT = 2000;
const bool HALT_ON_FAIL = false;

Adafruit_SSD1306 display1(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 display2(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

//
// setup Bluetooth on ESP32
//
BluetoothSerial SerialBT;
#define ELM_PORT SerialBT
#define DEBUG_PORT Serial
String device_name = "ArduHUD";

//
// ELM32& adapter details
//
ELM327 myELM327;
uint8_t adapter1Addr[6] = { 0x00, 0x1D, 0xA5, 0x00, 0xB1, 0xC0 };  //backup adapter for testing
uint8_t adapter2Addr[6] = { 0x00, 0x1D, 0xA5, 0x01, 0x72, 0x58 };  // adapter on bike for production

//
// using example code from https://github.com/PowerBroker2/ELMduino
//
typedef enum { ENG_RPM,
               SPEED } obd_pid_states;
obd_pid_states obd_state = ENG_RPM;
uint32_t rpm = 0;
uint32_t mph = 0;
void setup() {

  //
  // setup I2C with alternate pins for display
  //
  Wire.begin(SDAPIN, SCLPIN, 100000);
  //
  // Let's get the displays setup so we can show status/errors on them
  //
  // setup display1
  if (!display1.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {  // Address 0x3C for 128x64
    DEBUG_PORT.println(F("Display1: 0x3c: SSD1306 allocation failed"));
    for (;;)
      ;
  }
  // setup display2
  if (!display2.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {  // Address 0x3D for 128x64
    Serial.println(F("Display2: 0x78: SSD1306 allocation failed"));
    for (;;)
      ;
  }
  initDisplays();

  DEBUG_PORT.begin(115200);
  delay(1000);  // let's all calm down now

  //
  // connect to ELM327 device
  //
  // setup ESP32 BT device with name, as master, disable BLE
  ELM_PORT.begin(device_name, true, true);  //Bluetooth device name
  DEBUG_PORT.print("Serial (test)...");
  showText(&display1, "Serial (test)...");
  // connect by name "OBDII" did not work
  if (!ELM_PORT.connect(adapter1Addr, 0, ESP_SPP_SEC_NONE, ESP_SPP_ROLE_MASTER)) {
    DEBUG_PORT.println("failed.");
    showText(&display1, "failed");
    DEBUG_PORT.print("Serial (bike)...");
    showText(&display1, "Serial (bike)...");
    if (!ELM_PORT.connect(adapter2Addr, 0, ESP_SPP_SEC_NONE, ESP_SPP_ROLE_MASTER)) {
      DEBUG_PORT.println("failed. Aborting.");
      showText(&display1, "failed. Aborting.");
      while (1)
        ;
    }
  }
  DEBUG_PORT.println("...connected.");
  showText(&display2, "SERIAL OK");
  DEBUG_PORT.print("ELM connection...");
  showText(&display1, "ELM connection...");
  // param2 = true for debug
  if (!myELM327.begin(ELM_PORT, false, 2000)) {
    DEBUG_PORT.println("failed. Aborting.");
    showText(&display1, "failed. Aborting.");
    while (1)
      ;
  }
  DEBUG_PORT.println("connected.");
  showText(&display2, "ELM OK");

  delay(500);
}

void initDisplays() {
  display1.clearDisplay();
  display2.clearDisplay();
  display1.setRotation(2);
  display2.setRotation(2);
  showLabel(&display1, "HELLO");
  showLabel(&display2, "WORLD");
  delay(1000);
  showLabel(&display1, "RPM");
  showLabel(&display2, "SPEED");
}

void showLabel(Adafruit_SSD1306 *display, String label) {

  display->setTextSize(2);
  display->setTextColor(WHITE);
  display->setCursor(1, 1);  // set to the left so we can erase the whole block
  // clear label area of screen on top
  display->writeFillRect(0, 1, 100, 15, BLACK);

  display->setCursor(1, 1);
  display->print(label);
  display->display();
}

void showText(Adafruit_SSD1306 *display, char *text) {
  // clear value area of screen
  display->writeFillRect(0, 16, 128, 48, BLACK);

  display->setTextSize(2);
  display->setTextColor(WHITE);
  display->setTextWrap(true);

  display->setCursor(1, 20);

  display->print(text);
  display->display();
}


void showValue(Adafruit_SSD1306 *display, int value) {

  // clear value area of screen
  display->writeFillRect(0, 16, 128, 48, BLACK);

  display->setTextSize(5);
  display->setTextColor(WHITE);

  if (value < 10) {
    display->setCursor(91, 20);
  } else if (value > 9 && value < 100) {
    display->setCursor(61, 20);
  } else if (value > 99 && value < 1000) {
    display->setCursor(31, 20);
  } else {
    display->setCursor(1, 20);
  }
  display->print(value);
  display->display();
}


void loop() {

  int value;

  //
  // using the code from https://github.com/PowerBroker2/ELMduino
  // You have to finish reading one PID before trying the next one. Reading
  // is considered done once you get ELM_SUCCESS or some error has occurred
  //
  switch (obd_state) {
    case ENG_RPM:
    {
      float temprpm = myELM327.rpm();
      uint32_t oldrpm = rpm;
      rpm = (uint32_t)temprpm;
      if (myELM327.nb_rx_state == ELM_SUCCESS) {
        DEBUG_PORT.print("RPM: "); 
        DEBUG_PORT.println(rpm);
        // show speed to nearest 10 rpm
        if( abs((int)(rpm/10) - (int)(oldrpm/10)) > 0)
          showValue(&display1, ((int)(rpm/10))*10);
        obd_state = SPEED;
      } else if (myELM327.nb_rx_state == ELM_TIMEOUT) {
        DEBUG_PORT.println("timeout");
      } else if (myELM327.nb_rx_state == ELM_STOPPED) {
        DEBUG_PORT.println("Stopped.");
        showText(&display1, "ENGINE OFF");
      } else if (myELM327.nb_rx_state != ELM_GETTING_MSG) {
        myELM327.printError();
        obd_state = SPEED;
      }
      
      break;
    }
    
    case SPEED: {
      float tempmph =  myELM327.mph();
      mph = (uint32_t)tempmph;
      if (myELM327.nb_rx_state == ELM_SUCCESS) {
        DEBUG_PORT.print("MPH -->>> : "); 
        DEBUG_PORT.println(mph);
        showValue(&display2, mph);
        obd_state = ENG_RPM;
      } else if (myELM327.nb_rx_state == ELM_TIMEOUT) {
        DEBUG_PORT.println("timeout");
      } else if (myELM327.nb_rx_state == ELM_STOPPED) {
        DEBUG_PORT.println("Stopped.");
        showText(&display1, "ENGINE OFF");
      } else if (myELM327.nb_rx_state != ELM_GETTING_MSG) {
        myELM327.printError();
        obd_state = ENG_RPM;
      }
      
      break;
    }
  }
  
}
