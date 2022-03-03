# -*- coding: utf-8 -*-
"""
Created on Wed Jan 12 22:13:18 2022

@author: sebas
"""
# GUI for project

from http import server
import string
import tkinter as tk
from tkinter import *
import numpy as np
from automic import *
#import pythonserver 
#sys.path.append(".")

Pos = {}

motors = [Motor(id = 4, ip_address= "192.168.1.4", port = 5000, encoder_direction= -1)]
mics = [Mic(name = "Mic 1", motors= [motors[0]]), Mic(name = "Mic 2", motors= [])]
stage = Stage(mics = mics)

stage.setup()

selected_mic = mics[0]



def select_mic(mic):
    global selected_mic
    selected_mic = mic
    print(mic)

def setPosition(event = None):
    global posXEntry
    global posYEntry
    global posZEntry
    PositionX = float(posXEntry.get())
    PositionY = float(posYEntry.get())
    PositionZ = float(posZEntry.get())
    global mics
    #position_input()
    #func = operate(menu.get(3, "Invalid argument"))
    posXEntry.delete(0,END)
    posYEntry.delete(0,END)
    posZEntry.delete(0,END)
    #print 
    position = np.array([PositionX,PositionY,PositionZ])
    selected_mic.move(position)
    return PositionX, PositionY

def homePosition(event = None):
    global PositionX
    global PositionY
    global PositionZ
    global mics
    PositionX = 0.0
    PositionY = 0.0
    PositionZ = 0.0
    position = np.array([PositionX,PositionY,PositionZ])
    selected_mic.move(position)

def savePosition(event = None):
    global i
    #stage.presets[f"Position {i}"] = None
    stage.save_preset(f"Position {i}")
    PosButton = tk.Button(m,text = "Position" + str(i), command=stage.recall_preset(f"Position {i}",stage.presets[f"Position {i}"]), width = 20)
    PosButton.grid(row = i+8, column= 2)
    
    
    i = i+1
    #PosButton.bind('<Button>', stage.recall_preset(stage.presets[f"Position {i}"]))

def insertPosition(event = None):
    global Pos
    global PosX, PosY
    global posXEntry, posYEntry
    #print(PosX, PosY)
    posXEntry.insert(0,str(Pos[i][0]))
    posYEntry.insert(0,str(Pos[i][1]))

#def exitGUI(event = None):

    
if __name__ == "__main__":
    i = 0
    m = Tk()
    m.title("Interface")
    m.minsize(width = 600, height = 600)
    
    Interface = Frame(m)
            
    Interface.grid()
    
    #selectMic = tk.Button(m, text = 'select Motor', width = 20)
    #selectMic.bind('<Button>', )
    #selectMic.pack()

    

    mic_buttons = [(tk.Button(m, text = mic.name , width = 20, command= lambda mic = mic: select_mic(mic)), mic )for mic in mics]
    j = 2
    for button, mic in mic_buttons:
        button.bind('<Button>', select_mic(mic))
        
        button.grid(row=j,column=1)
        j = j+1

    posX = tk.StringVar()
    posXLabel = tk.Label(m, text = 'Enter x direction', font=('calibre',10, 'bold'))
    posXLabel.grid(row=1, column=3)
    posXEntry = tk.Entry(m, width = 10, textvariable = posX)
    posXEntry.grid(row=2, column=3)
    
    posY = tk.StringVar()
    posYLabel = tk.Label(m, text = 'Enter y direction', font=('calibre',10, 'bold'))
    posYLabel.grid(row=3, column=3)
    posYEntry = tk.Entry(m, width = 10, textvariable = posY)
    posYEntry.grid(row=4, column=3)  

    posZ = tk.StringVar()
    posZLabel = tk.Label(m, text = 'Enter z direction', font=('calibre',10, 'bold'))
    posZLabel.grid(row=5, column=3)
    posZEntry = tk.Entry(m, width = 10, textvariable = posZ)
    posZEntry.grid(row=6, column=3) 

    setSaveButton = tk.Button(m, text = 'save Position', width = 20)
    if setSaveButton.bind('<Button>', savePosition):
        i = i + 1
    setSaveButton.grid(row = 8, column=4)
       
    
    moveButton = tk.Button(m, text = 'move',width = 20)
    moveButton.bind('<Button>', setPosition)
    moveButton.grid(row=7, column=2)
    
    homeButton = tk.Button(m, text= 'home', width = 20)
    homeButton.bind('<Button>', homePosition)
    homeButton.grid(row=7, column=3)

    exitButton = tk.Button(m, text='exit', command=m.destroy, width = 20)
    exitButton.bind('<Button>')
    exitButton.grid(row=7,column = 4)

    calibrateButton = tk.Button(m, text='calibrate', width = 20)
    calibrateButton.bind('<Button>')
    calibrateButton.grid(row=8,column=2)

    editButton = tk.Button(m, text='edit', width = 20)
    editButton.bind('<Button>')
    editButton.grid(row=8,column=3)

    m.mainloop()