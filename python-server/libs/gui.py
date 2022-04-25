from tkinter import *
from tkinter import font
from tkinter.font import Font
from tkinter.ttk import Separator

from automic import *
from genuino import *

import matplotlib.pyplot as pl
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure

class GUI:
    def __init__(self):
        self.root = Tk()
        self.main_frame = Frame()
        self.hilight_font = Font(size=10, weight="bold")

        self.display_frame = LabelFrame(self.main_frame)
        self.preset_list_frame = Frame(self.display_frame)
        self.motion_frame = LabelFrame(self.main_frame)

        self.stage = Stage()

        self.mic = Mic()
        self.step_size = DoubleVar(value=12.0)
        self.motor = Motor()

        self.preset = list()

        self.preset_list = list()
        self.mic_list = list()

    def setup(self, file_name="stage.pkl"):
        self.stage = self.stage.setup(file_name)

        self.mic = self.stage.mics[0]
        self.motor = self.mic.motors[0]

        self.root.configure(width=1200, height=800)

        def on_exit():
            self.stage.pickle()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_exit)

        self.main_frame.grid()

        self.display_frame.configure(borderwidth=5, text="Display")
        self.display_frame.grid(row=0, column=0)

        self.motion_frame.configure(borderwidth=5, text="Motion Frame")
        self.motion_frame.grid(row=0, column=1, sticky=(N, S))

        self.preset_selection()
        self.preset_controls()

        self.mic_seletion()
        self.mic_controls()

        self.motion_controls()

    def run(self):
        self.main_frame.mainloop()

    def mic_controls(self):
        Label(self.display_frame, text="Microphone controls",
              font=self.hilight_font).pack()

        mic_controls_frame = Frame(self.display_frame)
        mic_controls_frame.pack()

        Button(mic_controls_frame, text="Calibrate",
               command=self.calibration_popup).grid(row=1, column=0)
        Button(mic_controls_frame, text="Home",
               command=self.home_popup).grid(row=1, column=1)

        Button(mic_controls_frame, text="Motor controls",
               command=self.motor_control_popup).grid(row=2, column=0)
        
        def visu_popup():
            popup = Toplevel(self.root)
            fig = pl.figure(figsize=(4,4), dpi=100)
            ax = fig.add_subplot(111, projection='3d')

            for mic in self.stage.mics:
            
                x, y, z = (coordinate for coordinate in mic.position)
                ax.scatter(x,y,z)
        
            canvas = FigureCanvasTkAgg(fig, popup)
            canvas.draw()
            canvas.get_tk_widget().grid(row=1,column=0)
            toolbar = NavigationToolbar2Tk(canvas, popup)
            toolbar.update()
            canvas._tkcanvas.grid(row=0,column=0)
            Label(popup, text="Visualization").grid(row=0, column=0)
        Button(mic_controls_frame, text="Visualization", command=visu_popup).grid(row=2, column=1) 


    def mic_seletion(self):
        Label(self.display_frame, text="Select a microphone:",
              font=self.hilight_font).pack()

        mic_list_frame = Frame(self.display_frame)
        mic_list_frame.pack()

        def select_mic(mic):
            self.mic = mic

        mic_index = IntVar()

        mic_buttons = [Radiobutton(mic_list_frame, text=mic.name, command=lambda mic=mic: select_mic(
            mic), variable=mic_index, value=index) for index, mic in enumerate(self.stage.mics)]

        for index, mic_button in enumerate(mic_buttons):
            mic_button.grid(row=index//3 + 1, column=index % 3)

        mic_index.set(0)

    def motor_selection(self):
        Label(self.display_frame, text="Motor list").pack()

        motor_list_frame = Frame(self.display_frame)
        motor_list_frame.pack()

        def select_motor(motor):
            self.motor = motor

        motor_index = IntVar()

        motor_buttons = [Radiobutton(motor_list_frame, text=str(motor), command=lambda motor=motor: select_motor(
            motor), variable=motor_index, value=index) for index, motor in enumerate(self.mic.motors)]

        for index, motor_button in enumerate(motor_buttons):
            motor_button.grid(row=index//3 + 1, column=index % 3)

    def motor_info(self):
        motor_display_frame = Frame(self.display_frame)
        motor_display_frame.pack()

        Label(self.display_frame, text="Motor info").pack()

    def motion_controls(self):
        def move(position):
            self.mic.move(self.mic.position + position*self.step_size.get())

        Button(self.motion_frame, text="Down", command=lambda position=np.array(
            [0, 0, -1]): move(position)).grid(row=0, column=0)
        Button(self.motion_frame, text="Up", command=lambda position=np.array(
            [0, 0, 1]): move(position)).grid(row=0, column=2)

        Button(self.motion_frame, text="Forward", command=lambda position=np.array(
            [0, 1, 0]): move(position)).grid(row=0, column=1)
        Button(self.motion_frame, text="Backwards", command=lambda position=np.array(
            [0, -1, 0]): move(position)).grid(row=1, column=1)

        Button(self.motion_frame, text="Right", command=lambda position=np.array(
            [1, 0, 0]): move(position)).grid(row=1, column=2)
        Button(self.motion_frame, text="Left", command=lambda position=np.array(
            [-1, 0, 0]): move(position)).grid(row=1, column=0)

        Button(self.motion_frame, text="Stop", command=lambda self=self: self.mic.broadcast(
            "Stop")).grid(row=2, column=1)

        Label(self.motion_frame, text="Step size (in inches)",
              font=self.hilight_font).grid(row=3, columnspan=3)

        Scale(self.motion_frame, from_=1.0, to=24.0, variable=self.step_size,
              orient=HORIZONTAL).grid(row=4, columnspan=3)

    def preset_controls(self):
        Label(self.display_frame, text="Preset controls",
              font=self.hilight_font).pack()

        preset_controls_frame = Frame(self.display_frame)
        preset_controls_frame.pack()

        save_button = Button(preset_controls_frame,
                             text="Save", command=self.save_popup)
        save_button.grid(row=0, column=0)

        def recall():
            self.stage.recall_preset(self.preset)

        recall_button = Button(preset_controls_frame,
                               text="Recall", command=recall)
        recall_button.grid(row=0, column=1)

    def preset_selection(self):
        Label(self.display_frame, text="Select a preset",
              font=self.hilight_font).pack()

        self.preset_list_frame.pack()

        def select_preset(preset_name):
            self.preset = self.stage.presets[preset_name]

        for index, preset_name in enumerate(self.stage.presets):
            Radiobutton(self.preset_list_frame, text=preset_name,
                        command=lambda preset_name=preset_name: select_preset(preset_name), value=index).pack()

    def calibration_popup(self):
        initial_position_input = list()
        final_position_input = list()

        initial_position = list()
        final_position = list()

        initial_lengths = list()

        popup = Toplevel(self.root)

        calibration_popup_frame = Frame(popup)
        calibration_popup_frame.pack()

        Label(calibration_popup_frame, text="Initial Position",
              font=self.hilight_font).pack()

        initial_input_frame = Frame(calibration_popup_frame)
        initial_input_frame.pack()

        for index, axis in enumerate(["x: ", "y: ", "z: "]):
            initial_position_input.append(DoubleVar(value=0.0))
            Label(initial_input_frame, text=axis).grid(row=0, column=index * 3)
            Entry(initial_input_frame, width=5, textvariable=initial_position_input[-1]).grid(row=0, column=index * 3 + 1)
            Label(initial_input_frame, text="in").grid(
                row=0, column=index * 3 + 2)            

        def record_initial():
            initial_position = np.array([coordinate.get() for coordinate in initial_position_input])
            self.mic.home(np.array([coordinate.get() for coordinate in initial_position_input]))
            initial_lengths = [motor.length for motor in self.mic.motors]

        Button(calibration_popup_frame, text="Record",
               command=record_initial).pack()

        Label(calibration_popup_frame, text="Final Position",
              font=self.hilight_font).pack()

        final_input_frame = Frame(calibration_popup_frame)
        final_input_frame.pack()

        for index, axis in enumerate(["x: ", "y: ", "z: "]):
            final_position_input.append(DoubleVar(value=0.0))
            Label(final_input_frame, text=axis).grid(row=0, column=index * 3)
            Entry(final_input_frame, width=5, textvariable=final_position_input[-1]).grid(row=0, column=index * 3 + 1)
            Label(final_input_frame, text="in").grid(
                row=0, column=index * 3 + 2)  

        def record_final():
            final_position = np.array([coordinate.get() for coordinate in final_position_input])

            final_lengths = [motor.length for motor in self.mic.motors]

            theoretical_distances = np.array(
                [norm(final_position - motor.position) - initial_length for motor, initial_length in zip(self.mic.motors, initial_lengths)])
            actual_distances = np.array(
                [motor.length - initial_length for motor, initial_length in zip(self.mic.motors, initial_lengths)])

            fudge_factors = actual_distances / theoretical_distances

            for motor, fudge_factor in zip(self.mic.motors, fudge_factors):
                motor.pulses_per_inches *= fudge_factor

            self.mic.home(final_position)

            popup.destroy()

        Button(popup, text="Record", command=record_final).pack()

    def home_popup(self):
        popup = Toplevel(self.root)

        Label(popup, text="Enter the coordinates:",
              font=self.hilight_font).pack()

        home_frame = Frame(popup)
        home_frame.pack()

        coordinates = list()

        for index, axis in enumerate(["x: ", "y: ", "z: "]):
            coordinates.append(DoubleVar())

            Label(home_frame, text=axis).grid(row=1, column=index * 3)
            Entry(home_frame,  width=5,
                  textvariable=coordinates[-1]).grid(row=1, column=index * 3 + 1)
            Label(home_frame, text="in").grid(row=1, column=index * 3 + 2)

        def home():
            self.mic.home(np.array([coordinate.get()
                          for coordinate in coordinates]))

        Button(popup, text="Home", command=home).pack()

    def motor_control_popup(self):
        popup = Toplevel(self.root)

        Label(popup, text="Select a motor:", font=self.hilight_font).pack()

        motor_selection = Frame(popup)
        motor_selection.pack()

        motor_index = IntVar()

        def select_motor(motor):
            self.motor = motor

        for index, motor in enumerate(self.mic.motors):
            Radiobutton(motor_selection, text=str(motor), variable=motor_index, value=index,
                        command=lambda motor=motor: select_motor(motor)).grid(row=1, column=index)

        Label(popup, text="Motor controls:", font=self.hilight_font).pack()

        motor_controls = Frame(popup)
        motor_controls.pack()

        Label(motor_controls, text="Length: ").grid(row=0, column=0)
        amount = DoubleVar(value=0.0)
        Entry(motor_controls,  width=5,
                  textvariable=amount).grid(row=0, column=1)
        Label(motor_controls, text="in").grid(row=0, column=2)

        Button(popup, text="Go!", command=lambda amount=amount: self.motor.send_length(
            self.motor.length + float(amount.get()))).pack()

    def save_popup(self):
        popup = Toplevel(self.root)

        name = StringVar()

        def save():
            preset_name = name.get()
            self.stage.save_preset(preset_name)

            def select_preset(preset_name):
                self.preset = self.stage.presets[preset_name]

            length = len(self.stage.presets) - 1

            new_preset_button = Radiobutton(self.preset_list_frame, text=name.get(
            ), command=lambda preset_name=preset_name: select_preset(preset_name), value=len(self.stage.presets)+1)
            new_preset_button.grid(row=length//3, column=length % 3)

            popup.destroy()

        Label(popup, text="Save as:", font=self.hilight_font).pack()
        Entry(popup, textvariable=name).pack()
        Button(popup, text="Save", command=save).pack()
