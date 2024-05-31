//ThatsEngineering A
//Sending Data from Arduino to NodeMCU Via Serial Communication
//Arduino code

//DHT11 Lib

//Arduino to NodeMCU Lib
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

#include <Q2HX711.h>
#include <SPI.h>
#include <RFID.h>

#define buzz 7 //buzzer 

#define SS_PIN 10 //sda
#define RST_PIN 9 //rst
RFID rfid(SS_PIN, RST_PIN);

const byte hx711_data_pin = 3;
const byte hx711_clock_pin = 4;

//Initialise Arduino to NodeMCU (5=Rx & 6=Tx)
SoftwareSerial nodemcu(5, 6);

float y1 = 1005.0; // calibrated mass to be added
long x1 = 0;
long x0 = 0;
float avg_size = 10.0; // amount of averages for each mass measurement
long comp = 0;
long oldweight = 0;

String rfidCard;
String red = "";
Q2HX711 hx711(hx711_data_pin, hx711_clock_pin); // prep hx711


//Initialisation of DHT11 Sensor
#define DHTPIN 4
int hum;

void setup() {
  Serial.begin(115200);
  nodemcu.begin(115200);
  delay(1000);
  Serial.println("Program started");
  Serial.println("Starting the RFID Reader...");
  SPI.begin();
  rfid.init();
  
  delay(1000); // allow load cell and hx711 to settle
  // tare procedure
  for (int ii=0;ii<int(avg_size);ii++){
    delay(10);
    x0+=hx711.read();
  }
  x0/=long(avg_size);
  Serial.println("Add Calibrated Mass");
  // calibration procedure (mass should be added equal to y1)
  int ii = 1;
  while(true){
    if (hx711.read()<x0+10000){
    } else {
      ii++;
      delay(2000);
      for (int jj=0;jj<int(avg_size);jj++){
        x1+=hx711.read();
      }
      x1/=long(avg_size);
      break;
    }
  }
  Serial.println("Calibration Complete");
      tone(buzz, 450);
      delay(200);
      noTone(buzz);
}

void loop() {
  // averaging reading
  long reading = 0;
  for (int jj=0;jj<int(avg_size);jj++){
    reading+=hx711.read();
  }
  reading/=long(avg_size);
  // calculating mass based on calibration and linear fit
  float ratio_1 = (float) (reading-x0);
  float ratio_2 = (float) (x1-x0);
  float ratio = ratio_1/ratio_2;
  float mass = y1*ratio;
  //Serial.print("Raw: ");
  //Serial.print(reading);
  if (rfid.isCard()) {
    if (rfid.readCardSerial()) {
      rfidCard = String(rfid.serNum[0])+ String(rfid.serNum[1]) + String(rfid.serNum[2]) + String(rfid.serNum[3]);
      tone(buzz, 1000);
      delay(50);
      noTone(buzz);
      if (red != rfidCard){
        Serial.println(rfidCard); 
        red = rfidCard;
        }
    }
    rfid.halt();
  }
  else{
    red = "not";
    rfidCard = red;
    }
  if(mass < oldweight){
    Serial.print(", ");
  Serial.println(mass);
    }
  else if (mass > comp){
      Serial.print(", ");
  Serial.println(mass);
    }

  StaticJsonBuffer<1000> jsonBuffer;
  JsonObject& data = jsonBuffer.createObject();

  //Obtain Temp and Hum data


  //Assign collected data to JSON Object
  data["mass"] = mass;
  data["rfidCard"] = rfidCard; 

  //Send data to NodeMCU
  data.printTo(nodemcu);
  jsonBuffer.clear();

      hum = mass;
      output();
  delay(2000);
    comp = mass + 15;
    oldweight = mass -15;

}

void output() {

  Serial.print("waight");
  Serial.println(hum);
  Serial.print("RF tag");
  Serial.println(rfidCard);

}
