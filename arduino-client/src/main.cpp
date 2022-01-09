#include <Hardware.h>
#include <Communication.h>

#define BOARD_NUM 2

void setup()
{
  Serial.begin(9600);

  ethernet(BOARD_NUM);
  motor();
  encoder(interrupt);

  Serial.println("Done with setup");
}

void loop()
{
  if (Udp.parsePacket())
  {
    String com = in(); // recieve a comand from the server

    if (isDigit(com[0]))
    {
      tar = com.toInt();
      Serial.println("Target: " + String(tar));
    }

    else
    {
      switch (com[0])
      {
      case 'P':
        out(String(count));
        break;

      case 'E':
        com.remove(0);
        count = com.toInt();
        tar = count;
        out(String(count));
        break;

      case 'S':
        tar = count;
        out(String(count));
        break;

      case 'D':
        if (com[1] == 'E')
        {
          edir = edir * -1;
          out(String(edir));
          break;
        }

        else if (com[1] == 'M')
        {
          mdir = mdir * -1;
          out(String(mdir));
          break;
        }

      default:
        Serial.println("Invalid command!");
        break;
      }
    }
  }

  setPWM();

  delay(5);
}