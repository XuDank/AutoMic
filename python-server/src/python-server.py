from time import sleep
from click import edit
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

            if len(user_input) == 1:
                return np.array([0, 0] + user_input)

            elif len(user_input) == 2:
                return np.array(user_input + [0])

            elif len(user_input) == 3:
                return np.array(user_input)

        except:
            print("Invalid input!")


class Motor:

    def __init__(self, pulses_per_revolution = 150.0 * 11.0, spool_diameter = 5, id = 0, ip_adress = "192.168.1.2", position = np.array([0, 0, 0]), length = 0.0, motor_direction = 1, encoder_direction = 1, kP = 1.0, kI = 0.0, kD = 0.0):
        self.pulses_per_revolution = pulses_per_revolution
        self.spool_diameter = spool_diameter
        self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)

        self.id = id
        self.ip_address = (ip_adress, 5000)
        self.position = position
        self.length = length
        self.target = self.length
        self.status = False

        self.motor_direction = motor_direction
        self.encoder_direction = encoder_direction

        self.kP = kP
        self.kI = kI
        self.kD = kD

    def __str__(self):
        return f"Motor {self.id} (ip = {self.ip_address[0]}, position = {np.array2string(self.position)} cm, length = {self.length} cm)"

    def __repr__(self):
        return str(self)

    def __getstate__(self):
        self.__dict__.pop('socket')
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state
        self.status = False
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.settimeout(1)

    def edit(self):
        menu = {0: "Exit"}
        menu.update({list(menu.keys())[-1] + index: name
                     for index, name in enumerate(vars(self).keys(), 1) if name not in ["target", "edit", "pulses_per_cm"]})

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            if menu[selection] == "Exit":
                break

            elif menu[selection] ==  "id":
                print(f"Current id: {self.id}")
                self.id = int(input("Enter the ID: "))

            elif menu[selection] ==  "ip_address":
                print(f"Current ip address: {self.ip_address}")

                while True:
                    try:
                        self.ip_address = (
                            str(adr(input("Enter the ip address: "))), 5000)
                    except:
                        print("Invalid ip address!")
                    else:
                        break

            elif menu[selection] ==  "spool_diameter":
                print(f"Current spool_diameter: {self.spool_diameter}")

                self.spool_diameter = float(input("Enter the spool_diameter: "))
                self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)

            elif menu[selection] ==  "pulses_per_revolution":
                print(f"Current pulses_per_revolution: {self.pulses_per_revolution}")

                self.pulses_per_revolution = float(input("Enter the pulses_per_revolution: "))
                self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)

            elif menu[selection] ==  "pulses_per_cm":
                print(f"Current pulses_per_cm: {self.pulses_per_cm}")
                self.pulses_per_cm = self.pulses_per_revolution / (np.pi * self.spool_diameter)
                print(f"Updated pulses_per_cm: {self.pulses_per_cm}")

            elif menu[selection] ==  "position":
                print(f"Current position: {self.position}")

                self.position = position_input()

            elif menu[selection] ==  "length":
                print(f"Current length: {self.length}")

                self.length = float(input("Enter the length: "))

        return self

    def send(self, message):
        self.socket.sendto(bytes(str(message), "utf-8"), self.ip_address)
        print(
            f"[{datetime.now()}] Sent: {message}  to:  {str(self.ip_address[0])}")#, file=open("log.txt", "a+"))

        return message

    def recieve(self):
        try:
            message = self.socket.recv(2048)
            message = message.decode("utf-8")

            print(
                 f"[{datetime.now()}] Recieved: {message} from: {self.ip_address[0]}")#, file=open("log.txt", "a+"))

        except:
            print(
                f"[{datetime.now()}] Timeout of {self.ip_address[0]}")#, file=open("log.txt", "a+"))
            self.status = not self.status

            return None

        try:    
            return float(message)
        
        except:
            return message

    def send_target(self, position):
        self.target = norm(self.position - position)
        self.send(self.target * self.pulses_per_cm)

    def get_length(self):
        self.send("P")
        self.length = self.recieve() / self.pulses_per_cm

    def set_length(self, length):
        self.send("E" + str(length * self.pulses_per_cm))
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
        print(f"{self.length}, {self.pulses_per_cm}")
        self.send(f"E{self.length * self.pulses_per_cm}")

        self.send(f"DM{self.motor_direction}")
        self.send(f"DE{self.encoder_direction}")

        self.send(f"kP{self.kP}")
        self.send(f"kI{self.kI}")
        self.send(f"kD{self.kD}")

        self.send("done")

        response = self.recieve()

        if response == "synced":
            self.status = True
        
        else:
            self.status = False

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
            

            if menu[selection] == "Exit":
                break

            elif menu[selection] == "stop":
                self.stop()
                pass

            elif menu[selection] == "kP":
                self.kP = float(input("Enter kP: "))
                self.send("kP" + str(self.kP))

            elif menu[selection] == "kI":
                self.kI= float(input("Enter kI: "))
                self.send("kI" + str(self.kI))

            elif menu[selection] == "kD":
                self.kD = float(input("Enter kD: "))
                self.send("kD" + str(self.kD))

            else:
                print("Not implemented lol")

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

            if menu[selection] == "Exit":
                break

            elif menu[selection] == "edit":
                self.edit()

            elif menu[selection] == "compute_error":
                self.compute_error()

            elif menu[selection] == "pid_tuning":
                self.pid_tuning()

            elif menu[selection] == "sync":
                self.sync()

            elif menu[selection] == "stop":
                self.stop()

            elif menu[selection] == "move (absolute)":
                self.target = norm(position_input())
                self.send(str(self.target * self.pulses_per_cm))

                print(f"Target: {self.target * self.pulses_per_cm}")
                

            elif menu[selection] == "recieve":
                print(f"Got: {self.recieve()}")

            elif menu[selection] == "move (relative)":
                self.target += norm(position_input())
                self.send(str(self.target * self.pulses_per_cm))
                
                print(f"Target: {self.target * self.pulses_per_cm}")

            elif menu[selection] == "get_length":
                self.get_length()

                print(f"Current length: {self.length}")

            elif menu[selection] == "set_length":
                self.set_length(norm(position_input()))

                print(f"Current length: {self.length}")

            elif menu[selection] == "toggle_encoder":
                self.toggle_encoder()

            elif menu[selection] == "toggle_motor":
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

    def move(self, position):
        for motor in self.motors:
            motor.send_target(position)

    def step_move(self, position):
        start = self.position
        stop = position
        distance = stop - start

        for step in np.arange(0, norm(distance)) / norm(distance):
            self.move(start + step * distance)

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

            if menu[selection] == "Exit":
                break

            elif menu[selection] == "Add a motor":
                self.motors.append(Motor().edit())

            elif menu[selection] == "id":
                self.id = input("Enter the new id: ")

            elif menu[selection] == "name":
                self.name = input("Enter the new name: ")

            elif menu[selection] == "position":
                self.position = position_input()

        return self

    def sync(self):
        status = []

        for motor in self.motors:
            status.append(motor.sync())

        return status

    def calibrate(self):
        for motor in self.motors:
            motor.sync()
            motor.set_length(0)
            motor.send_target(motor.position + 500)

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

        self.move(np.array([0, 0, 0]))                 

    def operate(self):
        self.sync()
        while True:
            menu = {0: "Exit",
                    1: "calibrate",
                    2: "home",
                    3: "move (absolute)",
                    4: "move (relative)",
                    5: "edit",
                    6: "select a motor"}
                    
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            match menu[selection]:
                case "Exit":
                    break

                case "calibrate":
                    self.calibrate()

                case "edit":
                    self.edit()

                case "select a motor":
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

                case "home":
                    self.move(np.array([0, 0, 0]))

                case "move (absolute)":
                    self.position = position_input()
                    self.move(self.position)

                case "move (relative)":
                    self.position += position_input()
                    self.move(self.position)


def select_mic():
    menu = {0: "Exit"}

    menu.update({list(menu.keys())[-1] + index: mic
                 for index, mic in enumerate(mics, 1)})
    
    while True:
        for key in sorted(menu.keys()):
            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():
            print("Invalid selection!")

        if not selection:
            break

        menu[selection].operate()


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
                mics.append(Mic().edit())

            case "Remove a mic":
                menu = {0: "Exit"}

                menu.update({list(menu.keys())[-1] + index: mic
                            for index, mic in enumerate(mics, 1)})
                
                while True:
                    for key in sorted(menu.keys()):
                        print(f"{key}: {menu[key]}")

                    while (selection := int(input("Make a selection: "))) not in menu.keys():
                        print("Invalid selection!")

                    if not selection:
                        break


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
            mic.set_position(save)


def remove_set():
    menu = {0: "Exit"}
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
        motors = [Motor(id = 2, motor_direction= -1, spool_diameter=5.9),
                  Motor(id = 3, ip_adress= "192.168.1.3", encoder_direction= -1, spool_diameter=5.9),
                  Motor(id = 4, ip_adress= "192.168.1.4", encoder_direction= -1, spool_diameter=5.9)]

        mics = [Mic(motors=  motors)]
        sets = {}

    # main
    try:
        menu = {0: "Exit",
                1: "select mic",
                2: "recall set",
                3: "save set",
                4: "edit mics",
                5: "edit sets"}

        while True:
            for key in sorted(menu.keys()):
                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():
                print("Invalid selection!")

            if menu[selection] == "Exit":
                break

            elif menu[selection] == "select mic":
                while True:
                    menu = {0: "Exit"}
                    menu.update({index: mic for index, mic in enumerate(mics, 1)})

                    for key in sorted(menu.keys()):
                        print(f"{key}: {menu[key]}")

                    while (selection := int(input("Make a selection: "))) not in menu.keys():
                        print("Invalid selection!")

                    if menu[selection] == "Exit":
                        break

                    menu[selection].operate()

            elif menu[selection] == "edit mics":
                edit_mics()
                
    finally:
        pk.dump((mics, sets), open("config.pkl", "wb"))