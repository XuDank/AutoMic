import numpy as np
import pickle as pk
import socket as skt

from datetime import datetime
from ipaddress import ip_address as adr
from numpy.linalg import norm


def position_input():
    while True:
        try:
            user_input = [float(coordinate) for coordinate in input(
                "Enter the coordinates: ").split()]

            match len(user_input):
                case 1:
                    return np.array([0, 0] + user_input)

                case 2:
                    return np.array(user_input + [0])

                case 3:
                    return np.array(user_input)

        except:
            print("Invalid input!")


class Motor:
    steps_per_inch = 327.48538
    log = open("log.txt", "a+")
    socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
    socket.settimeout(0)

    def __init__(self, id=0, ip="192.168.1.2", position=np.array([0, 0, 0])):
        self.id = id
        self.ip_address = (ip, 5000)
        self.position = position
        self.length = self.get_length()
        self.target = self.length

    def __str__(self):
        return f"Motor {self.id} (ip = {self.ip_address[0]}, position = {np.array2string(self.position)} cm, length = {self.length} cm)"

    def __repr__(self):
        return str(self)

    def edit(self):
        menu = {0: "Exit"}
        menu.update({menu.keys()[-1] + 1: name.capitalize()
                     for name in vars(self).keys() if name not in ["target", "edit"]})

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    break

                case "Id":
                    self.id = int(input("Enter the ID: "))

                case "Ip_address":
                    while True:
                        try:
                            self.ip_address = (
                                adr(input("Enter the IP address: ")), 5000)
                        except:
                            print("Invalid IP ip_address!")
                        else:
                            break

                case "Position":
                    self.position = position_input()

                case "Length":
                    self.length = float(input("Enter the length: "))

        return self

    def send(self, message):
        self.socket.sendto(bytes(str(message), "utf-8"), self.ip_address)
        print(
            f"[{datetime.now()}] Sent: {message}  to:  {str(self.ip_address[0])}", file=self.log)

        return message

    def recieve(self):
        try:
            count, _ = self.socket.recvfrom(2048)
            count = count.decode("utf-8")

        except:
            print(
                f"[{datetime.now()}] Timeout of {self.ip_address[0]}", file=self.log)

            return 0

        print(
            f"[{datetime.now()}] Recieved: {count} from: {self.ip_address[0]}", file=self.log)

        return int(count)

    def send_target(self, position):
        self.target = norm(self.position - position) * self.steps_per_inch

        return self.send(str(int(self.target)))

    def get_length(self):
        self.send("P")
        self.length = self.recieve()

        return self.length

    def set_length(self, length):
        self.send("E" + str(length))
        self.length = self.recieve()

        return self.length

    def stop(self):
        self.send("S")
        self.length = self.recieve()

        return self.L

    def toggle_endoder_dir(self):
        self.send("DE")

        return self.recieve()

    def toggle_encoder_dir(self):
        self.send("DM")

        return self.recieve()

    def compute_error(self):
        self.get_length()
        error = (self.target - self.length) / self.length

        return error

    def operate(self):
        method_list = [method for method in dir(
            Motor) if method.startswith('__') is False]

        menu = {0: "Exit",
                1: "Move"}
        menu.update({menu.keys()[-1] + 1: name.capitalize()
                     for name in method_list if name not in ["motors"]})

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    break

                case "Move":
                    while True:
                        try:
                            user_input = self.steps_per_inch * \
                                float(input("Enter the amount: "))

                        except:
                            print("Invalid input!")

                        else:
                            break

                    self.target += user_input
                    self.send(str(int(self.target)))

                    break

                case "set_length":
                    while True:
                        try:
                            user_input = self.steps_per_inch * \
                                float(input("Enter the value: "))

                        except:
                            print("Invalid input!")

                        else:
                            break

                    self.set_length(user_input)
                    print(f"Got: {self.length}")


class Mic:

    def __init__(self, id=0, name="blank", motors=[]):
        self.id = id
        self.name = name
        self.motors = motors

        if not motors:
            self.position = np.array([0, 0, 0])
        else:
            self.position = self.motors[0].get_mic_position()

    def __str__(self):
        string = f"{self.name} mic: (id: {self.id}, postition = {(self.position)}, motors: {len(self.motors)})"

        for motor in self.motors:
            string += "\n\t" + str(motor)

        return string

    def __repr__(self):
        return f"{self.name} mic: (id: {self.id}, postition = {(self.position)}, motors: {len(self.motors)})"

    def set_postion(self, position):
        start = self.position
        stop = position
        distance = stop - start

        num_steps = round(norm(distance) / self.motors[0].steps_per_inch)

        for step in range(num_steps):
            for motor in self.motors:
                motor.send_target(start + num_steps * motor.steps_per_inch)
                # add a delay

        self.position = stop

    def edit(self):
        menu = {0: "Exit",
                1: "Add a motor",
                2: "Delete a motor"}
        menu.update({menu.keys()[-1] + 1: name.capitalize()
                     for name in vars(self).keys() if name not in []})

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    if not self.motors:
                        print("Mic needs at least one motor!")

                    else:
                        break

                case "Add a motor":
                    self.motors.append(Motor().edit())

                case "Id":
                    self.id = input("Enter the new id: ")

                case "Name":
                    self.name = input("Enter the new name: ")

                case "Position":
                    self.position = position_input()

        return self

    def move(self, position):
        self.set_postion(self.position + position)

    def calibrate(self):
        for motor in self.motors:
            print(motor)
            motor.operate()

    def operate(self):

        menu = {0: "Exit",
                1: "Calibrate",
                2: "Home",
                3: "Move",
                4: "Edit",
                5: "Select a motor"}

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    break

                case "Calibrate":
                    self.calibrate()

                case "Edit":
                    self.edit()

                case "Select a motor":
                    menu = {motor.id: motor for motor in self.motors}

                    for key in sorted(menu.keys()):
                        print(f"{key}: {menu[key]}")

                    while (selection := int(input("Make a selection: "))) not in menu.keys():
                        print("Invalid selection!")

                    menu[selection].operate()

                case "Home":
                    position = position_input()
                    self.set_postion(position)

                case "Move":
                    position = position_input()
                    self.move(position)


def edit_mics():
    menu = {"0": "Exit",
            "1": "Add a mic",
            "2": "Remove a mic"}

    while True:
        print(*mics)
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        match menu[selection]:
            case "Exit":
                break

            case "Add a mic":
                mics.append(Mic().edit())

            case "Remove a mic":
                pass


def recall_set():
    menu = {0: ("Exit")}
    menu.update({menu.keys()[-1] + 1: (set_name, sets[set_name])
                 for set_name in sets.keys()})

    while True:
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key][0]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        match menu[selection][0]:
            case "Exit":
                break

        set = menu[selection][1]

        for mic, save in zip(mics, set):
            mic.set_position(save.position)


def remove_set():
    menu = {0: ("Exit")}
    menu.update({menu.keys()[-1] + 1: set_name
                 for set_name in sets.keys()})

    while True:
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        match menu[selection]:
            case "Exit":
                break

        del sets[menu[selection]]


if __name__ == "__main__":
    # setup
    try:
        mics, sets = pk.load(open("config.pkl", "rb"))

    except:
        sets = {}
        num_mics = int(input("Enter the number of mics: "))
        mics = [Mic(index).edit() for index in range(num_mics)]

    print(mics)

    for mic in mics:
        user_input = input(f"Do you want to calibrate mic {mic.id}? ")

        if user_input in ["Y", "y"]:
            mic.calibrate()

            break

        elif user_input in ["N", "n"]:
            break

    # main
    try:
        mics[0].operate()

    finally:
        pk.dump((mics, sets), open("config.pkl", "wb"))
        sets.update({input("Save as: "): mics})
