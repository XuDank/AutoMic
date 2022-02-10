#include <Hardware.h>
#include <Communication.h>

const int BOARD_NUM = 2;

void sync();

void setup()
{
  Serial.println("Setup...");

  Serial.begin(9600);

  ethernet(BOARD_NUM);
  motor();
  encoder(interrupt);
  sync();

  Serial.println("Done!");
}

void loop()
{
  if (Udp.parsePacket())
  {
    String com = in(); // recieve a comand from the server

    if (isDigit(com[0]) || com[0] == '-')
    {
      tar = com.toDouble();
      setPWM();
    }

    else if (com = "sync")
    {
      sync();
    }
    
    else if (com == "P")
    {
      out(String(count));
    }

    else if (com == "S")
    {
      tar = count;
      out(String(count));
    }

    else if (com[0] == 'E')
    {
      count = com.substring(1).toDouble();
      tar = count;
      out(String(count));
    }

    else if (com[0] == 'k')
    {
      if (com[1] == 'P')
      {
        kP = com.substring(2).toDouble();
      }

      else if (com[1] == 'P')
      {
        kI = com.substring(2).toDouble();
      }

      else if (com[1] == 'P')
      {
        kD = com.substring(2).toDouble();
      }

      myPID.SetTunings(kP, kI, kD);

      Serial.println("kP = " + String(kP) + ", kI = " + String(kI) + " & kD = " + String(kD));
    }
    
    else if (com.substring(0,1) == "DE")
    {
      edir = com.substring(2).toDouble();
      out(String(edir));
    }

    else if (com.substring(0,1) == "DM")
    {
      mdir = com.substring(2).toDouble();
      out(String(mdir));
    }

    else
    {
      Serial.println("Invalid command!");
    }
  }

  setPWM();
}

void sync()
{
  while(true) 
  {
    out("sync");

    if (Udp.parsePacket())
    {
      String com = in();

      if (com == "sync")
      {
        break;
      }
    }

    delay(500);
  }

  count = in().toDouble(); while (!Udp.parsePacket());
  tar = count; 

  mdir = in().toDouble(); while (!Udp.parsePacket());
  edir = in().toDouble(); while (!Udp.parsePacket());

  kP = in().toDouble(); while (!Udp.parsePacket());
  kI = in().toDouble(); while (!Udp.parsePacket());
  kD = in().toDouble(); while (!Udp.parsePacket());
  
}