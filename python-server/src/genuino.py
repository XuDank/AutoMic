import os
import socket as skt
import logging as log
from threading import Thread

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
        self.connected = False
        self.state = True

        self.count = 0
        self.target = 0

        self.setup()

    def setup(self):
        self.socket.bind(self.address)
        self.socket.listen()

        self.thread = Thread(target=self.loop, daemon=True)
        self.thread.start()

        return self

    def loop(self):
        while True:
            self.client, address = self.socket.accept()

            self.logger.info(f"Connected to: {address[0]}, {address[1]}")

            while True:
                try:
                    messages = self.client.recv(2048)

                    if not messages:
                        break

                    messages = messages.decode("utf-8").splitlines()

                    for message in messages:
                        self.logger.info(f"Recieved: {message}")
                        self.read(message)

                except Exception as error:
                    self.logger.exception(error)

            self.client.close()

            self.logger.info(
                f"Client disconected from: {address[0]}, {address[1]}")

    def send(self, message):
        try:
            self.client.send(str(message).encode("utf-8"))

            self.logger.info(f"Sent: {message}")

        except Exception as error:
            self.logger.exception(error)

    def read(self, message):
        try:
            self.count = float(message)
            self.state = False

        except ValueError:
            if message == "Sync":
                self.send(self.count)

                if self.state:
                    self.send("Ready")

                else:
                    self.send("Busy")
                    self.state = True

            elif message == "P":
                self.send(self.count)

            elif message[0] == "E":
                self.count = float(message[1:-1])
