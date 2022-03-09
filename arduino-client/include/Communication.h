#ifndef Communication
#define Communication

#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

EthernetServer server = EthernetServer(5000);
EthernetClient client;

void setupEthernet(int board)
{
    byte MAC[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, (byte)board}; // MAC address
    IPAddress IP(192, 168, 1, board);                     // IP adress

    Ethernet.begin(MAC, IP);

    while (!Ethernet.hardwareStatus());
    while (Ethernet.linkStatus() == LinkOFF);

    server.begin();

    while(!server.available());

    client = server.available();
}

String in()
{
  String msg;
  msg = client.readString();

  return msg;
}

void out(String msg, int port = 5000)
{
  server.print(msg);
}

#endif