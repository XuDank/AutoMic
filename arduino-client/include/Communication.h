#ifndef Communication
#define Communication

#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

EthernetUDP Udp;

void ethernet(int board)
{
    byte MAC[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, (byte)board}; // MAC address
    IPAddress IP(192, 168, 1, board);                     // IP adress

    Ethernet.begin(MAC, IP);

    while (1)
    {
        if (!Ethernet.hardwareStatus())
        {
            Serial.println("Ethernet shield was not found.");
        }
        else if (Ethernet.linkStatus() == LinkOFF)
        {
            Serial.println("Ethernet cable is not connected.");
            continue;
        }
        break;

        delay(1000);
    }

    Udp.begin(5000);

    Serial.println(IP);

    Serial.println("Done with ethernet setup.");
}

String in()
{
  char buff[UDP_TX_PACKET_MAX_SIZE] = {};
  Udp.read(buff, UDP_TX_PACKET_MAX_SIZE);

  Serial.println("Recieved: " + String(buff));
  return String(buff);
}

void out(String msg)
{
  char buff[UDP_TX_PACKET_MAX_SIZE];

  msg.toCharArray(buff, UDP_TX_PACKET_MAX_SIZE);

  Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
  Udp.write(buff);
  Udp.endPacket();

  Serial.println("Sent: " + String(buff));
}

#endif