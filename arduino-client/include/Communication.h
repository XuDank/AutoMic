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

  while (!Ethernet.hardwareStatus())
    ;
  while (Ethernet.linkStatus() == LinkOFF)
    ;

  server.begin();

  Serial.println("Waiting for connection");
  while (!server.available())
    ;

  client = server.available();
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