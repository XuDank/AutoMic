from time import sleep
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

    def __init__(self, pulses_per_revolution = 150.0 * 11.0, spool_diameter = 5, id = 0, ip_adress = "192.168.1.2", position = np.array([0, 0, 0]), length = 0.0, motor_direction = 1, encoder_direction = 1, kP = 1.0, kI = 0.0, kD = 0.0):

        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.settimeout(1)

        self.pulses_per_revolution = pulses_per_revolution
        self.spool_diameter = spool_diameter
        self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)

        self.id = id
        self.ip_address = (ip_adress, 5000)
        self.position = position
        self.length = length
        self.target = self.length

        self.motor_direction = motor_direction
        self.encoder_direction = encoder_direction

        self.kP = kP
        self.kI = kI
        self.kD = kD

    def __str__(self):
        return f"Motor {self.id} (ip = {self.ip_address[0]}, position = {np.array2string(self.position)} cm, length = {self.length} cm)"

    def __repr__(self):
        return str(self)

    def edit(self):
        menu = {0: "Exit"}
        menu.update({list(menu.keys())[-1] + index: name
                     for index, name in enumerate(vars(self).keys(), 1) if name not in ["target", "edit", "pulses_per_cm"]})

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    break

                case "id":
                    print(f"Current id: {self.id}")
                    self.id = int(input("Enter the ID: "))

                case "ip_address":
                    print(f"Current ip address: {self.ip_address}")

                    while True:
                        try:
                            self.ip_address = (
                                str(adr(input("Enter the ip address: "))), 5000)
                        except:
                            print("Invalid ip address!")
                        else:
                            break

                case "spool_diameter":
                    print(f"Current spool_diameter: {self.spool_diameter}")

                    self.spool_diameter = float(input("Enter the spool_diameter: "))
                    self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)

                case "pulses_per_revolution":
                    print(f"Current pulses_per_revolution: {self.pulses_per_revolution}")

                    self.pulses_per_revolution = float(input("Enter the pulses_per_revolution: "))
                    self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)

                case "pulses_per_cm":
                    print(f"Current pulses_per_cm: {self.pulses_per_cm}")
                    self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)
                    print(f"Updated pulses_per_cm: {self.pulses_per_cm}")

                case "position":
                    print(f"Current position: {self.position}")

                    self.position = position_input()

                case "length":
                    print(f"Current length: {self.length}")

                    self.length = float(input("Enter the length: "))

        return self

    def send(self, message):
        

        self.socket.sendto(bytes(str(message), "utf-8"), self.ip_address)
        print(
            f"[{datetime.now()}] Sent: {message}  to:  {str(self.ip_address[0])}", file=open("log.txt", "a+"))

        return message

    def recieve(self, type = float):
        try:
            message = self.socket.recv(2048)
            message = message.decode("utf-8")

        except:
            print(
                f"[{datetime.now()}] Timeout of {self.ip_address[0]}", file=open("log.txt", "a+"))

            return 0

        if type == str:
            return message

        print(
            f"[{datetime.now()}] Recieved: {message} from: {self.ip_address[0]}", file=open("log.txt", "a+"))

        
        return float(message)

    def send_target(self, position):
        self.target = norm(self.position - position)
        self.send(self.target * self.pulses_per_cm)

    def get_length(self):
        self.send("P")
        self.length = self.recieve()

    def set_length(self, length):
        self.send("E" + str(length))
        self.length = length

    def stop(self):
        self.send("S")
        self.target = self.length

    def toggle_motor(self):
        self.motor_direction = -self.motor_direction
        self.send("DM" + str(self.motor_direction))


    def toggle_encoder(self):
        self.encoder_direction = -self.encoder_direction
        self.send("DE" + str(self.encoder_direction))


    def compute_error(self):
        self.get_length()
        error = (self.target - self.length)

        print(f"The current error is {error} cm")

        return error

    def sync(self):
        self.send("sync")

        self.send(f"E{self.length * self.pulses_per_cm}")

        self.send(f"DM{self.motor_direction}")
        self.send(f"DE{self.encoder_direction}")

        self.send(f"kP{self.kP}")
        self.send(f"kI{self.kI}")
        self.send(f"kD{self.kD}")

        self.send("done")

        return self.recieve(type= str) == "synced"

    def pid_tuning(self):
        self.sync()

        menu = {0: "Exit",
                1: "stop",
                2: "kP",
                3: "kI",
                4: "kD"}

        while True:

            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")
            
            match menu[selection]:
                case "Exit":
                    break

                case "stop":
                    self.stop()
                    pass

                case "kP":
                    self.kP = float(input("Enter kP: "))
                    self.send("kP" + str(self.kP))

                case "kI":
                    self.kI= float(input("Enter kI: "))
                    self.send("kI" + str(self.kI))

                case "kD":
                    self.kD = float(input("Enter kD: "))
                    self.send("kD" + str(self.kD))

            self.target += 10
            print(f"Target: {self.target} {self.target * self.pulses_per_cm}")
            self.send(str(self.target * self.pulses_per_cm))

    def operate(self):
        self.sync()

        method_list = [method for method in dir(
            Motor) if method.startswith('__') is False]

        menu = {0: "Exit",
                1: "move (absolute)",
                2: "move (relative)"}
        menu.update({list(menu.keys())[-1] + index: name
                     for index, name in enumerate(method_list, 1) if name not in ["motors", "log", "operate", "socket"]})

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    break

                case "edit":
                    self.edit()

                case "compute_error":
                    self.compute_error()

                case "pid_tuning":
                    self.pid_tuning()

                case "sync":
                    self.sync()

                case "stop":
                    self.stop()

                case "move (absolute)":
                    while True:
                        try:
                            user_input = float(input("Enter the amount: "))

                        except:
                            print("Invalid input!")

                        else:
                            break

                    self.target = user_input
                    print(f"Target: {self.target * self.pulses_per_cm}")
                    self.send(str(self.target * self.pulses_per_cm))

                case "recieve":
                    print(f"Got: {self.recieve(str)}")

                case "move (relative)":
                    while True:
                        try:
                            user_input = float(input("Enter the amount: "))

                        except:
                            print("Invalid input!")

                        else:
                            break

                    self.target += user_input
                    print(f"Target: {self.target * self.pulses_per_cm}")
                    self.send(str(self.target * self.pulses_per_cm))

                case "get_length":
                    self.get_length()
                    print(f"Current length: {self.length}")


                case "set_length":
                    while True:
                        try:
                            user_input = float(input("Enter the value: "))

                        except:
                            print("Invalid input!")

                        else:
                            break

                    self.set_length(user_input)
                    print(f"Current length: {self.length}")

                case "toggle_encoder":
                    self.toggle_encoder()

                case "toggle_motor":
                    self.toggle_motor()

class Mic:

    def __init__(self, id=0, name="blank", motors=[Motor()], position=np.array([0, 0, 0])):

        self.id = id
        self.name = name
        self.motors = motors
        self.position = position

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


        for step in np.arange(0, norm(distance)) / norm(distance):
            for motor in self.motors:
                motor.send_target(start + step * distance)

            sleep(.1)

        self.position = stop

    def edit(self):
        menu = {0: "Exit",
                1: "Add a motor",
                2: "Delete a motor"}
        menu.update({list(menu.keys())[-1] + index: name
                     for index, name in enumerate(vars(self).keys(), 1) if name not in []})

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    break

                case "Add a motor":
                    self.motors.append(Motor().edit())

                case "id":
                    self.id = input("Enter the new id: ")

                case "name":
                    self.name = input("Enter the new name: ")

                case "position":
                    self.position = position_input()

        return self

    def sync(self):
        status = []

        for motor in self.motors:
            status.append(motor.sync())

        return status

    def move(self, position):
        self.set_postion(self.position + position)

    def calibrate(self):
        for motor in self.motors:
            print(motor)
            motor.operate()

    def operate(self):
        self.sync()
        while True:
            menu = {0: "Exit",
                    1: "Calibrate",
                    2: "Home",
                    3: "Move",
                    4: "Edit",
                    5: "Select a motor"}
                    
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
                    while True:
                        menu = {0: "Exit"}
                        menu.update({index: motor for index, motor in enumerate(self.motors, 1)})

                        for key in sorted(menu.keys()):
                            print(f"{key}: {menu[key]}")

                        while (selection := int(input("Make a selection: "))) not in menu.keys():
                            print("Invalid selection!")

                        if menu[selection] == "Exit":
                            break

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
        print(mics)
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        match menu[selection]:
            case "Exit":
                break

            case "Add a mic":
                mics.append(Mic(socket).edit())

            case "Remove a mic":
                pass


def recall_set():
    menu = {0: ("Exit")}
    menu.update({list(menu.keys())[-1] + index: (set_name, sets[set_name])
                 for index, set_name in enumerate(sets.keys())})

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
    menu.update({list(menu.keys())[-1] + index: set_name
                 for index, set_name in enumerate(sets.keys())})

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
        mics = [Mic(id=index).edit() for index in range(num_mics)]

    # print(mics)

    # # main
    # try:
    #     mics[0].operate()

    # finally:
    #     pk.dump((mics, sets), open("config.pkl", "wb"))

    Mic(motors = [Motor(id=num, ip_adress=f"192.168.1.{2 + num}", encoder_direction=-1) for num in range(2)]).operate()