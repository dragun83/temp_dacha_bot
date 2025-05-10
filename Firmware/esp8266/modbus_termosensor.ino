#ifdef ESP8266
 #include <ESP8266WiFi.h>
#else //ESP32
 #include <WiFi.h>
#endif
#include <ModbusIP_ESP8266.h>
#include <DS18B20.h>

//Modbus Registers Offsets
const int LED_COIL = 100;
const int ONEWIRE_PIN = 13;
const int TEMP_REG_START = 100;  // Начальный адрес для хранения float (Holding Registers)
const int ledPin = 2;
//ModbusIP object
ModbusIP mb;
DS18B20 ds(ONEWIRE_PIN);  

uint8_t dev_num = ds.getNumberOfDevices();

// Функция для преобразования float в два uint16_t
void floatToRegisters(float value, uint16_t* regs) {
  union {
    float f;
    uint16_t u[2];
  } converter;
  converter.f = value;
  regs[0] = converter.u[0];
  regs[1] = converter.u[1];
}

void setup() {
  Serial.begin(115200);
  WiFi.begin("dragun_wifi", "D9033001660gn");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
 
  Serial.println("\nWiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Number of sensors: ");
  Serial.println(dev_num);

  mb.server(502);
  pinMode(ledPin, OUTPUT);
  mb.addCoil(LED_COIL, true);

  // Регистры для хранения float (2 регистра на каждый датчик)
  for (uint8_t i = 0; i < dev_num; i++) {
    mb.addHreg(TEMP_REG_START + i * 2, 0);  // Младшее слово
    mb.addHreg(TEMP_REG_START + i * 2 + 1, 0);  // Старшее слово
  }
}
 
void loop() {
  mb.task();
  for (uint8_t i = 0; i < dev_num; i++) {
    ds.selectNext();
    float temp = ds.getTempC();
    //Serial.println(temp);
    uint16_t regs[2];
    floatToRegisters(temp, regs);
    mb.Hreg(TEMP_REG_START + i * 2, regs[0]);
    mb.Hreg(TEMP_REG_START + i * 2 + 1, regs[1]);
  }
  digitalWrite(ledPin, mb.Coil(LED_COIL));
}