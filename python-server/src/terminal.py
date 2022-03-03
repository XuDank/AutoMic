import logging
import sys 
sys.path.append('..')

import pickle as pk
from automic import *
from ipaddress import ip_address as adr

def position_input():
    while True:
        try:
            user_input = [float(coordinate) for coordinate in input(
                "Enter coordinates: ").split()]

            if len(user_input) == 1:
                return np.array([0, 0] + user_input)

            elif len(user_input) == 2:
                return np.array(user_input + [0])

            elif len(user_input) == 3:
                return np.array(user_input)

        except:
            print("Invalid input!")

# Motor

# Need a get motor method in the mic class

def operate_motor(motor): # May need a thread to keep track of the error # Implement a timeout for the thread
    print(motor)
    while True:
        menu = {0: "Exit",
                1: "Edit the spool diameter",
                2: "Adjust the spool diameter",
                3: "Edit the ID",
                4: "Edit the IP address",
                5: "Edit the position",
                6: "Edit the cable length",
                7: "Change the direction",
                8: "Edit the PID values",
                9: "Change the direction of the encoder",
                10: "Edit the encoder resolution",
                11: "Move",
                12: "Get the current cable length",
                13: "Send"}

        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Change the direction of the encoder":
            motor.toggle_encoder()

        elif menu[selection] == "Change the direction":
            motor.toggle_encoder()
            motor.toggle_motor()
        
        elif menu[selection] == "Send":
            motor.write(input("Enter the message: "))

        elif menu[selection] == "Edit the ID":
            print(f"Current ID: {motor.id}")
            motor.id = int(input("Enter the new ID: "))

        elif menu[selection] == "Edit the IP address":
            print(f"Current IP address: {motor.address}")
            motor.address = (
                str(adr(input("Enter the new IP address: "))), 5000)

        elif menu[selection] == "Edit the spool diameter":
            print(f"Current spool diameter: {motor.spool_diameter} cm")

            motor.spool_diameter = float(
                input("Enter the new spool diameter: "))
            motor.pulses_per_cm = motor.pulses_per_revolution / \
                (np.pi * motor.spool_diameter)

        elif menu[selection] == "Edit the encoder resolution":
            print(f"Current encoder resolution: {motor.pulses_per_revolution}")

            motor.pulses_per_revolution = float(
                input("Enter the new encoder resolution: "))
            motor.pulses_per_cm = motor.pulses_per_revolution / \
                (np.pi * motor.spool_diameter)

        elif menu[selection] == "Edit the position":
            print(f"Current position: {motor.position}")

            motor.position = position_input()

        elif menu[selection] == "Edit the PID values":
            print(f"Current values: {motor.PID}")

            motor.pid = position_input()

        elif menu[selection] == "Edit the cable length":
            print(f"Current cable length: {motor.length}")

            motor.length = float(input("Enter the new cable length: "))

            motor.set_length(motor.length)
            
        elif menu[selection] == "Move":
            length = motor.length + float(input("Enter the amount: "))
            motor.send_length(length)

        else:
            print("Not implemented in the code!")


def operate_mic(mic):
    print(mic)
    while True:
        menu = {0: "Exit",
                1: "Move",
                2: "Add a motor",
                3: "Remove a motor",
                4: "Edit the name",
                5: "Edit the position",
                6: "Select a motor"}

        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if menu[selection] == "Exit":
            break

        elif  menu[selection] == "Move":
            mic.move(position_input())

        elif menu[selection] == "Add a motor":
            mic.motors.append(Motor(server=mic.motors[0].server))

        elif menu[selection] == "Edit the name":
            mic.name = input("Enter the new name: ")

        elif menu[selection] == "Edit the position":
            mic.position = position_input()

        elif menu[selection] == "Select a motor":

            while True:
                menu = {0: "Exit"}
                menu.update({index: motor for index,
                            motor in enumerate(mic.motors, 1)})

                for key in sorted(menu.keys()):
                    print(f"{key}: {menu[key]}")

                while (selection := int(input("Make a selection: "))) not in menu.keys():
                    print("Invalid selection!")

                if menu[selection] == "Exit":
                    break

                motor = menu[selection]

                while True:
                    menu = {0: "Exit",
                            1: "Remove",
                            2: "Operate"}

                    for key in sorted(menu.keys()):
                        print(f"{key}: {menu[key]}")

                    while (selection := int(input("Make a selection: "))) not in menu.keys():
                        print("Invalid selection!")

                    if menu[selection] == "Exit":
                        break

                    elif menu[selection] == "Remove":
                        mic.motors.remove(motor)

                    elif menu[selection] == "Operate":
                        operate_motor(motor)

        else:
            print("Not implemented in the code!")

def operate_stage(stage):
    print(stage)
    menu = {0: "Exit",
            1: "Save preset",
            2: "Select preset",
            3: "Remove a motor",
            4: "Select a mic"}

    while True:
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if menu[selection] == "Exit":
            break

        elif  menu[selection] == "Save preset":
            stage.save_preset()

        elif menu[selection] == "Select preset":

            while True:
                menu = {0: "Exit"}
                menu.update({index: preset_name for index,
                            preset_name in enumerate(stage.presets.keys(), 1)})

                for key in sorted(menu.keys()):
                    print(f"{key}: {menu[key]}")

                while (selection := int(input("Make a selection: "))) not in menu.keys():
                    print("Invalid selection!")

                if menu[selection] == "Exit":
                    break

                preset = menu[selection]

                while True:

                    menu = {0: "Exit",
                            1: "Remove",
                            2: "Recall"}

                    for key in sorted(menu.keys()):
                        print(f"{key}: {menu[key]}")

                    while (selection := int(input("Make a selection: "))) not in menu.keys():
                        print("Invalid selection!")

                    if menu[selection] == "Exit":
                        break

                    elif menu[selection] == "Remove":
                        stage.presets.pop(preset, None)

                    elif menu[selection] == "Recall":
                        stage.recall_preset(preset)

        elif menu[selection] == "Select a mic":
            while True:
                menu = {0: "Exit"}
                menu.update({index: mic for index, mic in enumerate(stage.mics, 1)})

                for key in sorted(menu.keys()):
                    print(f"{key}: {menu[key]}")

                while (selection := int(input("Make a selection: "))) not in menu.keys():
                    print("Invalid selection!")

                if menu[selection] == "Exit":
                    break

                mic = menu[selection]

                while True:

                    menu = {0: "Exit",
                            1: "Remove",
                            2: "Operate"}

                    for key in sorted(menu.keys()):
                        print(f"{key}: {menu[key]}")

                    while (selection := int(input("Make a selection: "))) not in menu.keys():
                        print("Invalid selection!")

                    if menu[selection] == "Exit":
                        break

                    elif menu[selection] == "Remove":
                        stage.mics.remove(mic)

                    elif menu[selection] == "Operate":
                        operate_mic(mic = mic)

if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('logfile.log')
    formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)

    # add file handler to logger
    logger.addHandler(file_handler)

    # setup
    try:
        stage = pk.load(open("config.pkl", "rb"))

    except:

        motors = [Motor(id =num, ip_address= f"192.168.1.{num+2}", encoder_direction= -1, kD = .005, logger = logger) for num in range(3)]
        motors[1].position = np.array([226,69,0])
        motors[2].position = np.array([226,546,0])

        mic = Mic(name = "Test Mic", motors=motors)
        stage = Stage(mics = [mic])

        stage.setup()

    # main
    try:
        operate_stage(stage = stage)

    finally:
        pk.dump(stage, open("config.pkl", "wb"))
