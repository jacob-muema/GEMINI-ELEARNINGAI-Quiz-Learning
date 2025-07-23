/*
  Person 1 Program
  Author: Somnath Das
  More at: https://daslearning.in/

  NodeMCU Pins                          SX1278 Pins
  GND                                       GND
  3.3V                                      VCC
  D8                                        NSS
  D7                                        MOSI
  D6                                        MISO
  D5                                        SCK
  D0                                        RST
  D2                                        DIO0
*/

#include <LoRa.h>
#include "LittleFS.h"
#include <ESP8266WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ESPAsyncTCP.h>

#define csPin 15
#define resetPin 16
#define irqPin 2

// Replace with your network credentials
const char* ssid = "NodeMCU1";
const char* password = "123456789";

// Source and destination addresses for LoRa
byte localAddress = 0xBB;  // address of this device
byte destination = 0xCC;   // destination to send to

// Create AsyncWebServer object on port 80
AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

// Global variables
String outMsg;
bool outMsgStatus = LOW;

void handleClientMsg(void *arg, uint8_t *data, size_t len) {
  AwsFrameInfo *info = (AwsFrameInfo*)arg;
  if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
    data[len] = 0;
    outMsg = (char*)data;
    outMsgStatus = HIGH;
  }
}

void sendMessage() {
  LoRa.beginPacket();                // start packet
  LoRa.write(destination);           // add destination address
  LoRa.write(localAddress);          // add sender address
  LoRa.print(outMsg);                // add payload
  LoRa.endPacket();                  // finish packet and send it
  Serial.println("You:" + outMsg);   // For Serial Chat
  outMsgStatus = LOW;                // Set it to low for next msg
  outMsg = "";                       // Make the msg blank
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

void initLoRa(){
  LoRa.setPins(csPin, resetPin, irqPin);
  // Start LoRa module at local frequency
  // 433E6 for Asia
  // 866E6 for Europe
  // 915E6 for North America
  if (!LoRa.begin(433E6)) {
    Serial.println("Starting LoRa failed!");
  }
  else{
    Serial.println("LoRa initialized successfully");
  }
}

void initFS(){
  if (!LittleFS.begin()) {
    Serial.println("An error has occurred while mounting LittleFS");
  }
  else{
    Serial.println("LittleFS mounted successfully");
  }
}

// Incoming msg from LoRa
void onReceive(int packetSize) {
  if (packetSize == 0) return;  // if there's no packet, return

  // Read packet header bytes:
  int recipient = LoRa.read();        // recipient address
  byte sender = LoRa.read();          // sender address

  String incoming = "";  // payload of packet
  while (LoRa.available()) {        // can't use readString() in callback, so
    incoming += (char)LoRa.read();  // add bytes one by one
  }

  // If the recipient isn't this device or broadcast,
  if (recipient != localAddress && recipient != destination) {
    Serial.println("This message is not for me.");
    return;  // skip rest of function
  }

  // If message is for this device, or broadcast, print details:
  ws.textAll(incoming);
  Serial.println("From 0x" + String(sender, HEX) + ": " + incoming);
  Serial.println();
}

void setup(){
  // Serial port for debugging purposes
  Serial.begin(115200);

  // Wi-Fi
  initWiFi();

  // Socket
  initWebSocket();

  //LoRa
  initLoRa();

  //FS
  initFS();

  // Route for root / web page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(LittleFS, "/index.html", "text/html");
  });
  server.serveStatic("/", LittleFS, "/");

  // Start server
  server.begin();
}

void loop() {
  if(outMsgStatus){
    // Send msg via LoRa
    sendMessage();
    delay(300);
  }
  if(Serial.available()) {
    outMsg = Serial.readStringUntil('\n'); // Read until newline
    outMsg.trim();
    outMsgStatus = HIGH;
  }
  ws.cleanupClients();
  onReceive(LoRa.parsePacket());
}
