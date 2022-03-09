#ifndef Hardware
#define Hardware

#include <Arduino.h>

#include <PID_v1.h>

const int CHA = 2, CHB = 3;
const int IN1 = 5, IN2 = 6, PWM = 4;

const double MIN_PWM = 30;

double edir = 1, mdir = 1;
volatile double count = 0;
double tar = 0.0, pwm = 0.0;
double kP = 1.0, kI = 0.0, kD = 0.0;

volatile unsigned long prev; 
bool state = true;

PID myPID(&count, &pwm, &tar, kP, kI, kD, DIRECT);

void setupMotor()
{
    myPID.SetMode(AUTOMATIC);
    myPID.SetOutputLimits(-255.0, 255.0);
    myPID.SetSampleTime(1);

    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
}

void setPWM()
{
  myPID.Compute();
  
  if (pwm * mdir > 0)
  {
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      analogWrite(PWM, abs(pwm));
  }
  
  else
  {
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, HIGH);
      analogWrite(PWM, abs(pwm));
  }
  //Serial.println("Target: " + String(tar) + " Count: " + String(count) + " PWM: " + String(pwm));
}

void readEncoder()
{
  prev = millis();
  
    if (digitalRead(CHB) == HIGH)
    {
        count += edir;
    }
    else
    {
        count -= edir;
    }
}

void setupEncoder(void (*f)())
{
    pinMode(CHA, INPUT);
    pinMode(CHB, INPUT);
    attachInterrupt(digitalPinToInterrupt(CHA), f, RISING);
}

#endif