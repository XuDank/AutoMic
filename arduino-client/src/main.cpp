#include "Hardware.h"
#include "Communication.h"

const int BOARD_NUM = 2;

void setupUdp();
void read(String);

void setup()
{
  Serial.begin(9600);

  setupEthernet(BOARD_NUM);
  setupMotor();
  setupEncoder(readEncoder);

  state = "Ready";
  out(state);

  prev = millis();
}

void loop()
{
  if (!client.connected())
  {
    Serial.println("Disconnected");

    client.stop();

    pwm = 0;
    setPWM();

    delay(10);

    count = tar;

    setupEthernet(BOARD_NUM);
  }

  if (client.available())
  {
    // Serial.println("Availible");
    read(in());
  }

  if (state == "Moving" && millis() - prev > 150)
  {
    out(String(count));
    if (abs(tar - count) > 150)
    {
      state = "Stopped";
      pwm = -pwm;
      setPWM();

      delay(500);

      pwm = 0;
      setPWM();

      delay(100);

      count = tar;
    }

    else
    {
      state = "Ready";
      tar = count;
    }

    out(state);
  }

  else if (state == "Moving")
  {
    // Serial.println(String(millis()) + "," + String(count) + "," + String(pwm));
  }

  myPID.Compute();
  setPWM();
}

void read(String com)
{
  if (isDigit(com[0]) || com[0] == '-')
  {
    if (state == "Ready")
    {
      tar = com.toDouble();
      state = "Moving";
      prev = millis();
    }

    else
    {
      out(state);
    }
  }

  else if (com == "Sync")
  {
    out(String(count));
    out(state);
  }

  else if (com == "Ready")
  {
    state = com;
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

  else if (com[0] == 'S')
  {
    double speed = com.substring(1).toDouble() * 255.0;
    myPID.SetOutputLimits(-speed, speed);
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