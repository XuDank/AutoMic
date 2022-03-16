import os
from time import sleep, time
from threading import Thread
import socket as skt
import logging as log

import numpy as np
from numpy.linalg import norm


class Motor:
    """This class is used to send and recieve messages form the motor units."""

    def __init__(self, pulses_per_revolution=150.0 * 11.0, spool_diameter=5, number=0, ip_address="127.0.0.1", port=5000, position=np.array([0, 0, 0]), direction=1, kP=1.0, kI=0.0, kD=0.0):
        self.number = number
        self.address = (ip_address, port)
        self.socket = None
        self.logger = log.getLogger(f"Motor{self.number}")

        # A motor has a thread to recieve udp packets as well as a thread to sync with the motor on startup or during a movement
        self.recieve_thread = None
        self.sync_thread = None

        # Wether the motor is ready or busy
        self.status = ""  # Ready to move or not

        # Motor's physical position and the length reported by the controller
        self.position = position
        self.length = norm(self.position)

        # Used to convert the encoder counts to cm
        self.pulses_per_cm = pulses_per_revolution / (np.pi * spool_diameter)

        # Parameters for the controller
        self.direction = direction
        self.PID = [kP, kI, kD]

    def __str__(self):
        return f"Motor {self.number} (IP = {self.address}, Position = {np.array2string(self.position)} cm, Cable Length = {self.length} cm)"

    def __repr__(self):
        return str(self)

    def __getstate__(self):
        self.__dict__.pop('recieve_thread')
        self.__dict__.pop('sync_thread')
        self.__dict__.pop('socket')
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.update(
            {"recieve_thread": None, "sync_thread": None, "socket": None})

    def setup(self, mic_name="blank mic"):
        self.logger = log.getLogger(f"Motor{self.number}")
        self.logger.setLevel(log.DEBUG)

        file_handler = log.FileHandler(
            f"log/{mic_name}/motor{self.number}.log", mode="w")
        formatter = log.Formatter("%(asctime)s : %(message)s")

        file_handler.setFormatter(formatter)

        # add file handler to logger
        self.logger.addHandler(file_handler)

        self.socket = skt.socket(skt.AF_INET, skt.SOCK_STREAM)

        print(f"Connecting to {self.address}")

        while True:
            try:
                self.socket.connect(self.address)
                print(f"Connected to {self.address}")
                break
            
            except Exception as error:
                self.logger.exception(error)
                print(f"Failed to connect to {self.address}")
                sleep(1.0)

        self.recieve_thread = Thread(target=self.recieve, daemon=True)
        self.recieve_thread.start()

        self.send_parameters()

        self.sync_thread = Thread(target=self.sync, daemon=True)
        self.sync_thread.start()

    def reconnect(self):
        self.status = "Disconnected"
        print(f"Reconnecting to {self.address[0]}")

        try:
            self.socket.close()
            self.socket = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
            self.socket.connect(self.address)

        except Exception as error:
            self.logger.exception(error)
            self.logger.info("Failed to reconnect")

    def recieve(self):
        while True:
            try:
                messages = self.socket.recv(2048)
                messages = messages.decode("ascii").splitlines()
                # print(self.address, messages)

                for message in messages:
                    self.logger.info(f"Recieved: {message}")
                    self.read(message)

            except Exception as error:
                self.logger.exception(error)
                print(error)
                pass

    def send(self, message):
        try:
            self.socket.send(bytes(f"{message}\n", "ascii"))
            self.logger.info(f"Sent: {message}")

        except Exception as error:
            self.logger.exception(error)
            self.reconnect()

    def read(self, message):
        try:
            self.length = float(message) / self.pulses_per_cm

        except ValueError:
            if message == "Ready":
                self.status = message

            elif message == "Busy":
                self.status = message

            elif message == "Setup":
                self.send_parameters()
                self.status = message
            else:
                pass

    def sync(self):
        while True:
            sleep(0.5)  # In seconds
            self.send("Sync")
                
    def send_length(self, length):
        self.status = ""
        self.send(length * self.pulses_per_cm)

    def send_coordinates(self, position):
        # All the math is here
        self.send_length(norm(self.position - position))

    def get_length(self):
        self.send("P")

    def set_length(self, length):
        self.length = length

        self.send(f"E{self.length * self.pulses_per_cm}")

    def set_direction(self, direction):
        self.direction = direction

        self.send(f"DM{direction[0]}")
        self.send(f"DE{direction[1]}")

    def set_pid(self, PID):
        self.PID = PID

        self.send(f"kP{PID[0]}")
        self.send(f"kI{PID[1]}")
        self.send(f"kD{PID[2]}")

    def stop(self):
        self.send("Stop")

    def toggle_motor(self):
        self.direction[1] *= -1

        self.send(f"DM{self.direction[1]}")

    def toggle_encoder(self):
        self.direction[0] *= -1

        self.send(f"DE{self.direction[0]}")

    def send_parameters(self):
        self.set_length(self.length)

        self.set_direction(self.direction)

        self.set_pid(self.PID)


class Mic:
    """This class is used to send and recieve messages form the motor units."""

    def __init__(self, name="blank", motors=[Motor()], position=np.array([0, 0, 0])):
        self.name = name
        self.motors = motors
        self.position = position

        self.status = ""

    def __str__(self):
        string = f"{self.name}: (Postition = {(self.position)}, Motors: {len(self.motors)})"

        for motor in self.motors:
            string += "\n\t" + str(motor)

        return string

    def __repr__(self):
        return f"{self.name}: (Postition = {(self.position)}, Motors: {len(self.motors)})"

    def broadcast(self, message):
        for motor in self.motors:
            Thread(target=motor.send, daemon=True, args=(message, )).start()

    # [TODO] Check for colision and reachability (vector intersection)
    def move(self, position):
        # Check the status of the motors
        if [motor for motor in self.motors if motor.status != "Ready"] == []:
            # [TODO] Make sure it gets there before setting the value
            self.position = position

            for motor in self.motors:
                Thread(target=motor.send_coordinates,
                       daemon=True, args=(position, )).start()

        else:
            print("Motors not ready!")

    def step_move(self, position):
        # sends one message per centimeter travelled by the motor
        # only if all the mics are ready
        start = self.position
        stop = position
        distance = stop - start

        for step in np.arange(0, norm(distance)) / norm(distance):
            if [motor for motor in self.motors if motor.status == "Stopped"] != []:
                break

            position = start + step * distance

            for motor in self.motors:
                motor.move(position)

            sleep(0.1)

            # Check if they are all not moving
            while [motor for motor in self.motors if motor.status != "Moving"] != []:
                pass


class Stage:
    # [TODO] Add colision detection/prevention
    def __init__(self, mics=[Mic()], presets={"blank preset name": {"blank mic name": np.array([0, 0, 0])}}):
        self.mics = mics
        self.presets = presets

    def __str__(self):
        string = f"Stage: (Mics: {len(self.mics)})"

        return string

    def __repr__(self):
        return str(self)

    def setup(self):
        for mic in self.mics:
            os.makedirs(f"{os.getcwd()}/log/{mic.name}", exist_ok=True)

            for motor in mic.motors:
                Thread(target=motor.setup,
                       daemon=True, args=(mic.name, )).start()

    def recall_preset(self, preset_name="blank preset name", preset={"blank mic name": np.array([0, 0, 0])}):
        for mic in self.mics:

            try:
                position = next(
                    preset[name] for name in preset.keys() if mic.name == preset_name)

            except Exception as error:
                self.logger.exception(error)
                position = np.array([0, 0, 0])

            mic.move(position)

    def save_preset(self, name="untitled"):
        self.presets[name] = {mic.name: mic.position for mic in self.mics}
