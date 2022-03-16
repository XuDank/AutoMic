#ifndef Communication
#define Communication

#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>

EthernetServer server = EthernetServer(5000);
EthernetClient client;

void setupEthernet(int board)
{
  byte MAC[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, (byte)board}; // MAC address
  IPAddress IP(192, 168, 1, board);                         // IP adress

  Ethernet.begin(MAC, IP);

  while (!Ethernet.hardwareStatus()){
    Serial.println("Ethenet not ready");
    delay(1000);
  }
  while (Ethernet.linkStatus() == LinkOFF){
    Serial.println("Link not up");
    delay(1000);
  }

  server.begin();

  Serial.println("Waiting for connection");

  while(!(client = server.available())){
    Serial.println("Waiting for client connect..");
    delay(1000);
  }
  Serial.println("Got a connection");
}

String in()
{
  String msg;
  msg = client.readStringUntil('\n');
  Serial.println("Recieved: " + msg);

  return msg;
}

void out(String msg, int port = 5000)
{
  client.println(msg);
  Serial.println("Sent: " + msg);
}

#endif