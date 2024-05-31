//ThatsEngineering
//Sending Data from Arduino to NodeMCU Via Serial Communication
//NodeMCU code

//Include Lib for Arduino to Nodemcu
#include <SoftwareSerial.h>
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
String weighto = "0";

#define LED D1
const char* ssid     = "MAD_DRILLS_2.4GHz";
const char* password = "9449050762";

const char* host = "maddrills-code50-54169128-7q7qxg59crprq-5000.githubpreview.dev"; // only google.com not https://google.com

String rfold = " ";

//D6 = Rx & D5 = Tx
SoftwareSerial nodemcu(D6, D5);


void setup() {
  // Initialize Serial port
  Serial.begin(115200);
  nodemcu.begin(115200);
  
  pinMode(LED, OUTPUT);//FOR LED SUC
  pinMode(D2, OUTPUT);//ERROR
  pinMode(D3, OUTPUT);//START UP
  digitalWrite(D3,HIGH);
  
  delay(10);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  while (!Serial) continue;
   Serial.println("setup done");
  digitalWrite(D3,LOW);
}

void loop() {
  
  StaticJsonBuffer<1000> jsonBuffer;
  JsonObject& data = jsonBuffer.parseObject(nodemcu);

  if (data == JsonObject::invalid()) {
    //Serial.println("Invalid Json Object");
    jsonBuffer.clear();
    return;
  }

  Serial.println("JSON Object Recieved");
  Serial.print("Recieved weight:  ");
  String weight = data["mass"];
  Serial.println(weight);
  Serial.print("Recieved rf:  ");
  String rf = data["rfidCard"];
  Serial.println(rf);
  Serial.println("-----------------------------------------");

  delay(1000);

  Serial.print("connecting to ");
  Serial.println(host);

  // Use WiFiClient class to create TCP connections
  WiFiClientSecure client;
  const int httpPort = 443; // 80 is for HTTP / 443 is for HTTPS!
  
  client.setInsecure(); // this is the magical line that makes everything work
  
  if (!client.connect(host, httpPort)) { //works!
    Serial.println("connection failed");
    digitalWrite(D2,HIGH);
    delay(1000);
    digitalWrite(D2,LOW);
    return;
  }

  // We now create a URI for the request
  String url = "/repository";
  url += "?weight=";
  url += weight;
  url += "&";
  url += "rfid=";
  url += rf;
  url += "&";
  url += "code=";
  url += "9800";
  url += "&";
  url += "rfold=";
  url += rfold;


  Serial.print("Requesting URL: ");
  Serial.println(url);

  // This will send the request to the server
  client.print(String("POST ") + url + " HTTP/1.1\r\n" +
               "Host: " + host + "\r\n" + 
               "Connection: close\r\n\r\n");      

  Serial.println();
  Serial.println("closing connection");

  digitalWrite(LED,HIGH);
  delay(50);
  digitalWrite(LED,LOW);
  
  rfold = rf;
  weighto = weight;
  Serial.println(weighto);
  Serial.println(weight);
}
