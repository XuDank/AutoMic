from automic import *
from genuino import *

def position_input():
    while True:
        try:
            user_input = [float(coordinate) for coordinate in input(
                "Enter coordinates >> ").split()]

            if len(user_input) == 1:
                return np.array([0, 0] + user_input)

            elif len(user_input) == 2:
                return np.array(user_input + [0])

            elif len(user_input) == 3:
                return np.array(user_input)

        except:
            print("Invalid input!")


def operate_motor(motor):
    while True:
        print("-"*50)
        print(f"Motor {motor.number}")
        print(f"  {'Status':10}: {motor.status}")
        print(f"  {'Address':10}: {motor.address}")
        print(f"  {'Position':10}: {motor.position} inches")
        print(f"  {'Length':10}: {motor.length} inches")

        menu = {0: "Exit",
                1: "Edit the number of pulses per inches",
                2: "Send",
                3: "Edit the number",
                4: "Edit the IP address",
                5: "Edit the position",
                6: "Edit the cable length",
                7: "Change the direction",
                8: "Edit the PID values",
                9: "Change the direction of the encoder",
                10: "Edit the encoder resolution",
                11: "Move",
                12: "Get the current cable length"}

        selection = menu_selection(menu)

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Change the direction of the encoder":
            motor.toggle_encoder()

        elif menu[selection] == "Change the direction":
            motor.toggle_encoder()
            motor.toggle_motor()

        elif menu[selection] == "Send":
            motor.send(input("Enter the message >> "))

        elif menu[selection] == "Edit the number":
            print(f"Current number: {motor.id}")
            motor.id = int(input("Enter the new number >> "))

        elif menu[selection] == "Edit the IP address":
            print(f"Current IP address: {motor.address}")
            motor.address = (
                str(input("Enter the new IP address >> ")), 5000)

        elif menu[selection] == "Edit the number of pulses per inches: ":
            print(f"Current number of pulses per inches: {motor.pulses_per_inches} inches")

            motor.pulses_per_inches = float(
                input("Enter the new number of pulses per inches >> "))

        elif menu[selection] == "Edit the position":
            print(f"Current position: {motor.position}")

            motor.position = position_input()

        elif menu[selection] == "Edit the PID values":
            print(f"Current values: {motor.PID}")

            motor.pid = list(position_input())

        elif menu[selection] == "Edit the cable length":
            print(f"Current cable length: {motor.length}")

            motor.length = float(input("Enter the new cable length >> "))

            motor.set_length(motor.length)

        elif menu[selection] == "Move":
            length = motor.length + float(input("Enter the amount (in inches) >> "))
            motor.send_length(length)

        else:
            print("Not implemented in the code!")


def operate_mic(mic):
    while True:
        print("-"*50)
        print(f"{mic.name}:")
        print(f"  {'Position':9}: {mic.position} inches")
        print(f"  {'Status':9}: {[motor.status for motor in mic.motors]}")

        menu = {0: "Exit",
                1: "Move",
                2: "Add a motor",
                3: "Remove a motor",
                4: "Edit the name",
                5: "Edit the position",
                6: "Select a motor",
                7: "Set the position",
                8: "Step move",
                9: "Broadcast",
                10: "Home",
                11: "Calibrate"}

        selection = menu_selection(menu)

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Move":
            mic.move(position_input())

        elif menu[selection] == "Calibrate":
            print("Initial position\n")
            initial_position = position_input()

            while True:
                menu = {0: "Exit"}
                menu.update({index: motor for index,
                            motor in enumerate(mic.motors, 1)})

                selection = menu_selection(menu)
                
                if menu[selection] == "Exit":
                    break

                else:
                    operate_motor(menu[selection])

            mic.home(initial_position)

            initial_lengths = [motor.length for motor in mic.motors]

            print("Final position\n")

            final_position = position_input()

            theoretical_distances = [norm(final_position - motor.position) - initial_length  for motor, initial_length in zip(mic.motors, initial_lengths)]
            theoretical_distances = np.array(theoretical_distances)

            print(f"Theoretical distances traveled: {theoretical_distances} inches")

            while True:
                menu = {0: "Exit"}
                menu.update({index: motor for index,
                            motor in enumerate(mic.motors, 1)})

                selection = menu_selection(menu)
                
                if menu[selection] == "Exit":
                    break

                else:
                    operate_motor(menu[selection])

            actual_distances = np.array([motor.length - initial_length for motor, initial_length in zip(mic.motors, initial_lengths)])

            print(f"Actual distances traveled: {actual_distances} inches")

            fudge_factors = actual_distances / theoretical_distances

            print(f"Fudge factors: {fudge_factors * 100}%")

            for motor, fudge_factor in zip(mic.motors, fudge_factors):
                motor.pulses_per_inches *= fudge_factor

            mic.home(final_position)

        elif menu[selection] == "Step move":
            mic.step_move(position_input())

        elif menu[selection] == "Add a motor":
            mic.motors.append(Motor(server=mic.motors[0].server))

        elif menu[selection] == "Edit the name":
            mic.name = input("Enter the new name >> ")

        elif menu[selection] == "Edit the position":
            mic.position = position_input()

        elif menu[selection] == "Set the position":
            mic.home(position_input())

        elif menu[selection] == "Home":
            for motor in mic.motors:
                while True:
                    menu = {0: "Exit",
                            1: "Move"}

                    selection = menu_selection(menu)

                    if menu[selection] == "Exit":
                        break

                    elif menu[selection] == "Move":
                        length = motor.length + float(input("Enter the amount (in inches) >> "))
                        motor.send_length(length)
                
            mic.home(position_input())


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
            mic.broadcast(input("Broadcast >> "))

        else:
            print("Not implemented in the code!")


def operate_stage(stage):
    while True:
        print("-"*50)
        print(f"Stage:")
        status = {mic.name: [motor.status for motor in mic.motors] for mic in stage.mics}
        print(f"  {'Status':8}: {status}\n")
        print(f"  {'Presets':8}: {list(stage.presets.keys())}")

        menu = {0: "Exit",
                1: "Save preset",
                2: "Select preset",
                3: "Remove a motor",
                4: "Select a mic"}

        selection = menu_selection(menu)

        if menu[selection] == "Exit":
            break

        elif menu[selection] == "Save preset":
            stage.save_preset(input("Save as >> "))

        elif menu[selection] == "Select preset":

            while True:
                if stage.presets == dict():
                    break

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

                        break

                    elif menu[selection] == "Recall":
                        stage.recall_preset(preset)

                        break

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


def menu_selection(menu, prompt="Select an option >> "):
    print("-"*50)

    for key in sorted(menu.keys()):
        print(f"{key:2}.  {menu[key]}")
    
    print("-"*50)

    while (selection := int(input(f"\n{prompt}"))) not in menu.keys():
        print("Invalid selection!")

    return selection
