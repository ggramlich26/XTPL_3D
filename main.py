import pandas as pd
import csv
from typing import List
import csv_data
import dxf_data
import sdf_data
import surface
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
from tkinter.simpledialog import askfloat
from tkinter.simpledialog import askstring
from sys import exit
from tkinter import ttk
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sys
import numpy as np
import os
import subprocess
import export_xtpl
import time

axes_list = []
figure_list = []
width_list = []

coordinate_list = []

# use lists because they can mimic pointers
surface_list:List[surface.Surface] = []
dxf_list:List[dxf_data.Dxf2D] = []


def render(res: int):
    """Plots the visualization, queries for shifts until the shifts are both specified as 0, then final plot is
        created. res specifies by what factor the resolution of the ramp visualization is reduced, ramp is an object of
        the CSV_data class. ramp is an object of the CSV_data class"""

    # raises an error message and returns when the dxf object or the csv object is not initialized
    try:
        ramp: surface.Surface = surface_list[-1]
    except:
        text_widget_output('\nmissing a .csv or .sdf file', 'red')
        return
    try:
        dxf: dxf_data.Dxf2D = dxf_list[-1]
    except:
        text_widget_output('\nmissing a .dxf file', 'red')
        return

    if not hasattr(render, 'initialized'):

        # creates a messagebox that checks if the function should be executed or not, Returns True or False
        if not tk.messagebox.askyesno(title='Confirmation',
                                      message=('Plot ' + ramp.get_file_name() + ' and ' + dxf.get_dxf_name() + ' ?')):
            return

        # create figure and axis and save them in lists
        fig = Figure()
        figure_list.append(fig)
        ax = fig.add_subplot(projection='3d')
        axes_list.append(ax)

        # plots the canvas
        canvas = FigureCanvasTkAgg(fig, master=window_plt)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # plots the toolbar
        toolbar = NavigationToolbar2Tk(canvas, window_plt)
        toolbar.update()
        toolbar.pack(fill=tk.X, side=tk.BOTTOM)

        # same for the second graph that has a fixed view on the xy-plane
        # create figure_xy and axis_xy and save them in lists
        fig_xy = Figure()
        figure_list.append(fig_xy)
        ax_xy = fig_xy.add_subplot(projection='3d')
        axes_list.append(ax_xy)

        # change the view position and lock the mouse rotation
        ax_xy.view_init(azim=-90, elev=90)
        ax_xy.disable_mouse_rotation()

        # plot the canvas_xy
        canvas_xy = FigureCanvasTkAgg(fig_xy, master=window_plt_xy)
        canvas_xy.draw()
        canvas_xy.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # plot the toolbar_xy
        toolbar_xy = NavigationToolbar2Tk(canvas_xy, window_plt_xy)
        toolbar_xy.update()
        toolbar_xy.pack(fill=tk.X, side=tk.BOTTOM)

        width_list.append(dxf.width())
        # width_list.append(1)

        render.initialized = True

    if get_entry_value(entryY) != 0 or get_entry_value(entryX) != 0 or get_entry_value(entryPhi) != 0:
        x_shift = np.round(get_entry_value(entryX), 10)
        y_shift = (np.round(get_entry_value(entryY), 10))
        phi = (np.round(get_entry_value(entryPhi), 10))
        dxf.set_shift(x_shift, y_shift)
        dxf.set_rotation(phi)
        ramp.set_rotation(x_shift, y_shift, phi)

    # left plot (interactive plot)
    ax = axes_list[0]
    fig = figure_list[0]
    ax.clear()

    width = width_list[-1]

    # test how long the function runs
    start_time_f1 = time.time()

    ramp.plot_surface(fig, ax, width, res, get_unit_dropdown())
    dxf_points = dxf.plot_to_surface(fig, ax, ramp, get_entry_value(txt_enter_z_resolution), get_unit_dropdown())

    end_time_f1 = time.time()
    text_widget_output('\nNumber of points after projection onto surface: ' + str(dxf_points), 'blue')
    text_widget_output('\nElapsed time to plot the left plot (in s): ' + str(end_time_f1 - start_time_f1), 'blue')

    # uncomment the next 3 lines to enlarge the fontsize of the left plot
    # ax.set_zlabel('Z-Axis in µm', rotation=0, fontsize=16)
    # ax.set_xlabel('X-Axis in mm', rotation=0, fontsize=16)
    # ax.set_ylabel('Y-Axis in mm', rotation=0, fontsize=16)

    ax.set_zlabel('Z-Axis in µm', rotation=0)
    ax.set_xlabel('X-Axis in mm', rotation=0)
    ax.set_ylabel('Y-Axis in mm', rotation=0)

    # right plot (non interactive, fixed view angle plot)
    ax_xy = axes_list[1]
    ax_xy.clear()
    fig_xy = figure_list[1]

    # test how long the function runs
    start_time_f2 = time.time()

    ramp.plot_surface(fig_xy, ax_xy, width, res, get_unit_dropdown())
    dxf.plot_to_surface(fig_xy, ax_xy, ramp, get_entry_value(txt_enter_z_resolution), get_unit_dropdown())

    end_time_f2 = time.time()
    text_widget_output('\nElapsed time to plot the right plot (in s): ' + str(end_time_f2 - start_time_f2), 'blue')

    ax_xy.set_zlabel('Z-Axis in µm', rotation=0)
    ax_xy.set_xlabel('X-Axis in mm', rotation=0)
    ax_xy.set_ylabel('Y-Axis in mm', rotation=0)
    ax_xy.set_zticks([])  # turns the ticks in the z-axis off for better visibility

    text_widget_output('\nRendered successfully', 'blue')


# From here on it is just the GUI

# Class, that changes the standard output to the text widget from tkinter
class RedirectText:
    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string: str):
        self.text_space.insert(tk.END, string)
        self.text_space.see(tk.END)

    def flush(self):
        pass


class text_widget_output:
    """def __init__(self, string: str, color: str):
        txt_info.insert('end', string)
        txt_info.see('end')
        txt_info.tag_add('message', str(float(txt_info.index('end'))), 'end')
        print(txt_info.index('end'))
        txt_info.tag_config('message', foreground=color)
        #txt_info.tag_delete('message')"""

    def __init__(self, string: str, color: str):
        txt_info.tag_configure('red', foreground='red')
        txt_info.tag_configure('blue', foreground='blue')
        txt_info.tag_configure('green', foreground='green')

        if color == 'red':
            txt_info.insert('end', string, 'red')
        elif color == 'blue':
            txt_info.insert('end', string, 'blue')
        elif color == 'black':
            txt_info.insert('end', string, 'black')
        else:
            txt_info.insert('end', string, 'green')

        txt_info.see('end')

        # Get the indices for the last line
        """last_line_start = txt_info.index('end-2l')
        last_line_end = txt_info.index('end-1c lineend')
        print(txt_info.index('end linestart'), txt_info.index('end'))
        # Apply tags to the last line only
        txt_info.tag_add('message', last_line_start, last_line_end)
        txt_info.tag_configure('message', foreground=color)"""


def open_surface_file():
    """Opens the csv or sdf-file and creates an instance of CsvProfile  or sdfSurfacw which is then added to a list
    from where the render-function can use it."""

    filepath = askopenfilename(
        filetypes=[("*.csv, *.sdf", ("*.csv", "*.sdf")), ("All Files", "*.*")]
    )
    if not filepath:
        return
    elif filepath.lower().endswith(".csv"):
        surface_list.clear()
        surface_list.append(csv_data.CsvProfile(filepath, askfloat('Ramp length',
                                                               'What is the length of the ramp in mm? \nCancel if not needed.')))  # askfloat opens a popupwindow that asks for the length of the ramp

        if surface_list[-1].created_output_file:
            text_widget_output('\nCreated output_' + surface_list[-1].get_csv_name(), 'blue')
            text_widget_output('\noutput_' + surface_list[-1].get_csv_name() + ' loaded', 'green')
        elif surface_list[0].created_output_file == False:
            text_widget_output('\n' + surface_list[-1].get_file_name() + ' loaded', 'green')
        else:
            text_widget_output('\nAn error occurred', 'red')
            surface_list.clear()
    elif filepath.lower().endswith(".sdf"):
        surface_list.clear()
        surface_list.append(sdf_data.SdfSurface(filepath))
        text_widget_output('\n' + surface_list[-1].get_file_name() + ' loaded', 'green')
    else:
        text_widget_output('\nFile type not supported.', 'red')
        surface_list.clear()

    # changing the surface file means that the projection is invalid
    if len(dxf_list):
        dxf_list[-1].invalidateProjection()


def shortcut(shift: bool):
    """shortcut function for debugging. Loads the files, and immedeately plots them with a predefined shift"""
    surface_list.append(
        sdf_data.SdfSurface(r'C:\Users\ag4716\Documents\KIT_800um_gaussian_LP.SDF'))
    dxf_list.append(
        dxf_data.Dxf2D(r'C:\Users\ag4716\Documents\print_200um_ramp.dxf'))
    if shift:
        entryY.insert(0, '0.6')
        entryX.insert(0, '0.2')
    render(int(get_entry_value(txt_resolution)))


def open_dxf_file():
    """Opens the dxf-file and creates an instance of CsvProfile which is then added to al list from where the render-function can use it."""
    filepath = askopenfilename(
        filetypes=[("dxf Files", "*.dxf"), ("All Files", "*.*")]
    )
    if not filepath:
        return
    else:
        dxf_list.clear()
        dxf_list.append(dxf_data.Dxf2D(filepath))
        if dxf_list[-1].points == []:
            text_widget_output(
                '\nit seems as if the .dxf-file has an error. Try changing the file version to something different than AutoCAD R12/LT2 DXF.',
                'red')
        else:
            text_widget_output('\n' + dxf_list[-1].get_dxf_name() + ' loaded', 'green')


def get_entry_value(widget: tk.Entry) -> float:
    """returns the value written in the entry widget"""
    try:
        return float(widget.get())
    except:
        text_widget_output('\nEntry in wrong format', 'red')


def increase_entry_value(widget: tk.Entry):
    """Adds 0.1 to the value from the entry widget and updates the entry widget to the new value"""
    a = get_entry_value(widget)

    a += 0.1
    a = np.round(a, 5)
    widget.delete(0, tk.END)
    widget.insert(0, a)


def decrease_entry_value(widget: tk.Entry):
    """Subtracts 0.1 from the value from the entry widget and updates the entry widget to the new value"""

    a = get_entry_value(widget)

    a -= 0.1
    a = np.round(a, 5)
    widget.delete(0, tk.END)
    widget.insert(0, a)


def restart_program():
    """Restarts the current program, with file objects and descriptors
    cleanup"""
    window.destroy()
    try:
        p = subprocess.Popen([sys.executable] + sys.argv,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stdout:
            print(stdout.decode('utf-8'))
        if stderr:
            print(stderr.decode('utf-8'), file=sys.stderr)
    except Exception as e:
        print(f"Error during program restart: {e}")


def get_unit_dropdown():
    """returns the chosen value of the dropdown menu"""
    if unit_dropdown_clicked.get() == 'mm':
        return 0.001
    elif unit_dropdown_clicked.get() == 'µm':
        return 1
    elif unit_dropdown_clicked.get() == 'nm':
        return 1000
    elif unit_dropdown_clicked.get() == '\u00C5':
        return 10000


def export_button():
    """calls the export_xtpl_code function"""
    if len(dxf_list) == 0:
        text_widget_output('\nno .dxf-file loaded', 'red')
        return
    if len(surface_list) == 0:
        text_widget_output('\nno .csv or sdf-file loaded', 'red')
        return
    filepath = tk.filedialog.asksaveasfilename(filetypes=[("Text Document", "*.txt"), ("All Files", "*.*")],
                                               defaultextension=".txt")
    # user selected a filepath
    if filepath:
        export_xtpl.export_xtpl_code(dxf_list[-1].get_points(surface_list[-1], get_unit_dropdown()),
                                     askstring(title="function name", prompt="Name your function"), filepath)
        text_widget_output('\nSaved to: ' + filepath, 'blue')

    # user closed the file browser window
    else:
        text_widget_output('\nNo file chosen', 'red')


window = tk.Tk()
window.title('Visualize DXF and CSV')

window.rowconfigure(0, minsize=450, weight=1)
window.columnconfigure(1, minsize=450, weight=1)
window.columnconfigure(2, minsize=450, weight=1)
window.rowconfigure(1, weight=0)

# create a frame for the text widget an the scrollbar
frm_txt = tk.Frame(window, relief=tk.GROOVE, bd=2)
# create a text_info widget
txt_info = tk.Text(frm_txt, height=10)
# create a scrollbar and add functionality to it
S = tk.Scrollbar(frm_txt)
S.config(command=txt_info.yview)
txt_info.config(yscrollcommand=S.set)

# arrange text_info widget and scrollbar in the text frame
"""S.pack(side=tk.RIGHT, fill=tk.Y)
txt_info.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)"""
frm_txt.columnconfigure(0, weight=1)
frm_txt.columnconfigure(1, weight=0)
frm_txt.columnconfigure(2, weight=0)
S.grid(row=0, column=1, sticky='ns')
txt_info.grid(row=0, column=0, sticky='nsew')

# redirect standard output to the txt_info widget of the GUI
# sys.stdout = RedirectText(txt_info) #Todo: wieder den Standartoutput auf das Textwidget umändern

text_widget_output('1. Open your .csv or .sdf File. (Use ASCII and float for sdf files))\n'
                   '2. Open your .dxf-File . (Not AutoCAD R12/LT2 DXF)\n'
                   '3. Change the .csv-height unit if necessary (no influence for .sdf files)\n'
                   '4. Adjust the number of surfaces to approximate the scanned surface (only for .csv files)\n'
                   '5. Adjust the z-resolution of the projection if necessary\n'
                   '6. Press "Render" to plot your graphs or shift them directly by the Buttons or enter a value to the textfields\n'
                   '7. You can specify a rotation (counterclockwise) around the center point of the .dxf file (the shift, only for .sdf files)\n'
                   '8. Shift and rotate your plots until you are satisfied with the alignment and press "Render" again\n'
                   '9. Press "Export" to create your xtpl file', 'black')

"""txt_info.insert('end', '1. Open your .csv or .sdf file. (Use ASCII and float for sdf files))\n'
      '2. Open your .dxf-File \n'
      '3. Change the .csv-height unit if necessary (no influence for .sdf files)\n'
      '4. Adjust the number of surfaces to approximate the scanned surface\n'
      '5. Adjust the z-resolution of the projection if necessary\n'
      '6. Press "Render" to plot your graphs or shift them directly by the Buttons or enter a value to the textfields\n'
      '7. Shift your plots until you are satisfied with the alignment and press "Render" again\n'
      '8. Press "Export" to create your xtpl file\n')
txt_info.tag_add('program_explanation', '1.0', 'end')
txt_info.tag_config('program_explanation', foreground='black')"""
# create a frame for the plots and adjust it's size
window_plt = tk.Frame(window, relief=tk.GROOVE, bd=2)
window_plt.rowconfigure(1, weight=0)
window_plt_xy = tk.Frame(window, relief=tk.GROOVE, bd=2)
window_plt_xy.rowconfigure(0, weight=1)

# create a frame for the buttons
frm_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
# creat buttons for open_csv, open_dxf, render, x_up, export, stop
btn_open_csv = tk.Button(frm_buttons, text="Open surface",
                         command=lambda: open_surface_file())
btn_open_dxf = tk.Button(frm_buttons, text="Open dxf",
                         command=lambda: open_dxf_file())
btn_render = tk.Button(frm_buttons, text='Render', bg='#009682',
                       command=lambda: render(int(get_entry_value(txt_resolution))))  # calls the render function
btn_restart = tk.Button(frm_buttons, text='Restart', bg='#A22223',
                        command=lambda: restart_program())  # calls the restart_program function
btn_export = tk.Button(frm_buttons, text='Export', command=lambda: export_button())
# create an entry text widget txt_resosolution with a label
txt_resolution = tk.Entry(frm_buttons)
txt_resolution_label = tk.Label(frm_buttons, text='Number of surfaces')
txt_resolution.insert(0, '50')

# create an entry text widget txt_csv_length with a label
'''txt_csv_length = tk.Entry(frm_buttons)
txt_csv_length_label = tk.Label(frm_buttons, text='csv length in mm')'''

# create a dropdown menu and label for different units
options = ['mm', 'µm', 'nm', '\u00C5']
unit_dropdown_clicked = tk.StringVar(frm_buttons)
unit_dropdown_clicked.set(options[1])
unit_dropdown = tk.OptionMenu(frm_buttons, unit_dropdown_clicked, *options)
unit_dropdown_label = tk.Label(frm_buttons, text='CSV height unit')

# create an entry text widget txt_enter_z_resolution and corresponding label
txt_enter_z_resolution = tk.Entry(frm_buttons)
txt_enter_z_resolution_label = tk.Label(frm_buttons,
                                        text='z-resolution in µm')  # add get_unit_dropdown.get() but doesn't update when changing the dropdown menu

txt_enter_z_resolution.insert(0, '1')

# arrange buttons in the grid
btn_open_csv.grid(row=0, column=0, sticky='ew', padx=5, pady=2.5)
btn_open_dxf.grid(row=1, column=0, sticky='ew', padx=5, pady=2.5)
btn_render.grid(row=11, column=0, sticky='ew', padx=5, pady=2.5)
btn_export.grid(row=2, column=0, sticky='ew', padx=5, pady=2.5)
btn_restart.grid(row=12, column=0, sticky='ew', padx=5, pady=2.5)
txt_resolution_label.grid(row=7, column=0, sticky='ew', padx=5, pady=2.5)
txt_resolution.grid(row=8, column=0, sticky='ew', padx=5, pady=2.5)
unit_dropdown.grid(row=4, column=0, sticky='ew', padx=5, pady=2.5)
unit_dropdown_label.grid(row=3, column=0, sticky='ew', padx=5, pady=2.5)
txt_enter_z_resolution_label.grid(row=9, column=0, sticky='ew', padx=5, pady=2.5)
txt_enter_z_resolution.grid(row=10, column=0, sticky='ew', padx=5, pady=2.5)

# create a frame for the navigation and add buttons as well as entry widgets
frm_navigate = tk.Frame(frm_txt)
btn_Y_up = tk.Button(frm_navigate, text='Y \N{UPWARDS BLACK ARROW}', command=lambda: increase_entry_value(entryY))
btn_Y_down = tk.Button(frm_navigate, text='Y \N{DOWNWARDS BLACK ARROW}', command=lambda: decrease_entry_value(entryY))
btn_X_up = tk.Button(frm_navigate, text='X \N{RIGHTWARDS BLACK ARROW}', command=lambda: increase_entry_value(entryX))
btn_X_down = tk.Button(frm_navigate, text='\N{LEFTWARDS BLACK ARROW} X', command=lambda: decrease_entry_value(entryX))

btn_X_up.grid(row=1, column=2, sticky='ew', padx=5, pady=5)
btn_X_down.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
btn_Y_up.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
btn_Y_down.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

# create frm_navigate_text and add the widgets
frm_navigate_text = tk.Frame(frm_navigate)
entryX = tk.Entry(frm_navigate_text)
entryY = tk.Entry(frm_navigate_text)
entryPhi = tk.Entry(frm_navigate_text)
entry_x_label = tk.Label(frm_navigate_text, text='X-Shift / mm')
entry_y_label = tk.Label(frm_navigate_text, text='Y-Shift / mm')
entry_phi_label = tk.Label(frm_navigate_text, text='Rotation / °')
entryY.insert(0, '0')
entryX.insert(0, '0')
entryPhi.insert(0, '0')

entryX.grid(row=1, column=0, sticky='nsew', padx=5)
entryY.grid(row=3, column=0, sticky='nsew', padx=5)
entryPhi.grid(row=5, column=0, sticky='nsew', padx=5)
entry_x_label.grid(row=0, column=0, sticky='nsew', padx=5)
entry_y_label.grid(row=2, column=0, sticky='nsew', padx=5)
entry_phi_label.grid(row=4, column=0, sticky='nsew', padx=5)

# add frm_navigate_text to frm_navigate
frm_navigate_text.grid(row=0, rowspan=3, column=3)

# adjust button-frame and other frames in the window grid
frm_buttons.grid(row=0, column=0, rowspan=2, sticky='ns')
window_plt.grid(row=0, column=1, sticky='nsew')
window_plt_xy.grid(row=0, column=2, sticky='nsew')
frm_txt.grid(row=1, column=1, columnspan=2, sticky='ew')
frm_navigate.grid(row=0, column=2)

# shortcut(True)
# changes the icon of the window
window.iconphoto(False, tk.PhotoImage(file='logo_ihe.png'))
window.mainloop()
