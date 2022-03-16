import pickle as pk
from automic import *
from genuino import *


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


def operate_motor(motor):
    print(motor)

    while True:
        menu = {0: "Exit",
                1: "Edit the number of pulses per cm",
                2: "",
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

        selection = menu_selection(menu)

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Change the direction of the encoder":
            motor.toggle_encoder()

        elif menu[selection] == "Change the direction":
            motor.toggle_encoder()
            motor.toggle_motor()

        elif menu[selection] == "Send":
            motor.send(input("Enter the message: "))

        elif menu[selection] == "Edit the ID":
            print(f"Current ID: {motor.id}")
            motor.id = int(input("Enter the new ID: "))

        elif menu[selection] == "Edit the IP address":
            print(f"Current IP address: {motor.address}")
            motor.address = (
                str(input("Enter the new IP address: ")), 5000)

        elif menu[selection] == "Edit the number of pulses per cm: ":
            print(f"Current number of pulses per cm: {motor.pulses_per_cm} cm")

            motor.pulses_per_cm = float(
                input("Enter the new number of pulses per cm: "))

        elif menu[selection] == "Edit the position":
            print(f"Current position: {motor.position}")

            motor.position = position_input()

        elif menu[selection] == "Edit the PID values":
            print(f"Current values: {motor.PID}")

            motor.pid = list(position_input())

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
                6: "Select a motor",
                7: "Set the position",
                8: "Step move",
                9: "Broadcast"}

        selection = menu_selection(menu)

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Move":
            mic.move(position_input())

        elif menu[selection] == "Step move":
            mic.step_move(position_input())

        elif menu[selection] == "Add a motor":
            mic.motors.append(Motor(server=mic.motors[0].server))

        elif menu[selection] == "Edit the name":
            mic.name = input("Enter the new name: ")

        elif menu[selection] == "Edit the position":
            mic.position = position_input()

        elif menu[selection] == "Set the position":
            mic.set_position(position_input())

        elif menu[selection] == "Select a motor":

            while True:
                menu = {0: "Exit"}
                menu.update({index: motor for index,
                            motor in enumerate(mic.motors, 1)})

                selection = menu_selection(menu)

                if menu[selection] == "Exit":
                    break

                motor = menu[selection]

                while True:
                    menu = {0: "Exit",
                            1: "Remove",
                            2: "Operate"}

                    selection = menu_selection(menu)

                    if menu[selection] == "Exit":
                        break

                    elif menu[selection] == "Remove":
                        mic.motors.remove(motor)

                    elif menu[selection] == "Operate":
                        operate_motor(motor)

        elif menu[selection] == "Broadcast":
            mic.broadcast(input("Broadcast: "))

        else:
            print("Not implemented in the code!")


def operate_stage(stage):
    print(stage)

    while True:
        menu = {0: "Exit",
                1: "Save preset",
                2: "Select preset",
                3: "Remove a motor",
                4: "Select a mic"}

        selection = menu_selection(menu)

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Save preset":
            stage.save_preset()

        elif menu[selection] == "Select preset":

            while True:
                menu = {0: "Exit"}
                menu.update({index: preset_name for index,
                            preset_name in enumerate(stage.presets.keys(), 1)})

                selection = menu_selection(menu)

                if menu[selection] == "Exit":
                    break

                preset = menu[selection]

                while True:

                    menu = {0: "Exit",
                            1: "Remove",
                            2: "Recall"}

                    selection = menu_selection(menu)

                    if menu[selection] == "Exit":
                        break

                    elif menu[selection] == "Remove":
                        stage.presets.pop(preset, None)

                    elif menu[selection] == "Recall":
                        stage.recall_preset(preset)

        elif menu[selection] == "Select a mic":
            while True:
                menu = {0: "Exit"}
                menu.update(
                    {index: mic for index, mic in enumerate(stage.mics, 1)})

                selection = menu_selection(menu)

                if menu[selection] == "Exit":
                    break

                mic = menu[selection]

                while True:

                    menu = {0: "Exit",
                            1: "Remove",
                            2: "Operate"}

                    selection = menu_selection(menu)

                    if menu[selection] == "Exit":
                        break

                    elif menu[selection] == "Remove":
                        stage.mics.remove(mic)

                    elif menu[selection] == "Operate":
                        operate_mic(mic=mic)


def menu_selection(menu):
    for key in sorted(menu.keys()):
        print(f"{key}: {menu[key]}")

    while (selection := int(input("Make a selection: "))) not in menu.keys():
        print("Invalid selection!")

    return selection


if __name__ == "__main__":
    # setup
    ip_addresses = [f"192.168.1.{num}" for num in [2, 3, 4]]

    positions = [np.array([0, 0, 0]),
                 np.array([226, 69, 0]),
                 np.array([226, 546, 0])]

    directions = [(1, 1), (1, 1), (1, 1)]

    parameters = zip(ip_addresses, positions, directions)

    motors = [Motor(number=index, position=position, ip_address=ip_address, direction=direction, kD=.005)
              for index, (ip_address, position, direction) in enumerate(parameters)]

    # motors = [Motor(number=index, position=position, port=5000+index, direction=direction, kD=.005)
    #           for index, (ip_address, position, direction) in enumerate(parameters)]

    # fake_motors = [Genuino(address=motor.address) for motor in motors]

    mics = [Mic(name="Test Mic", motors=motors)]
    stage = Stage(mics=mics)

    stage.setup()

    # main
    try:
        operate_stage(stage=stage)

    finally:
        pk.dump(stage, open("config.pkl", "wb"))
