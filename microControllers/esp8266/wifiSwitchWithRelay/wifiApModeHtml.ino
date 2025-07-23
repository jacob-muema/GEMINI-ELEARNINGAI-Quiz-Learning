#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>

/* Put your SSID & Password */
const char* ssid = "NodeMCU";
const char* password = "123456789";

// Set the html file location
const char* htmlFile = "/index.html";

ESP8266WebServer server(80);

bool LED1Status = LOW;
bool LED2Status = LOW;

void setup() {

  if (!LittleFS.begin()) {
    Serial.println("An error has occurred while mounting LittleFS");
    return;
  }
  else{
    Serial.println("LittleFS mounted successfully");
  }

  Serial.begin(9600);
  pinMode(D2, OUTPUT); 
  pinMode(D4, OUTPUT); 
  WiFi.softAP(ssid, password);

  IPAddress myIP = WiFi.softAPIP();
  Serial.print("Access Point IP:");
  Serial.println(myIP);
  
  server.on("/", handle_OnConnect);
  server.on("/stat", handleStat);
  server.onNotFound(handle_NotFound);

  server.begin();
  //Serial.println("HTTP Server Started");
}

void loop() {
  server.handleClient();

  if(LED1Status)
  {digitalWrite(D2, HIGH);}
  else
  {digitalWrite(D2, LOW);}

  if(LED2Status)
  {digitalWrite(D4, HIGH);}
  else
  {digitalWrite(D4, LOW);}
}

void handle_OnConnect() {
  String fileContent = readFile(htmlFile);
  if (fileContent) {
    server.send(200, "text/html", fileContent);
  }
  else{
    server.send(404, "text/plain", "Not found");
  }
}

void handleStat() {
  // Check if a specific argument is present in the GET request
  String sendJson = "";
  String led1Txt = "";
  String led2Txt = "";

  if (server.hasArg("led1on")) {
    LED1Status = HIGH; // Later use server.arg("led1on") to get the value
  }
  if (server.hasArg("led1off")) {
    LED1Status = LOW;
  }
  if (server.hasArg("led2on")) {
    LED2Status = HIGH;
  }
  if (server.hasArg("led2off")) {
    LED2Status = LOW;
  }

  if(LED1Status){
    led1Txt = "on";
  }
  else{
    led1Txt = "off";
  }
  if(LED2Status){
    led2Txt = "on";
  }
  else{
    led2Txt = "off";
  }

  sendJson = "{\"led1\": \"";
  sendJson += led1Txt;
  sendJson += "\", \"led2\": \"";
  sendJson += led2Txt;
  sendJson += "\"}";
  server.send(200, "text/json", sendJson);
}

void handle_NotFound(){
  server.send(404, "text/plain", "Not found");
}

String readFile(const char* path) {
  File file = LittleFS.open(path, "r");
  if (!file) {
    Serial.println("Failed to open file for reading");
    return "";
  }

  String content = "";
  while (file.available()) {
    content += char(file.read());
  }
  file.close();
  return content;
}
