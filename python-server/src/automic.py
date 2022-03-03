import numpy as np
import socket as skt
import logging as log

from time import sleep
from threading import Thread
from datetime import datetime
from numpy.linalg import norm


# Have the Arduino send a message if they get locked

class Motor:

    def __init__(self, pulses_per_revolution=150.0 * 11.0, spool_diameter=5, id=0, ip_address="192.168.1.2", port=5000, position=np.array([0, 0, 0]), length=0.0, motor_direction=1, encoder_direction=1, kP=1.0, kI=0.0, kD=0.0, logger = None):
        self.id = id
        self.address = (ip_address, port)
        self.socket = None

        # A motor has a thread to recieve udp packets as well as a thread to sync with the motor on startup or during a movement 
        self.recieve_thread = None
        self.sync_thread = None

        # Wether the motor is ready or busy
        self.status = False
        
        # Motor's physical position and the length reported by the controller
        self.position = position
        self.length = length

        # Used to convert the encoder counts to cm
        self.pulses_per_cm = pulses_per_revolution / (np.pi * spool_diameter)

        # Parameters for the controller
        self.motor_direction = motor_direction
        self.encoder_direction = encoder_direction
        self.PID = [kP, kI, kD]

        # Logging
        self.logger = logger

        
    def __str__(self):
        return f"Motor {self.id} (IP = {self.address}, Position = {np.array2string(self.position)} cm, Cable Length = {self.length} cm)"

    def __repr__(self):
        return str(self)

    def __getstate__(self):
        self.__dict__.pop('recieve_thread')
        self.__dict__.pop('sync_thread')
        self.__dict__.pop('socket')
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.update({"recieve_thread": None, "recieve_thread": None, "socket": None})
        
    def setup(self, sync = False):
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        #self.socket.bind(self.address)
        #self.socket.bind(("0.0.0.0", 5000))

        self.recieve_thread = Thread(target= self.recieve, daemon=True)
        self.recieve_thread.start()

        if sync:
            self.sync_thread = Thread(target= self.sync, daemon=True)
            self.sync_thread.start()

    def recieve(self):
        while True:
            try:
                message, ip_address = self.socket.recvfrom(2048)
                message = message.decode("utf-8")

                self.read(message)
                
                if self.logger is not None:
                    self.logger.info(f"Recieved: {message} from:  {ip_address}")
            except TimeoutError:
                pass
            except Exception as exception:
                pass

    def send(self, message):
        self.socket.sendto(bytes(str(message), "utf-8"), self.address)
        if self.logger is not None:
            self.logger.info(f"Sent: {message}  to:  {self.address}")


    def read(self, message):
        try:
            self.length = float(message) / self.pulses_per_cm
        except:
            if message == "Ready":
                self.status = True

            elif message == "Busy":
                self.status = False

            elif message == "Setup":
                self.send_parameters()
                self.status = True
            else:
                pass
    
    def sync(self):
        while True:
            if not self.status:
                self.send("Sync")
                sleep(0.5)

    def send_length(self, length):
        self.status = False
        self.send(length * self.pulses_per_cm)

    def send_coordinates(self, position):
        # All the math is here 
        self.send_length(norm(self.position - position))

    def get_length(self):
        self.send("P")

    def set_length(self, length):
        self.length = length
        self.send("E" + str(self.length * self.pulses_per_cm))

    def stop(self):
        self.send("S")

    def toggle_motor(self):
        self.motor_direction = -self.motor_direction
        self.send("DM" + str(self.motor_direction))

    def toggle_encoder(self):
        self.encoder_direction = -self.encoder_direction
        self.send("DE" + str(self.encoder_direction))

    def send_parameters(self):
        self.send(f"E{self.length * self.pulses_per_cm}")

        self.send(f"DM{self.motor_direction}")
        self.send(f"DE{self.encoder_direction}")

        self.send(f"kP{self.PID[0]}")
        self.send(f"kI{self.PID[1]}")
        self.send(f"kD{self.PID[2]}")

class Mic:

    def __init__(self, name="blank", motors=[Motor()], position=np.array([0, 0, 0])):
        self.name = name
        self.motors = motors
        self.position = position

    def __str__(self):
        string = f"{self.name}: (Postition = {(self.position)}, Motors: {len(self.motors)})"

        for motor in self.motors:
            string += "\n\t" + str(motor)

        return string

    def __repr__(self):
        return f"{self.name}: (Postition = {(self.position)}, Motors: {len(self.motors)})"

    def move(self, position): # [TODO] Check for colision (vector intersection)
        #if [motor for motor in self.motors if not motor.status] == []: #Check the status of the motors
            self.position = position
            for motor in self.motors:
                motor.send_coordinates(self.position)

    def step_move(self, position):
        # sends one message per centimeter travelled by the motor
        # only if all the mics are ready
        if [motor for motor in self.motors if not motor.status] == []:

            start = self.position
            stop = position
            distance = stop - start

            for step in np.arange(0, norm(distance)) / norm(distance):
                self.position = start + step * distance

                if not self.move(self.position):
                    break


class Stage:
    # colision detection thread?

    def __init__(self, mics = [Mic()], presets={"blank preset name": {"blank mic name": np.array([0, 0, 0])}}):
        self.mics = mics
        self.presets = presets
    
    def __str__(self):
        string = f"Stage: (Mics: {len(self.mics)})"

        for mic in self.mics:
            string += "\n\t" + str(mic)

        return string

    def __repr__(self):
        return f"Stage: (Mics: {len(self.mics)})"

    def setup(self):
        for mic in self.mics:
            for motor in mic.motors:
                motor.setup(True)

    def recall_preset(self, preset_name = "blank preset name",preset={"blank mic name": np.array([0, 0, 0])}):
        for mic in self.mics:
            try:
                position = next(preset[name] for name in preset.keys() if mic.name == preset_name)
            except:
                position = np.array([0,0,0])
                
            mic.move(position)

    def save_preset(self, name="untitled"):
        self.presets[name] = {mic.name: mic.position for mic in self.mics}
