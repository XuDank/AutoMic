import os
import socket as skt
import logging as log
from threading import Thread, Lock
from time import sleep

import numpy as np

os.makedirs(f"{os.getcwd()}/log/genuino", exist_ok=True)


class Genuino:
    def __init__(self, address=("0.0.0.0", 5000)) -> None:
        self.logger = log.getLogger(f"genuino{address[1]}")
        self.logger.setLevel(log.DEBUG)

        file_handler = log.FileHandler(
            f"log/genuino/{address[1]}.log", mode="w")
        formatter = log.Formatter("%(asctime)s : %(message)s")

        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.address = ("0.0.0.0", address[1])
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_STREAM)

        self.lock = Lock()
        self.status = "Ready"

        self.count = 0
        self.target = 0

        self.setup()

    def setup(self):
        self.socket.bind(self.address)
        self.socket.listen()

        self.thread = Thread(target=self.loop, daemon=True)
        self.thread.start()

    def loop(self):
        while True:
            self.client, address = self.socket.accept()

            self.logger.info(f"Connected to: {address[0]}, {address[1]}")
            self.send("Ready")
            
            while True:
                try:
                    self.lock.acquire()
                    messages = self.client.recv(2048)
                    self.lock.release()

                    messages = messages.decode("ascii").splitlines()

                    for message in messages:
                        self.logger.info(f"Recieved: {message}")
                        self.read(message)

                except BlockingIOError:
                    self.lock.release()
                    sleep(0.001)

    def send(self, message):
        try:
            self.lock.acquire()
            self.client.send(f"{message}\n".encode("utf-8"))
            self.lock.release()

            self.logger.info(f"Sent: {message}")

        except Exception as error:
            self.logger.exception(error)

    def read(self, message):
        try:
            target = float(message)

            self.send("Moving")

            for count in np.linspace(self.count, target, 10):
                self.send(count)
                sleep(0.25)

            self.count = target
            self.send(self.count)
            self.send("Ready")

        except ValueError:
            if message == "Sync":
                self.send("Ready")

            elif message == "P":
                self.send(self.count)

            elif message[0] == "E":
                self.count = float(message[1:-1])
