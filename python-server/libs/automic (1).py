import os
import logging as log
import pickle as pk
import socket as skt

from csv import reader
from threading import Thread, Lock
from time import sleep, time

import numpy as np
from numpy.linalg import norm
from scipy.optimize import root


class Motor:
    """This class is used to send and recieve messages form the motor units."""

    def __init__(self, pulses_per_revolution=150.0 * 11.0, spool_diameter=5/2.54, number=0, ip_address="127.0.0.1", port=5000, position=np.array([0, 0, 0]), direction=[1, 1], kP=1.0, kI=0.0, kD=0.0):
        self.number = number
        self.address = (ip_address, port)
        self.mic = None

        self.socket = None
        self.logger = None

        # A motor has a thread to recieve udp packets as well as a thread to sync with the motor on startup or during a movement
        self.recieve_thread = None
        self.sync_thread = None
        self.lock = None

        self.status = None  # Ready to move or not

        # Motor's physical position and the length reported by the controller
        self.direction = direction
        self.PID = [kP, kI, kD]

        self.position = position
        self.pulses_per_inches = pulses_per_revolution / \
            (np.pi * spool_diameter)
        self.length = 0

    def __str__(self):
        return f"Motor {self.number}"

    def __repr__(self):
        return str(self)

    def __getstate__(self):
        """Necessary to save the ".pkl" file.
        """
        self.status = None
        self.__dict__.pop('recieve_thread')
        self.__dict__.pop('sync_thread')
        self.__dict__.pop('socket')
        self.__dict__.pop('lock')

        return self.__dict__

    def __setstate__(self, state):
        """Necessary to load the ".pkl" file.
        """

        self.__dict__ = state
        self.__dict__.update(
            {"recieve_thread": None, "sync_thread": None, "socket": None, "lock": None})

    def connect(self):
        """Tries to connect to the motor unit repetedly.

        Raises:
            Exception: Raises an exception when the connection is succesfull but no response is recieved.
        """

        attempts = 0

        while self.lock:
            self.socket = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
            self.socket.settimeout(1)

            try:
                attempts += 1
                self.socket.connect(self.address)
                self.socket.settimeout(0.1)

                self.send("Yes")

                self.recieve_thread = Thread(target=self.recieve, daemon=True, name=f"{str(self)}-revcieve")
                self.recieve_thread.start()

                start_time = time()

                while self.status != "Ready" and time() - start_time < 5:
                    pass

                if self.status != "Ready":
                    raise Exception("Did not recieve!")

                break

            except Exception as error:
                self.logger.exception(error)
                self.logger.info(f"Failed setup! ({attempts} attempt(s))")

        self.logger.info(f"Connected! ({attempts} attempt(s))")

    def setup(self, mic):
        """Setup the motor object by opening a ".log" file named after the Motor object, initiating the connection (with the 'connect' function) and send the opperational parameters to the motor.

        Args:
            mic (Mic): Parent Mic object to the Motor object. This is the microphone controlled by the corresponding motor.
        """

        self.mic = mic
        self.logger = log.getLogger(str(self))
        self.logger.setLevel(log.DEBUG)

        file_handler = log.FileHandler(
            f"log/{str(self.mic).lower().replace(' ', '_')}/{str(self).lower().replace(' ', '_')}.log", mode="w")
        formatter = log.Formatter("%(asctime)s : %(message)s")

        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.status = "Setup"
        self.lock = Lock()

        self.logger.info(f"Connecting...")

        self.connect()

        self.send_parameters()

        self.sync_thread = Thread(target=self.sync, daemon=True, name=f"{str(self)}-sync")
        self.sync_thread.start()

    def reconnect(self):
        """This is called when a socket operation fails. The socket is closed, the 'connect' function is called and the operational parameters are sent to the motor.
        """
        self.logger.info("Reconnecting!")
        self.socket.close()

        self.connect()

        self.send_parameters()

    def recieve(self):
        """This repetedly tries to recieve messages from the motor unit
        """

        while self.lock:
            try:
                self.lock.acquire()
                messages = self.socket.recv(2048)
                self.lock.release()

                messages = messages.decode("ascii").splitlines()

                for message in messages:
                    self.logger.info(f"Recieved: {message}")

                    if message == "Ready" and self.status == "Moving":
                        self.logger.info("Done!")

                    self.read(message)

            except Exception as error:
                if type(error) not in [BlockingIOError, TimeoutError] and self.logger:
                    self.logger.exception(error)

                if self.lock:
                    try:
                        self.lock.release()
                    except Exception as error:
                        self.logger.exception(error)

                    sleep(0.1)
                    
                else:
                    break

    def send(self, message):
        """This is used to send a message to the motor unit.

        Args:
            message (str): Message string to be sent to the motor unit.

        Returns:
            bool: 'True' if the message was sent succesfully and 'False' otherwise.
        """
        if self.status != "Disconnected" and self.lock:
            try:
                self.lock.acquire()
                self.socket.send(bytes(f"{message}\n", "ascii"))
                self.lock.release()

            except Exception as error:
                self.logger.exception(error)
                self.status = "Disconnected"
                self.reconnect()

                return False

            self.logger.info(f"Sent: {message}")

            return True

        return False

    def read(self, message):
        """Reads the incoming message. Look at the function to understand how the messages are interpreted.

        Args:
            message (str): Message to be read and interpreted.
        """
        try:
            self.length = float(message) / self.pulses_per_inches
            self.mic.approx_position()

        except ValueError:
            if message in ["Ready", "Busy", "Moving", "Stopped", "Close"]:
                self.status = message

            else:
                pass

    def sync(self):
        """Sends a message to the motor unit every 5 seconds to check the connection.
        """
        while self.lock:
            if self.status not in ["Moving", "Close"]:
                try:
                    self.send("Sync")

                except Exception as error:
                    self.logger.exception(error)

                sleep(5)

    def send_length(self, length, speed=1.0):
        if self.send(f"S{speed}"):
            if self.send(length * self.pulses_per_inches):
                self.logger.info(f"Moving: {length - self.length} inches...")

    def get_length(self):
        self.send("P")

    def set_length(self, length):
        self.length = length

        self.send(f"E{self.length * self.pulses_per_inches}")

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
        self.direction[0] = self.direction[0]*(-1)

        self.send(f"DE{self.direction[0]}")

    def send_parameters(self):
        self.set_length(self.length)

        self.set_direction(self.direction)

        self.set_pid(self.PID)


class Mic:
    """This class is used to send and recieve messages form the motor units."""

    def __init__(self, name="blank", motors=[], position=np.array([0, 0, 0])):
        self.name = name
        self.motors = motors
        self.position = position
        self.stage = None
        self.logger = None

        self.status = ""

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def setup(self, stage):
        self.stage = stage
        self.stage.logger.info(f"{self}: {self.position} in")
        os.makedirs(
            f"{os.getcwd()}/log/{str(self).lower().replace(' ', '_')}", exist_ok=True)

    def home(self, position):
        """Adjusts the length of the motors to match a position.

        Args:
            position (ndarray): Position to adjust to.
        """
        self.position = position
        lengths = [norm(motor.position - self.position)
                   for motor in self.motors]

        for motor, length in zip(self.motors, lengths):
            motor.set_length(length)

    def broadcast(self, message):
        """Send a message to all the motors associated to this microphone.

        Args:
            message (str): Message to be broadcasted.
        """
        for motor in self.motors:
            motor.send(message)

    # [TODO] Check for colision and reachability (vector intersection)
    def move(self, position):
        """Sends the right length and speed to the motors to move the microphone.

        Args:
            position (ndarray): Position to reach.
        """
        #self.stage.colision_detection(self, position)

        if [motor for motor in self.motors if motor.status not in ["Ready", "Close", "Moving"]] == list():
            # [TODO] Make sure it gets there before setting the value

            self.stage.logger.info(
                f"Moving {self} {position - self.position} inches")
            self.position = position

            current_lengths = np.array([motor.length for motor in self.motors])

            target_lengths = np.array(
                [norm(motor.position - self.position) for motor in self.motors])

            distances = abs(target_lengths - current_lengths)

            speeds = [distance/max(distances) if distance/max(distances) > 0.5 else 0.5 for distance in distances]

            for motor, length, speed in zip(self.motors, target_lengths, speeds):
                Thread(target=motor.send_length,
                       daemon=True, args=(length, speed)).start()
                
        else:
            self.stage.logger.info(f"Some motors are faulty! ({[(motor, motor.status) for motor in self.motors if motor.status not in ['Ready', 'Close']]})")

    def step_move(self, position):
        """Moves the microphone in 5 cm increments making sure the position is reached before the next increment.

        Args:
            position (ndarray): Position to reach.
        """

        # sends one message per centimeter travelled by the motor
        # only if all the mics are ready
        self.logger.info(f"Inching along to {position} inches...")

        start = self.position
        stop = position
        distance = stop - start

        steps = np.arange(0.0, norm(distance), 5) / norm(distance)

        if steps[-1] != 1.0:
            steps = np.append(steps, 1.0)

        for step in np.arange(0, norm(distance), 5):
            position = start + step * distance
            self.logger.info(f"{step * 100}%...")

            try:
                self.move(position=position)

                while [motor for motor in self.motors if motor.status not in ["Close", "Ready"]] != list():
                    pass

            except Exception:
                self.logger.info(f"Failed at {step * 100}%!")

    def approx_position(self):
        """Approximates the position of the microphone based on the length measured by the motors

        Returns:
            ndarray: Position approximated the position of the microphone
        """
        
        spheres = [(motor.position, motor.length) for motor in self.motors]

        def intersection(t, spheres):
            return np.array([np.sum((t-sphere[0])**2)-sphere[1]**2 for sphere in spheres])

        self.position = root(intersection, x0=self.position, args=(spheres, ), method="lm").x
        
        self.stage.logger.info(f"{self} is at {np.array2string(self.position, precision=2, floatmode='fixed')} inches")

class Stage:

    def __init__(self, mics=list(), presets=dict()):
        self.mics = mics
        self.presets = presets
        self.logger = None

        self.motor_handler = None

    def __eq__(self, other):
        if not isinstance(other, Stage):
            return False

        if dir(self) == dir(other):
            return True

        return False

    def pickle(self, file_name="stage.pkl"):
        """Saves the `Stage` object to a ".pkl" file

        Args:
            file_name (str, optional): Name of the file to be saved. Defaults to "stage.pkl".
        """

        self.logger.info(f"Saving configuration file...")

        try:
            pk.dump(self, open(f"config/{file_name}", "wb"))
            self.logger.info(f"Saved as '{file_name}'!")

        except Exception as error:
            self.logger.exception(error)
            self.logger.info(f"Could not save as '{file_name}'!")

    def setup(self, file_name="stage.pkl"):
        """Sets up the stage and all of it's components from a ".csv" or ".pkl" file

        Args:
            file_name (str, optional): Name of the file to be loaded. Defaults to "stage.pkl".

        Returns:
            Stage: Returns the loaded `Stage` object
        """

        self.logger = log.getLogger("Stage")
        self.logger.setLevel(log.DEBUG)

        file_handler = log.FileHandler(
            f"log/stage.log", mode="w")
        formatter = log.Formatter("%(asctime)s : %(message)s")

        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        if file_name[-3:] == "pkl":
            self.logger.info(f"Loading '{file_name}'...")

            try:
                self = pk.load(open(f"config/{file_name}", "rb"))

            except Exception as error:
                self.logger.exception(error)
                self.logger.info(f"Could not load '{file_name}'!")
                file_name = "motor_list.csv"

        if file_name[-3:] == "csv":
            self.logger.info(f"Loading '{file_name}'...")

            with open(f"config/{file_name}", 'r') as dest_f:
                csv_file = reader(dest_f, delimiter=",")
                next(csv_file, None)

                data = [data for data in csv_file]

            for index, (ip_address, port, motor, encoder, x, y, z, mic_name) in enumerate(data):
                if mic_name not in [mic.name for mic in self.mics]:
                    self.mics.append(Mic(name=mic_name))
                    self.mics[-1].stage = self
                    self.mics[-1].motors = list()

                motor = Motor(number=index + 1, ip_address=ip_address, port=int(port), direction=[
                              int(motor), int(encoder)], position=np.array([float(x), float(y), float(z)]))

                mic = next((mic for mic in self.mics if mic.name == mic_name))
                mic.motors.append(motor)

        self.logger.info(f"Presets: {self.presets}")

        for mic in self.mics:
            mic.setup(self)

            for motor in mic.motors:
                Thread(target=motor.setup, args=(mic, ),daemon=True, name=f"{str(motor)}-setup").start()

        return self

    def recall_preset(self, preset):
        """Recalls a preset list of positions for all the microphones

        Args:
            preset (list(np.array)): List of position of all the microphones
        """

        for mic, position in zip(self.mics, preset):
            Thread(target=mic.move, daemon=True, args=(position, )).start()

        self.logger.info(f"Recalled preset! {preset}")

    def save_preset(self, name):
        """Saves the current position of the microphones as a new preset

        Args:
            name (str): Name of the new preset
        """

        self.presets[name] = [mic.position for mic in self.mics]
        self.logger.info(f"Saved preset! {self.presets[name]}")

    def colision_detection(self, moving_mic, final_position):
        """(Experimental) 
        Checks to see if a colision will occur when moving a microphone.

        Args:
            moving_mic (Mic): Microphone that will be moving
            final_position (ndarray): The position that the moving microphone is trying to reach

        Returns:
            bool: `True` if there's no colision and `False` otherwise. 
        """

        other_mics = [mic for mic in self.mics if mic != moving_mic]

        segments = [(motor.position, mic.position - motor.position)
                    for mic in other_mics for motor in mic.motors]
        planes = [(motor.position, np.cross(moving_mic.position - motor.position,
                   final_position - motor.position)) for motor in moving_mic.motors]

        def intersection(t, plane, segment):
            # n*(r-b)=0

            r = t * segment[1] + segment[0]
            n = plane[1]
            b = plane[0]

            return n*(r-b)

        for plane in planes:
            for segment in segments:
                try:
                    ans = root(intersection, x0=0, args=(plane, segment))
                    self.logger.info(ans)

                    if 0 <= ans <= 1:
                        return False

                except Exception as error:
                    self.logger.exception(error)

        return True
