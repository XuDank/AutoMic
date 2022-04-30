""""test"""
from matplotlib import pyplot as pl
from automic import *
from genuino import *

import pandas as pd

def double_pid(motor, arduino):
    times = list()
    counts = list()
    speeds = list()

def speed(motor, arduino):
    throttle = list()
    speed = list()

    try:
        for num in range(0, 101, 5):
            motor.send(f"S{num/100}")

            for _ in range(3):
                throttle.append(num)

                motor.set_length(0.0)
                motor.send_length(50)

                timer = []
                counter = []
                pwm = []

                while True:
                    try:
                        csv_line = arduino.readline().decode().strip().split(",")
                        
                        if csv_line == [""]:
                            break

                        timer.append(float(csv_line[0]))
                        counter.append(float(csv_line[1]) / motor.pulses_per_cm)
                        pwm.append(float(csv_line[2]))

                    except:
                        pass

                if motor.status == "Stopped":
                    motor.send("Ready")

                data = {"time": timer, "count": counter, "pwm": pwm}
                data_frame = pd.DataFrame(data=data)
                data_frame.drop(data_frame[data_frame["pwm"] != data_frame["pwm"].max()].index, inplace=True)

                speed.append((data_frame["count"].max() - data_frame["count"].min())/(data_frame["time"].max() - data_frame["time"].min()) / motor.pulses_per_cm * 1000000)

    except:
        if len(throttle) > len(speed):
            throttle.pop()

    data = {"throttle": throttle, "speed": speed}
    data_frame = pd.DataFrame(data=data)

    pl.figure()

    pl.plot(data_frame["throttle"], data_frame["speed"],
            "r.", label="Measured")

    pl.xlabel("Throttle (in %)")
    pl.ylabel("Speed (in cm/min)")

    pl.title("Speed vs throttle")
    pl.show()
    #pl.savefig(f"speed/speed plot")


def pid_tunner(motor, arduino):
    motor.set_length(0.0)

    while True:
        menu = {0: "Exit",
                1: "Go"}

        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Go":
            motor.PID = [float(parameter)
                         for parameter in input("Enter coordinates: ").split()]

            motor.set_length(0)
            motor.send_parameters()

            motor.send_length(5)

            timer = []
            counter = []
            pwm = []

            while motor.status != "Ready":
                try:
                    csv_line = tuple(
                        arduino.readline().decode().strip().split(","))
                    timer.append(float(csv_line[0]))
                    counter.append(float(csv_line[1]) / motor.pulses_per_cm)
                    pwm.append(float(csv_line[2]))

                except Exception as e:
                    print(e)
                    pass

            motor.send_length(0)

            data = {"time": timer, "length": counter, "pwm": pwm}
            data_frame = pd.DataFrame(data=data)
            data_frame["speed"] = data_frame.diff()["length"] / \
                data_frame.diff().time
            pl.plot(data_frame.time, data_frame["length"],
                    "b-", label="Measured")
            pl.plot([0, data_frame.time.max()],
                    [5, 5], "r--", label="Actual")
            pl.xlabel("Time (in ms)")
            pl.ylabel("Length (in cm)")
            pl.title(
                f"P = {motor.PID[0]}, I = {motor.PID[1]}, D = {motor.PID[2]}")
            pl.savefig(
                f"pid/P{motor.PID[0]}I{motor.PID[1]}D{motor.PID[2]}".replace(".", ""))
            pl.show()


def calibrate(motor):
    motor.set_length(0.0)

    while True:
        menu = {0: "Exit",
                1: "Go"}

        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Go":
            initial_measurement = float(input("Initial measurement (in cm): "))
            initial_length = motor.length

            motor.send_length(10)

            while not motor.status:
                pass

            final_length = motor.length
            final_measurement = float(input("Final measurement (in cm): "))

            measured_length = (final_length - initial_length)
            actual_length = (final_measurement - initial_measurement)

            fudge_factor = (actual_length - measured_length) / actual_length

            print(f"Fudge factor: {fudge_factor}")

            motor.send_length(0)
            motor.pulses_per_cm *= fudge_factor


def accuracy_test(motor):
    number_of_trials = int(input("Enter the number of trials: "))
    desired_length = int(input("Enter the desired length: "))

    measured_length = []
    actual_length = []

    motor.set_length(0.0)

    for _ in range(number_of_trials):
        initial_length = motor.length
        initial_measurement = float(input("Initial measurement (in cm): "))

        motor.send_length(desired_length)

        while not motor.status:
            pass

        final_measurement = float(input("Final measurement (in cm): "))

        measured_length.append(abs(motor.length - initial_length))
        actual_length.append(abs(final_measurement - initial_measurement))

        motor.send_length(0.0)

        while not motor.status:
            pass

    data = {"Measured Length (in cm)": measured_length,
            "Actual Length (in cm)": actual_length}
    data_frame = pd.DataFrame(data)
    data_frame["Measured Error (in cm)"] = data_frame["Actual Length (in cm)"] - \
        data_frame["Measured Length (in cm)"]
    data_frame.to_csv(f"accuracy/{int(desired_length)}.csv")

    data_frame["Measured Error (in cm)"].hist()

    pl.title(
        f"Desired length: {desired_length} cm\n(N = {number_of_trials}, $\mu$ = {np.mean(data_frame['Measured Error (in cm)']):.3f} cm, $\sigma$ = {np.std(data_frame['Measured Error (in cm)']):.3f} cm)")
    pl.xlabel("Measured Error (in cm)")
    pl.savefig(f"accuracy/{int(desired_length)}cm")


def reliability_test(motor):
    number_of_trials = int(input("Enter the number of trials: "))
    desired_length = int(input("Enter the desired length: "))

    measured_error = []

    motor.set_length(0.0)

    for _ in range(number_of_trials):
        motor.send_length(desired_length)

        while not motor.status:
            pass

        measured_error.append(desired_length - motor.length)

        motor.send_length(0.0)

        while not motor.status:
            pass

    data = {"Measured Error (in cm)": measured_error}
    data_frame = pd.DataFrame(data)
    data_frame.to_csv(f"reliability/{int(desired_length)}.csv")

    data_frame.hist()

    pl.title(
        f"Desired length: {desired_length} cm\n(N = {number_of_trials}, $\mu$ = {np.mean(measured_error):.3f} cm, $\sigma$ = {np.std(measured_error):.3f} cm)")
    pl.xlabel("Measured Error (in cm)")
    pl.savefig(f"reliability/{int(desired_length)}cm")


if __name__ == "__main__":
    

    menu = {0: "Exit",
            1: "Move",
            2: "PID Tunner",
            3: "Calibrate",
            4: "Accuracy test",
            5: "Reliability test",
            6: "Speed test"}

    arduino = None
    #arduino = Serial(port="COM10", baudrate=9600, timeout=0.5)

    while True:
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Move":
            motor.send_length(
                motor.length + float(input("Enter the amount (in cm): ")))

        elif menu[selection] == "PID Tunner":
            pid_tunner(motor=motor, arduino=arduino)
            arduino.close()

        elif menu[selection] == "Calibrate":
            calibrate(motor=motor)

        elif menu[selection] == "Accuracy test":
            accuracy_test(motor=motor)

        elif menu[selection] == "Reliability test":
            reliability_test(motor=motor)

        elif menu[selection] == "Speed test":
            speed(motor=motor, arduino=arduino)
            arduino.close()
