from typing import Match
import numpy as np
import pickle as pk
import socket as skt

from datetime import datetime
from pytz import timezone
from time import sleep
from numpy.linalg import norm


SKT = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)  # Set Up the Socket
SKT.settimeout(0)  # only wait 1 second for a response

AXIS = ["X", "Y", "Z"]

PORT = 5000
K = 327.48538
STEP_SIZE = K
DELAY = 0
home = np.array([0, 0, 0])

log = open("log.txt", "a+")

def position_input():

    while True:

        try:

            user_input = [float(coordinate) for coordinate in input("Enter the coordinates: ").split()]

        except:
            
            print("Invalid input!")

        else:

            break


    match len(user_input):

        case 1:

            return np.array([0, 0] + user_input) * K

        case 2:

            return np.array(user_input + [0]) * K

        case 3: 

            return np.array(user_input) * K

        case _:

            return 

class Motor:

    def __init__(self, ip_adress = "192.168.1.2", id = 0):

        self.id = id
        self.adress = (ip_adress, PORT)
        self.position = self.get_mic_position()
        self.length = self.get_length()
        self.target = self.length

    def __str__(self):

        return f"Motor {self.id} (ip = {self.adress[0]}, position = {np.array2string(self.position)} cm, length = {self.length} cm)"

    def __repr__(self):

        return str(self)

    def send(self, message):

        SKT.sendto(bytes(message, "utf-8"), self.adress)
        print(f"[{datetime.now()}] Sent: {message}  to:  {str(self.adress[0])}", file = log)

        return message

    def recieve(self):

        try:

            count, _ = SKT.recvfrom(2048)
            count = count.decode("utf-8")

        except:

            print(f"[{datetime.now()}] Timeout of {self.adress[0]}", file = log)

            return 0

        print(f"[{datetime.now()}] Recieved: {count} from: {self.adress[0]}", file = log)

        return int(count)

    def send_target(self, position):

        self.target = norm(self.position - position)

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
        self.edir = self.recieve()

        return self.edir

    def toggle_encoder_dir(self):

        self.send("DM")
        self.encoder_dir = self.recieve()

        return self.encoder_dir
    
    def get_mic_position(self):

        print(f"\nRetrieving the mic position from motor {self.id} ...")
        position = []

        for axis in ["X", "Y", "Z"]:

            self.send("M" + axis)
            position.append(self.recieve())

        return np.array(position)
    
    def compute_error(self):

        self.get_length()
        error = (self.target - self.length) / self.length

        return error

    def operate(self):

        method_list = [method for method in dir(Motor) if method.startswith('__') is False]
        menu = ({i + 2: name for i, name in enumerate(method_list) if name != "motors"})
        menu.update({0: "Exit", 
                     1: "Move"})

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
                            user_input = K * float(input("Enter the amount: "))
                        
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
                            user_input = K * float(input("Enter the value: "))
                        
                        except:

                            print("Invalid input!")

                        else:

                            break
                    
                    self.set_length(user_input)
                    print(f"Got: {self.length}")

class Mic:
    
    def __init__(self, motors = Motor(), id = 0, name = "blank"):

        self.id = id
        self.name = name
        self.motors = motors
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

        num_steps = round(norm(stop - start) / STEP_SIZE)
        steps = np.arange(num_steps)    # the different positions that are reached
        
        for step in range(num_steps):
            target = 1
            for motor in self.motors:


            # retry sending each step up to 3 times 
                for _ in range(3):

                    distance = stop - start
                    if motor.send_target(start + distance / norm(distance) * step) is None:

                        pass 

                    else:

                        break

            sleep(DELAY)
        
        self.position = stop

    def edit(self):

        menu = {i + 1: name for i, name in enumerate(vars(self).keys()) if name != "motors"}
        menu.update({0: "Exit"})

        while True:

            for key in sorted(menu.keys()):

                print(f"{key}: {menu[key]}")

            while (selection := int(input("Make a selection: "))) not in menu.keys():

                print("Invalid selection!")

            pass

            

            if menu[selection] == "Exit":

                break

            elif menu[selection] == "id":

                self.id = input("Enter the new id: ")

            elif menu[selection] == "name":

                self.name = input("Enter the new name: ")
            
            elif menu[selection] == "position":

                self.position = position_input()
        
        return self

    def move(self, position):

        self.set_postion(self.position + position)
        
    def calibrate(self):

        for motor in self.motors:

            print(motor)
            motor.operate()
    
    def operate(self):

        while True:

            menu = {"0": "Exit",
                    "1": "Calibrate",
                    "2": "Home",
                    "3": "Move",
                    "4": "Edit",
                    "4": "Select a motor"}

            for key in sorted(menu.keys()):

                print(f"{key}: {menu[key]}")

            while (selection := input("Make a selection: ")) not in menu.keys():

                print("Invalid selection!")
            
            if menu[selection] == "Exit":

                break

            elif menu[selection] == "Calibrate":

                self.calibrate()

            elif menu[selection] == "Edit":

                self.edit()
            
            elif menu[selection] == "Select a motor":

                menu = {motor.id: motor for motor in self.motors}

                for key in sorted(menu.keys()):

                    print(f"{key}: {menu[key]}")

                while (selection := int(input("Make a selection: "))) not in menu.keys():

                    print("Invalid selection!")

                menu[selection].operate()               

            elif menu[selection] == "Home":
                
                position = position_input()
                self.set_postion(position)

            elif menu[selection] == "Move":

                position = position_input()
                self.move(position)

# setup

try:
    mics, sets = pk.load(open("config.pkl", "rb"))

except:

    mics = []
    sets = {}
    num = int(input("Enter the number of mics:"))
    count = 1

    for i in range(num):

        motors = []
        num = int(input("Enter the number of motors:"))

        for _ in range(num):

            ip_adress = "192.168.1." + str(count + 1)
            motors.append(Motor(ip_adress, count))
            count += 1
            print("\n" + str(motors[-1]))

        mics.append(Mic(motors, i + 1))
        print("\n" + str(mics[-1]))

print(mics)

for mic in mics:

    user_input = input(f"Do you want to calibrate mic {mic.id}? ")

    if user_input in ["Y", "y"]:

        mic.calibrate()

        break

    elif user_input in ["N", "n"]:

        break

# loop

mics[0].operate()

for mic in mics:

    print(mic)

# on exit
pk.dump((mics, sets), open("config.pkl", "wb"))

def save_set(mics):

    sets.update({input("Save as: "): mics})

def edit_mics():

    while True:

        print(*mics)

        menu = {"0": "Exit",
                "1": "Add a mic",
                "2": "Remove a mic"}
        
        selection = menu.get(input("\nMake a selection: "))

        for key in sorted(menu.keys()):

            print(f"{key}: {menu[key]}")

        while (selection := input("Make a selection: ")) not in menu.keys():

            print("Invalid selection!")
                
        if menu[selection] == "Exit":

            break

        elif menu[selection] == "Add a mic":

            mics.append(Mic().edit())

        elif menu[selection] == "Remove a mic":

            pass    

def recall_set():

    while True:

        menu = {index: set_name for index, set_name in enumerate(sets.keys(), 1)}
        menu.update({0: "Exit"})

        for key in sorted(menu.keys()):

            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():

            print("Invalid selection!")

        set = sets[menu[selection]]

        for mic in mics:

            position = next(filter(lambda save: save.id == mic.id, set)).position
            mic.set_position(position)
                
        if menu[selection] == "Exit":

            break

def remove_set():

    while True:

        menu = {index: set_name for index, set_name in enumerate(sets.keys(), 1)}
        menu.update({0: "Exit"})

        for key in sorted(menu.keys()):

            print(f"{key}: {menu[key]}")

        while (selection := int(input("Make a selection: "))) not in menu.keys():

            print("Invalid selection!")

        del sets[menu[selection]]

        for mic in mics:

            position = next(filter(lambda save: save.id == mic.id, set)).position
            mic.set_position(position)
                
        if menu[selection] == "Exit":

            break