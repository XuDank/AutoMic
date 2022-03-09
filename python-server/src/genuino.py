import os
import numpy as np
import socket as skt
import logging as log

from threading import Thread
from time import sleep
from time import time

os.makedirs(f"{os.getcwd()}/log/genuino", exist_ok=True)

class Genuino:
    def __init__(self, port) -> None:
        self.logger = log.getLogger(f"genuino{port}")
        self.logger.setLevel(log.DEBUG)

        file_handler = log.FileHandler(f"log/genuino/{port}.log", mode="w")
        formatter    = log.Formatter("%(asctime)s : %(message)s")

        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.address = ("0.0.0.0", port)
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
        self.connected = False
        self.state = True

        self.count = 0
        self.target = 0

        self.setup()
    
    def setup(self):
        self.socket.bind(self.address)
        self.socket.listen()

        self.thread = Thread(target = self.loop, daemon= True)
        self.thread.start()

    def loop(self):
        while True:
            self.client, _ = self.socket.accept()
            self.client.settimeout(0.0)

            self.logger.info(f"Connected to {self.address[1]}")

            while True:
                try:
                    message = self.client.recv(2048).decode("utf-8")

                    if not message:
                        break

                    self.logger.info((f"Recieved: {message}"))
                    self.read(message)

                except:
                    pass
        
            self.client.close()

            self.logger.info(f"Client disconected ({self.address})")
                            
    def send(self, message):
        try:
            self.client.send(str(message).encode("utf-8"))

            self.logger.info(f"Sent: {message}")

        except skt.error as error:
            if self.logger is not None:
                self.logger.info(f"{error}")
            
            self.logger.info(f"{error}")

    def read(self, message):
        try:
            self.count = float(message)
            self.state = False
        
        except:
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

if __name__ == "__main__":
    pass