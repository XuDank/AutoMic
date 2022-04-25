from gui import *

if __name__ == "__main__":
    app = GUI()

    for mic in app.stage.mics:
            for motor in mic.motors:
                    if motor.address[0] == "127.0.0.1":
                        Genuino(address=motor.address)

    app.run()