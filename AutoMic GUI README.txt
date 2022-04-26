****Automated Microphone GUI Instructions****

Read this document to learn how to use the GUI for the automated microphone project


***To start GUI run test:***

Automic->python-server->testing->test_app.py

Once GUI opens in pop up window perform calibration


***Calibration Process***

To calibrate Microphone:

1. Select microphone for calibration
2. Push "Calibrate" button
3. Type in the inital x,y,z coordinates for the microphone into the respective "Initial Position" windows
4. Hit the "Record" button underneath the newly entered coordinates
5. While keeping the position recording window open, push the "Motor controls" button in the main GUI window
6. Choose another position to move the microphone within its area of operation
7. Use the newly opend motor control window to move the microphone to this new position by adjusting each individual motor
8. Once the microphone is in the desired location, go back to the calibration window
9. Measure the microphones new coordinates and enter them into the respective "Final position" window
10. Hit the record button underneath
11. The system is now calibrated


***Moving a Microphone***

Calibrate system before attempting this. Only start this process if the system was calibrated and shutdown properly beforehand.

1. Select the desired microphone to move
2. Use the "Step size" slider to adjust to the desired moving interval
3. Use the motion buttons in the main GUI to move the microphone to the desired location


***Saving a Preset***

Follow the steps in the "Moving a Microphone" section before this

1. Once the microphone(s) are in the desired location, press the "Save" button underneath and name the preset
2. To move the microphone to a desired preset, select the desired preset from the available presets
3. Press the "Recall" button
4. To home the microphone, press the "Home" button