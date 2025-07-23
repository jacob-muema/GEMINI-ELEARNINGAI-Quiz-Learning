/* 
  Controls a toy car using ESP8266
  Developer: Somnath Das
  Contact: daslearning.in
*/

#include <ESP8266WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ESPAsyncTCP.h>
#include "LittleFS.h"

// Define Motor PINs
#define fwdPin 13   //D7 connects to the forward pin of rear DC motor via motor driver
#define bckPin 15   //D8 connects to the backward pin of rear DC motor via motor driver
#define leftPin 14  //D5 connects to the left pin of front DC motor via motor driver
#define rightPin 12 //D6 connects to the right pin of front DC motor via motor driver

// Define LED PINs
#define fLight 5  //D1 connects to head lamp LEDs (use proper resistor)
#define bLight 4  //D2 connects to rear brake RED LEDs (use proper resistor)
#define leftInd 0 //D3 connects to left indicator LEDs (use proper resistor)
#define rigtInd 2 //D4 connects to right indicator LEDs (use proper resistor

// Replace with your network credentials
const char* ssid = "CarMCU";
const char* password = "123456789";
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// Define variables
int carSpeed = 130;
int turnPwm = 180;
bool fwdFlag = true; // Goes back for false
bool dirChng = false;
bool moveFlag = false;
bool lftTurn = false;
bool rgtTurn = false;

String ctlMsg; // Inputs from User

unsigned long oldLeftMillis = 0;
unsigned long oldRghtMillis = 0;
const int interval = 500; // Blink interval in milliseconds
bool lftInFlag = false;
bool rghtInFlag = false;
bool frntLiFlag = false;
bool backLiFlag = false;

bool frntLiChg = false;
bool backLiChg = false;
int beamIntensity = 120; // Low beam and high beam
bool indiChg = false;

void initWebSocket() {
  ws.onEvent(onEvent);
  server.addHandler(&ws);
}

void initWiFi(){
  WiFi.softAP(ssid, password);
  IPAddress myIP = WiFi.softAPIP();
  Serial.print("Access Point IP:");
  Serial.println(myIP);
}

void initFS(){
  if (!LittleFS.begin()) {
    Serial.println("An error has occurred while mounting LittleFS");
  }
  else{
    Serial.println("LittleFS mounted successfully");
  }
}

void carControl(String ctlMsg) {
  ctlMsg.trim();

  if(ctlMsg == "fwd"){
    fwdFlag = true;
    dirChng = true;
    backLiFlag = false;
    backLiChg = true;
    moveFlag =  true;
    turnPwm = 180;
    Serial.println("forward received");
  }
  else if(ctlMsg == "bck"){
    fwdFlag = false;
    dirChng = true;
    backLiFlag = true;
    backLiChg = true;
    moveFlag =  true;
    turnPwm = 180;
    Serial.println("backward received");
  }
  else if(ctlMsg == "left"){
    lftTurn = true;
    rgtTurn = false;
    Serial.println("left turn received");
  }
  else if(ctlMsg == "right"){
    rgtTurn = true;
    lftTurn = false;
    Serial.println("right turn received");
  }
  else if(ctlMsg == "speed1"){
    carSpeed = 130;
    dirChng = true;
    Serial.println("gear 1 received");
  }
  else if(ctlMsg == "speed2"){
    carSpeed = 150;
    dirChng = true;
    Serial.println("gear 2 received");
  }
  else if(ctlMsg == "speed3"){
    carSpeed = 170;
    dirChng = true;
    Serial.println("gear 3 received");
  }
  else if(ctlMsg == "speed4"){
    carSpeed = 200;
    dirChng = true;
    Serial.println("gear 4 received");
  }
  else if(ctlMsg == "stop"){
    analogWrite(bckPin, 0);
    analogWrite(fwdPin, 0);
    backLiFlag = true;
    backLiChg = true;
    moveFlag =  false;
    turnPwm = 200;
    Serial.println("stop received");
  }
  else if(ctlMsg == "hbeam"){
    frntLiFlag = true;
    frntLiChg = true;
    beamIntensity = 250;
    Serial.println("high beam received");
  }
  else if(ctlMsg == "lbeam"){
    frntLiFlag = true;
    frntLiChg = true;
    beamIntensity = 120;
    Serial.println("low beam received");
  }
  else if(ctlMsg == "floff"){
    frntLiFlag = false;
    frntLiChg = true;
    beamIntensity = 120;
    Serial.println("front light off received");
  }
  else if(ctlMsg == "lftind"){
    lftInFlag = true;
    rghtInFlag = false;
    indiChg = true;
    Serial.println("left indicator received");
  }
  else if(ctlMsg == "rgtind"){
    lftInFlag = false;
    rghtInFlag = true;
    indiChg = true;
    Serial.println("right indicator received");
  }
  else if(ctlMsg == "park"){
    lftInFlag = true;
    rghtInFlag = true;
    indiChg = true;
    Serial.println("park indicator received");
  }
  else if(ctlMsg == "indoff"){
    lftInFlag = false;
    rghtInFlag = false;
    indiChg = true;
    Serial.println("indicator off received");
  }
}

void handleClientMsg(void *arg, uint8_t *data, size_t len) {
  String inMsg;
  AwsFrameInfo *info = (AwsFrameInfo*)arg;
  if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
    data[len] = 0;
    inMsg = (char*)data;
    carControl(inMsg);
  }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type,
  void *arg, uint8_t *data, size_t len) {
  switch (type) {
    case WS_EVT_CONNECT:
      Serial.printf("WebSocket client #%u connected from %s\n", client->id(), client->remoteIP().toString().c_str());
      break;
    case WS_EVT_DISCONNECT:
      Serial.printf("WebSocket client #%u disconnected\n", client->id());
      break;
    case WS_EVT_DATA:
      handleClientMsg(arg, data, len);
      break;
    case WS_EVT_PONG:
    case WS_EVT_ERROR:
      break;
  }
}

// Set the board
void setup() {
  Serial.begin(115200);
  Serial.println("Initializing...");

  // Wi-Fi
  initWiFi();
  // Socket
  initWebSocket();

  //FS
  initFS();

  // Route for root / web page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/index.html", "text/html");
  });
  server.serveStatic("/", LittleFS, "/");
  // Start server
  server.begin();

  pinMode(fwdPin, OUTPUT);
  pinMode(bckPin, OUTPUT);
  pinMode(leftPin, OUTPUT);
  pinMode(rightPin, OUTPUT);

  pinMode(fLight, OUTPUT);
  pinMode(bLight, OUTPUT);
  pinMode(leftInd, OUTPUT);
  pinMode(rigtInd, OUTPUT);

  Serial.println("Setup Complete!");
}

void turnSlowDown() {
  if(moveFlag) {
    if(fwdFlag) {
      analogWrite(fwdPin, 140);
    }
    else {
      analogWrite(bckPin, 140);
    }
    dirChng = true;
    delay(100);
  }
}

//The loop or the main brain
void loop() {

  // Car Direction & Speed
  if(dirChng) {
    if(fwdFlag) {
      analogWrite(bckPin, 0); //Stop the other pin
      analogWrite(fwdPin, carSpeed);
    }
    else {
      analogWrite(fwdPin, 0); // Stop the other pin
      analogWrite(bckPin, carSpeed);
    }
    dirChng = false;
  }

  // Car Left & Right Turns
  if(lftTurn) {
    if(carSpeed > 140){
      turnSlowDown();
    }
    analogWrite(leftPin, turnPwm);
    delay(50);
    analogWrite(leftPin, 0);
    lftTurn = false;
  }
  if(rgtTurn) {
    if(carSpeed > 140){
      turnSlowDown();
    }
    analogWrite(rightPin, turnPwm);
    delay(50);
    analogWrite(rightPin, 0);
    rgtTurn = false;
  }

  // Front & Back LED
  if(frntLiChg) {
    if(frntLiFlag) {
      analogWrite(fLight, beamIntensity);
    }
    else {
      analogWrite(fLight, 0);
    }
  }
  if(backLiChg) {
    if(backLiFlag) {
      analogWrite(bLight, 100);
    }
    else {
      analogWrite(bLight, 0);
    }
  }

  // Control indicators
  if(indiChg) {
    if(lftInFlag) {
      unsigned long leftMillis = millis();
      if (leftMillis - oldLeftMillis >= interval) {
        digitalWrite(leftInd, !digitalRead(leftInd));
        oldLeftMillis = leftMillis;
      }
    }
    else {
      digitalWrite(leftInd, LOW);
    }

    if(rghtInFlag) {
      unsigned long rghtMillis = millis();
      if (rghtMillis - oldRghtMillis >= interval) {
        digitalWrite(rigtInd, !digitalRead(rigtInd));
        oldRghtMillis = rghtMillis;
      }
    }
    else {
      digitalWrite(rigtInd, LOW);
    }

    if(!rghtInFlag && !lftInFlag) {
      indiChg = false;
      Serial.println("Indicators turned off!");
    }
  }

  ws.cleanupClients();

}
