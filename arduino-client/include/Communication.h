#ifndef Communication
#define Communication

#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

#define PORT 5000

EthernetUDP Udp;

void ethernet(int board)
{
    byte MAC[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, (byte)board}; // MAC address
    IPAddress IP(192, 168, 1, board + 1);                     // IP adress

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
    }

    Udp.begin(PORT);

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
  char buff[16];

  msg.toCharArray(buff, 16);

  Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
  Udp.write(buff);
  Udp.endPacket();

  Serial.println("Sent: " + String(buff));
}

#endif