#ifndef Hardware
#define Hardware

#include <Arduino.h>

#include <PID_v1.h>

const int CHA = 2, CHB = 3;
const int IN1 = 5, IN2 = 6, PWM = 4;

const double MIN_PWM = 0.1 * 255;

double edir = 0, mdir = 0;
double count = 0, tar = 0.0, pwm = 0.0;
double kP = 0.0, kI = 0.0, kD = 0.0;

PID myPID(&count, &pwm, &tar, kP, kI, kD, DIRECT);

void motor()
{
    myPID.SetMode(AUTOMATIC);
    myPID.SetOutputLimits(-255.0, 255.0);
    myPID.SetSampleTime(50); // default is 100

    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
}

void setPWM()
{
    myPID.Compute();

    if (abs(pwm) < MIN_PWM)
    {
        pwm = 0;
    }

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

}

void interrupt()
{
    if (digitalRead(CHB) == HIGH)
    {
        count = count + edir;
    }
    else
    {
        count = count - edir;
    }
}

void encoder(void (*f)())
{
    pinMode(CHA, INPUT);
    pinMode(CHB, INPUT);
    attachInterrupt(digitalPinToInterrupt(CHA), f, RISING);
}

#endif