#include "Hardware.h"
#include "Communication.h"

const int BOARD_NUM = 2;

void setupUdp();
void read(String );

void setup()
{
  Serial.begin(9600);

  setupEthernet(BOARD_NUM);
  setupMotor();
  setupEncoder(readEncoder);

  out("Setup");

  prev = millis();
}

void loop()
{
  if(!client.connected())
  {
    client.stop();
    setupEthernet(BOARD_NUM);
  }

  if (client.available())
  {
    read(in());
  }

  if (!state && prev - millis() > 10)
  {
    if (abs(tar-count) > 11)
    {
      out("Emergency Stop");
      tar = count + 1000;
      setPWM();
    }

    else
    {
      out("Ready");
      state = true;
    }
  }

  Serial.println(String(millis()) + "," + String(count) + "," + String(pwm));
  setPWM();
}

void read(String com)
{
  if (isDigit(com[0]) || com[0] == '-')
  {
    prev = millis();
    tar = com.toDouble();
    state = false;
    prev = millis();
  }

  else if (com == "Sync")
  {
    out(String(count));

    if(state) out("Ready");
    else out("Busy");
  }

  else if (com == "P")
  {
    out(String(count));
  }

  else if (com == "Stop")
  {
    tar = count;
    setPWM();
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
  }


  else if (com.substring(0, 2) == "DE")
  {
    edir = com.substring(2).toDouble();
  }

  else if (com.substring(0, 2) == "DM")
  {
    mdir = com.substring(2).toDouble();
  }

  else
  {
  }
}