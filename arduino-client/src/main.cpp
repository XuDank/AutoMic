#include "Hardware.h"
#include "Communication.h"

const int BOARD_NUM = 4;

void setupUdp();
void PIDresponse();
void read(String );

void setup()
{
  Serial.begin(9600);
  Serial.println("Setup...");

  setupEthernet(BOARD_NUM);
  setupMotor();
  setupEncoder(readEncoder);

  setupUdp();

  Serial.println("Setup complete!");
  prev = millis();
}

void loop()
{
  String com = "";

  if (Udp.parsePacket())
  {
     com = in(); // recieve a comand from the server
     read(com);
  }

  if(millis()- prev > 50 && state == false)
  {
    state = true;
    out(String(count));
    out("True");
  }

  //Serial.println(String(count) + ", " + String(pwm) + ", " + String(tar));
  setPWM();
}

void setupUdp()
{
  Serial.println("Waiting for a UDP packet...");

  while(!Udp.parsePacket());
  out("True");
  
  Serial.println("Connected to: " + String(Udp.remoteIP()));
}

void PidResponse()
{
  String com = "";

  while(!Udp.parsePacket());
  
  com = in();
  tar = com.toDouble();

  int startTime = millis();
  int startCount = count;
  
  do
  {
    Serial.println(String(millis()-startTime)+ "," +String(count-startCount)+ "," +String(pwm));
    setPWM();
  }while(millis() - startTime < 10 * 1000 && millis() - prev < 1000);

  out("False");
}

void read(String com)
{
  if (isDigit(com[0]) || com[0] == '-')
  {
    tar = com.toDouble();
    prev = millis();
  }

  else if (com == "setup")
  {
    out("True");
  }

  else if (com == "sync")
  {
    out(String(count));
    
    if (abs(tar-count) < 150)
    {
      out("True");
    }
  }

  else if (com == "P")
  {
    out(String(count));
    if(abs(count - tar) < 150)
    {
      out("True");
    }
  }

  else if (com == "S")
  {
    pwm = 0;
    tar = count;
    out("True");
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

  else if (com == "PidResponse")
  {
    PidResponse();
  }

  else
  {
    Serial.println("Invalid command!");
  }
}
