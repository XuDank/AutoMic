#ifndef Hardware
#define Hardware

#include <Arduino.h>

#include <PID_v1.h>

#define CHA 2
#define CHB 3
#define K 327.48538

#define IN1 5
#define IN2 6
#define PWM 4

int edir = 1, mdir = 1;

double count;

double tar = 0, pwm;

double kP = 10.0, kI = 1.0, kD = 0.0;

PID myPID(&count, &pwm, &tar, kP, kI, kD, DIRECT);

void motor()
{
    myPID.SetMode(AUTOMATIC);

    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
}

void setPWM()
{
    myPID.Compute();

    if (abs(pwm) < 30)
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
    count = 0;
}

#endif