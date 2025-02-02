from tkinter import *
import subprocess
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import os
import re


class Root:
    def __init__(
        self,
        width,
        height,
        plot_settings,
        title="GUI_atompaw",
        resizable=(False, False),
        icon=None,
    ):
        self.root = Tk()
        self.root.configure(background=self.rgb((46, 52, 64)))
        self.root.title(title)
        self.root.geometry(f"{width}x{height}+10+10")
        self.root.resizable(resizable[0], resizable[1])
        if icon:
            self.root.iconphoto(False, PhotoImage(file="icon.png"))

        self.plot_settings = plot_settings
        self.show_plot_canvas()

    def show_plot_canvas(self):
        # костыль!
        plot_frame_new = LabelFrame(self.root, text="plots")
        x = 30 + 550 + 10 + 550 + 10
        y = 10
        plot_frame_new.place(
            x=x,
            y=y,
            width=self.plot_settings["width"],
            height=self.plot_settings["height"] + 80,
        )
        canvas = Canvas(
            plot_frame_new,
            bg="#FFFFFF",
            width=self.plot_settings["width"],
            height=self.plot_settings["height"],
            highlightthickness=0,
        )
        canvas.pack(side=LEFT, expand=True, fill=BOTH)

    def create_buttons(self):
        frame = LabelFrame(
            self.root,
        )
        frame.place(
            x=30 + 550 + 10,
            y=19,
            width=550,
            height=70,
        )
        bg = self.rgb((217, 217, 217))
        fg = "black"
        Button(
            frame,
            text="load (C-l)",
            bg=bg,
            fg=fg,
            width=7,
            height=1,
            command=self.load_input_file,
        ).place(x=2, y=2)
        Button(
            frame,
            text="save (C-s)",
            bg=bg,
            fg=fg,
            width=7,
            height=1,
            command=self.save_input_file,
        ).place(x=90, y=2)
        Button(
            frame,
            text="run (C-r)",
            bg=bg,
            fg=fg,
            width=7,
            height=1,
            command=self.run_atompaw,
        ).place(x=2, y=35)
        Button(
            frame,
            text="plot (C-p)",
            bg=bg,
            fg=fg,
            width=7,
            height=1,
            command=self.plot,
        ).place(x=90, y=35)
        Button(
            frame,
            text="run and plot (F9)",
            bg=bg,
            fg=fg,
            width=12,
            height=1,
            command=self.run_and_plot,
        ).place(x=178, y=35)

        # self.root.bind("<Control-l>", self.load_input_file)
        # self.root.bind("<Control-s>", self.save_input_file)
        # self.root.bind("<Control-r>", self.run_atompaw)
        # self.root.bind("<Control-c>", self.stop_atompaw)
        # self.root.bind("<Control-p>", self.plot)
        # self.root.bind("<F9>", self.run_and_plot)

    def create_input_atompaw_area(self, settings):
        self.input_atompaw = self.create_text_area(
            settings["x"], settings["y"], settings, settings["title"]
        )

    def create_output_atompaw_area(self, settings):
        self.output_atompaw = self.create_text_area(
            settings["x"], settings["y"], settings, settings["title"]
        )

    def plot(self, event=None):
        """
        Plot PS and AE partial waves and projectors
        And plot log derivatives
        """

        # array of active l. For example if lmax=1, then l_arr=[0,1]
        l_arr = []
        l_arr = re.findall(
            r"For l =\s+(.+)\s+\d\s+basis functions\s+",
            self.output_atompaw.get("1.0", END),
        )
        l_arr = list(map(int, l_arr))

        # array of number of partial waves per l
        # For example if lmax=1 (l_arr=[0,1]) and there are 1 partial
        # waves per l=0 and 2 partial wave per l=1, then pw_per_l=[1,2]
        pw_per_l = []
        pw_per_l = re.findall(
            r"For l =\s+\d\s+(.+)\s+basis functions\s+",
            self.output_atompaw.get("1.0", END),
        )
        pw_per_l = np.array(list(map(int, pw_per_l)))

        number_of_l = len(l_arr)
        max_number_pw_per_l = np.max(pw_per_l)

        path_dir = self.entry_output_file_path.get()

        fig = Figure(
            figsize=(2.8 * number_of_l, 2.2 * (max_number_pw_per_l)),
            layout="constrained",
        )
        ax = fig.subplots(max_number_pw_per_l + 1, number_of_l)
        li = [0] * (number_of_l)

        for i in range(number_of_l + 1 + max_number_pw_per_l):
            radius, AEpw, PSpw, projector = [np.array([])] * 4
            file_path = f"{path_dir}/wfn{i+1}"
            with open(file_path, "r") as file:
                radius, AEpw, PSpw, projector = [np.array([])] * 4
                preamble = file.readline()
                preamble = re.split(r"\s+", preamble)
                l = int(preamble[3])
                E = float(preamble[-2])
                for line in file:
                    radius = np.append(radius, float(line.split()[0]))
                    AEpw = np.append(AEpw, float(line.split()[1]))
                    PSpw = np.append(PSpw, float(line.split()[2]))
                    projector = np.append(projector, float(line.split()[3]))

                ax[li[l], l].plot(radius, AEpw, color="black", label="AE")
                ax[li[l], l].plot(radius, PSpw, color="red", label="PS")
                ax[li[l], l].plot(radius, projector, color="green", label="Proj")
                ax[li[l], l].set(
                    xlabel="radius [a.u.]",
                    ylabel="amplitude",
                    title=f"l={l}, E={E:.2f} Ry",
                )
                ax[li[l], l].grid()
                # if li[l] == 0 and l == 0:
                # ax[li[l], l].legend(loc="upper right")
                li[l] += 1

        for i in range(number_of_l):
            energy, AElogderiv, PSlogderiv = [np.array([])] * 3
            file_path = f"{path_dir}/logderiv.{i}"
            with open(file_path, "r") as file:
                for line in file:
                    energy = np.append(energy, float(line.split()[0]))
                    AElogderiv = np.append(AElogderiv, float(line.split()[1]))
                    PSlogderiv = np.append(PSlogderiv, float(line.split()[2]))

            ax[-1, i].plot(energy, AElogderiv, color="black", label="Exact")
            ax[-1, i].plot(energy, PSlogderiv, color="red", label="PAW", linestyle="--")
            ax[-1, i].set(
                xlabel="energy [Ry]",
                ylabel="log derivative",
                title=f"logderiv.{i}" + f"   l={i}",
                ylim=([-500, 500]),
            )
            ax[-1, i].grid()
            # ax[li[-1], i].legend()

        fig.savefig(self.entry_output_file_path.get() + "/plots.png")

        plot_frame = LabelFrame(self.root, text="plots")
        x = 30 + 550 + 10 + 550 + 10
        y = 10

        plot_frame.place(
            x=x,
            y=y,
            width=self.plot_settings["width"],
            height=self.plot_settings["height"] + 80,
        )
        canvas = FigureCanvasTkAgg(
            fig,
            master=plot_frame,
        )
        canvas = Canvas(
            plot_frame,
            bg="#FFFFFF",
            width=self.plot_settings["width"],
            height=self.plot_settings["height"],
            highlightthickness=0,
        )
        vbar = Scrollbar(plot_frame, orient=VERTICAL, command=canvas.yview)
        vbar.pack(side=RIGHT, fill=Y)
        canvas.config(yscrollcommand=vbar.set)
        canvas.pack(side=LEFT, expand=True, fill=BOTH)
        middle = Frame(canvas, bg="yellow")
        canvas.create_window(0, 0, window=middle, anchor="nw")
        canvas_1 = FigureCanvasTkAgg(fig, middle)
        canvas_1.get_tk_widget().pack(expand=True, fill=BOTH)
        canvas_1.draw()
        middle.bind(
            "<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all"))
        )
        self.input_atompaw.focus_force()

    # def stop_atompaw(self, event=None):
    #     self.output_atompaw.run_command("^C")

    def run_and_plot(self, event=None):
        self.run_atompaw()
        self.plot()

    def make_key_bindings(self):
        self.root.bind("<Control-l>", self.load_input_file)
        self.root.bind("<Control-s>", self.save_input_file)
        self.root.bind("<Control-r>", self.run_atompaw)
        # self.root.bind("<Control-c>", self.stop_atompaw)
        self.root.bind("<Control-p>", self.plot)
        self.root.bind("<F9>", self.run_and_plot)

    def load_input_file(self, event=None):
        file_path = self.entry_input_file_path.get()
        if file_path:
            self.input_atompaw.delete("1.0", END)
            with open(file_path, "r") as f:
                self.input_atompaw.insert("1.0", f.read())

    def save_input_file(self, event=None):
        file_path = self.entry_input_file_path.get()
        with open(file_path, "w") as f:
            text = self.input_atompaw.get("1.0", END)
            f.write(text)

    def create_input_path_entry(self):
        input_path_label = Label(self.root, text="input file:")
        input_path_label.place(x=30, y=20, width=100, height=30)
        self.entry_input_file_path = Entry(
            bd=0, bg="#D9D9D9", fg="#000716", highlightthickness=0
        )
        self.entry_input_file_path.place(x=140, y=20, width=440, height=30)
        self.entry_input_file_path.insert(
            END,
            "enter the absolute path to the atompaw.input file",
        )

    def create_output_path_entry(self):
        output_path_label = Label(self.root, text="out dir:")
        output_path_label.place(x=30, y=60, width=100, height=30)
        self.entry_output_file_path = Entry(
            bd=0, bg="#D9D9D9", fg="#000716", highlightthickness=0
        )
        self.entry_output_file_path.place(x=140, y=60, width=440, height=30)
        self.entry_output_file_path.insert(
            END, "enter the path to the output directory"
        )

    def run(self):
        self.root.mainloop()

    def rgb(self, rgb):
        return "#%02x%02x%02x" % rgb

    def create_entry(self, x, y, entry_settings, title):
        frame = LabelFrame(self.root, text=title)
        entry = Entry(
            frame,
            bd=entry_settings["bd"],
            bg=entry_settings["bg"],
            fg=entry_settings["fg"],
            highlightthickness=0,
        )
        frame.place(
            x=x,
            y=y,
            width=entry_settings["width"],
            height=entry_settings["height"],
        )
        entry.pack(fill=BOTH)
        return entry

    def create_text_area(self, x, y, text_area_settings, title):
        frame = LabelFrame(self.root, text=title)
        text_area = Text(
            frame,
            bd=0,
            bg=text_area_settings["bg"],
            fg=text_area_settings["fg"],
            highlightthickness=0,
            font=text_area_settings["font"],
            padx=10,
            pady=10,
            wrap=NONE,
            relief=FLAT,
            width=text_area_settings["width"],
            height=text_area_settings["height"],
            insertbackground=text_area_settings["insertbackground"],
            selectbackground=text_area_settings["selectbackground"],
        )
        frame.place(
            x=x,
            y=y,
            width=text_area_settings["width"],
            height=text_area_settings["height"],
        )
        text_area.pack()
        return text_area

    # def create_terminal(self, x, y, text_area_settings, title):
    #     frame = LabelFrame(self.root, text=title)
    #     frame.place(
    #         x=x,
    #         y=y,
    #         width=text_area_settings["width"],
    #         height=text_area_settings["height"],
    #     )
    #     terminal = Terminal(frame, pady=5, padx=5)
    #     terminal.shell = True
    #     terminal.linebar = True
    #     terminal.pack(expand=True, fill="both")
    #     return terminal

    def clean_atompaw(self):
        self.output_atompaw.delete("1.0", END)

    def run_atompaw(self, event=None):
        self.save_input_file()
        self.clean_atompaw()
        file_path = self.entry_input_file_path.get()

        with open("paths.txt", "r") as f:
            atompaw_root = f.readline().split(":")[1]

        v_complete = f"{atompaw_root[:-1]} < {file_path}"

        if not os.path.exists(self.entry_output_file_path.get()):
            os.makedirs(self.entry_output_file_path.get())

        def ls_proc():
            return subprocess.Popen(
                v_complete,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                cwd=self.entry_output_file_path.get(),
            )

        with ls_proc() as p:
            if p.stdout:
                for line in p.stdout:
                    self.output_atompaw.insert(END, line)
            if p.stderr:
                for line in p.stderr:
                    self.output_atompaw.insert(END, line)

        self.output_atompaw.see(END)
        self.input_atompaw.focus_force()


if __name__ == "__main__":

    def rgb(rgb):
        return "#%02x%02x%02x" % rgb

    atompaw_input_settings = {
        "x": 30,
        "y": 100,
        "width": 550,
        "height": 830,
        "title": "Atompaw input",
        "bg": rgb((42, 42, 42)),
        "fg": "white",
        "insertbackground": rgb((234, 234, 234)),
        "selectbackground": "#8D917A",
        "font": "Consolas 12",
    }

    atompaw_output_settings = {
        "x": 30 + 550 + 10,
        "y": 100,
        "width": 550,
        "height": 830,
        "title": "Atompaw output",
        "bg": rgb((42, 42, 42)),
        "fg": "white",
        "insertbackground": rgb((234, 234, 234)),
        "selectbackground": "#8D917A",
        "font": "Consolas 12",
    }
    entry_settings = {
        "bd": 0,
        "bg": "#D9D9D9",
        "fg": "#000716",
        "width": 550,
        "height": 30,
    }
    plot_settings = {
        "width": 650,
        "height": 840,
    }

    root = Root(1800, 950, plot_settings)
    root.create_input_atompaw_area(atompaw_input_settings)
    root.create_output_atompaw_area(atompaw_output_settings)
    root.create_input_path_entry()
    root.create_output_path_entry()
    root.create_buttons()
    # root.load_input_file()
    root.make_key_bindings()
    root.run()
