#include <Hardware.h>
#include <Communication.h>

const int BOARD_NUM = 4;

void sync(bool = true);
void read(String );

void setup()
{
  Serial.begin(9600);
  Serial.println("Setup...");

  setupEthernet(BOARD_NUM);
  setupMotor();
  setupEncoder(readEncoder);

  sync();

  Serial.println("Setup complete!");
  Serial.println("Entering the loop");
}

void loop()
{
  if (Udp.parsePacket())
  {
    String com = in(); // recieve a comand from the server

    if (isDigit(com[0]) || com[0] == '-')
    {
      tar = com.toDouble();
    }

    else read(com);
  }

  setPWM();
}

void sync(bool wait)
{
  while (wait)
  {
    while (!Udp.parsePacket());

    String com = in();
    if (com == "sync") break;
  }

  while(true)
  {
    while (!Udp.parsePacket());

    String com = in();
    if (com == "done")
    {
      out("synced");
      break;
    } 

    read(com);
  }
}

void read(String com)
{
  Serial.println("Reading...");
  if (com == "sync") sync(false);

  else if (com == "P")
  {
    out(String(count));
  }

  else if (com == "S")
  {
    pwm = 0;
    tar = count;
  }

  else if (com[0] == 'E')
  {
    count = com.substring(1).toDouble();
    tar = count;
  }

  else if (com[0] == 'k')
  {
    if (com[1] == 'P')
    {
      kP = com.substring(2).toDouble();
    }

    else if (com[1] == 'I')
    {
      kI = com.substring(2).toDouble();
    }

    else if (com[1] == 'D')
    {
      kD = com.substring(2).toDouble();
    }

    myPID.SetTunings(kP, kI, kD);

    Serial.println("kP = " + String(kP) + ", kI = " + String(kI) + " & kD = " + String(kD));
  }


  else if (com.substring(0,2) == "DE")
  {
    edir = com.substring(2).toDouble();
  }

  else if (com.substring(0,2) == "DM")
  {
    mdir = com.substring(2).toDouble();
  }

  else
  {
    Serial.println("Invalid command!");
  }
}