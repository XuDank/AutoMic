from matplotlib import pyplot as pl
from automic import *
import pandas as pd
from serial import Serial
import logging

def pid_tunner(motor, arduino):

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
            motor.PID =  [float(parameter) for parameter in input("Enter coordinates: ").split()]
            motor.set_length(0)
            motor.send_parameters()

            motor.write("PidResponse")

            motor.send_length(5)

            timer = []
            counter = []
            pwm = []

            while not motor.status:
                try:
                    csv_line = tuple(arduino.readline().decode().strip().split(","))
                    timer.append(float(csv_line[0]))
                    counter.append(float(csv_line[1]) / motor.pulses_per_cm)
                    pwm.append(float(csv_line[2]))
                except Exception as e:
                    print(e)
                    pass

            motor.send_length(0)

            data = {"time": timer, "length": counter, "pwm": pwm}
            data_frame = pd.DataFrame(data=data)
            data_frame["speed"] = data_frame.diff()["length"] / data_frame.diff()["time"]
            pl.plot(data_frame["time"], data_frame["length"], "b-", label = "Measured")
            pl.plot([0, data_frame["time"].max()], [5, 5], "r--", label = "Actual")
            pl.xlabel("Time (in ms)")
            pl.ylabel("Length (in cm)")
            pl.title(f"P = {motor.PID[0]}, I = {motor.PID[1]}, D = {motor.PID[2]}")
            pl.savefig(f"pid/P{motor.PID[0]}I{motor.PID[1]}D{motor.PID[2]}".replace(".", ""))
            pl.show()

def calibrate(motor):
    while motor.length:
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
            actual_length = (final_measurement- initial_measurement)

            fudge_factor = (actual_length - measured_length) / actual_length

            print(f"Fudge factor: {fudge_factor}")

            motor.send_length(0)
            motor.pulses_per_cm *= fudge_factor

def accuracy_test(motor):
    number_of_trials = int(input("Enter the number of trials: "))
    desired_length = int(input("Enter the desired length: "))

    measured_length = []
    actual_length = []

    while motor.length:
        motor.set_length(0.0)

    for _ in range(number_of_trials):
        initial_length = motor.length
        initial_measurement = float(input("Initial measurement (in cm): "))

        motor.send_length(desired_length)

        while not motor.status:
            pass

        final_measurement = float(input("Final measurement (in cm): ")) 

        measured_length.append(abs(motor.length - initial_length))
        actual_length.append(abs(final_measurement- initial_measurement))

        motor.send_length(0.0)

        while not motor.status:
            pass

    data = {"Measured Length (in cm)": measured_length, "Actual Length (in cm)": actual_length}
    data_frame = pd.DataFrame(data)
    data_frame["Measured Error (in cm)"] = data_frame["Actual Length (in cm)"] - data_frame["Measured Length (in cm)"]
    data_frame.to_csv(f"accuracy/{int(desired_length)}.csv")

    data_frame["Measured Error (in cm)"].hist()

    pl.title(f"Desired length: {desired_length} cm\n(N = {number_of_trials}, $\mu$ = {np.mean(data_frame['Measured Error (in cm)']):.3f} cm, $\sigma$ = {np.std(data_frame['Measured Error (in cm)']):.3f} cm)")
    pl.xlabel("Measured Error (in cm)")
    pl.savefig(f"accuracy/{int(desired_length)}cm")

def reliability_test(motor):
    number_of_trials = int(input("Enter the number of trials: "))
    desired_length = int(input("Enter the desired length: "))

    measured_error = []

    while motor.length:
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

    pl.title(f"Desired length: {desired_length} cm\n(N = {number_of_trials}, $\mu$ = {np.mean(measured_error):.3f} cm, $\sigma$ = {np.std(measured_error):.3f} cm)")
    pl.xlabel("Measured Error (in cm)")
    pl.savefig(f"reliability/{int(desired_length)}cm")

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('logfile.log')
    formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)

    # add file handler to logger
    logger.addHandler(file_handler)


    motors = [Motor(id = 1, ip_address= "192.168.1.4", encoder_direction=-1, motor_direction=-1, kP = 5, kI = 0.1, kD = .01, logger = logger), Motor(id = 2, ip_address= "192.168.1.3", encoder_direction=-1, motor_direction=-1, kP = 5, kI = 0.1, kD = .01, logger = logger)]
    
    mic = Mic(motors=motors)
    stage = Stage(mics = [mic])
    motor = motors[0]
    stage.setup()

    menu = {0: "Exit",
            1: "Move",
            2: "PID Tunner",
            3: "Calibrate",
            4: "Accuracy test",
            5: "Reliability test"}

    while True:
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Move":
            motor.send_length(motor.length + float(input("Enter the amount (in cm): ")))

        elif menu[selection] == "PID Tunner":
            arduino = Serial(port = "COM10", baudrate = 9600)
            pid_tunner(motor=motor, arduino=arduino)
            arduino.close()
        
        elif menu[selection] == "Calibrate":
            calibrate(motor=motor)

        elif menu[selection] == "Accuracy test":
            accuracy_test(motor=motor)

        elif menu[selection] == "Reliability test":
            reliability_test(motor=motor)