#include <GyverHX711.h>
GyverHX711 sensor(7, 8, HX_GAIN128_A);
// HX_A_GAIN128 - канал А усиление 128
// HX_B_GAIN32 - канал B усиление 32
// HX_A_GAIN64 - канал А усиление 64

void setup() {
  Serial.begin(9600);
  sensor.tare();		// калибровка нуля
  
  //sensor.sleepMode(true);		// выключить датчик
  //sensor.sleepMode(false);	// включить датчик
}

void loop() {
  // чтение только по доступности! if available
  if (sensor.available()) {
    Serial.println(sensor.read());
  }
}
