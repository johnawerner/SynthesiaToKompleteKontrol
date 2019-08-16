# The MIT License
# 
# Copyright (c) 2019 John Werner
# 
# Synthesia for KK: An app to control NI Komplete Kontrol keyboards'
#                   Light Guide using MIDI events from Synthesia

import hid
import mido
import time
import sys
import tkinter as tk
from tkinter.ttk import Combobox
from tkinter.colorchooser import askcolor
from tkinter.messagebox import showerror
import threading
import configparser as cfg

NI_HID_ID = 0x17CC
S61_MK2_ID = 0x1620
S88_MK2_ID = 0x1630
S49_MK2_ID = 0x1610
S61_MK1_ID = 0x1360
S88_MK1_ID = 0x1410
S49_MK1_ID = 0x1350
S25_MK1_ID = 0x1340
MK2_HEADER_VAL = 0x81
MK1_HEADER_VAL = 0x82
LIGHT_GUIDE_CMD = 0xa0

class STKKApplication(tk.Frame):

    colorButtons = []              # List of the tkinter Buttons that select colors
    lights_buffer = []             # List of integers containing color values + 1 int header
    header_value = MK1_HEADER_VAL  # Header value for lights buffer
    buffer_scale = 3               # Integer scale value for indexing into the buffer
    color_list = []                # List of tuples containing the currently selected colors
    off_color = (0x00,)            # Tuple for turning off a light
    kb_hid_id = S61_MK1_ID         # Keyboard identifier used when opening HID
    kb_num_keys = 61               # Number of keys on the keyboard
    kb_note_offset = -36           # Offset to convert MIDI note value to buffer index
                                   # Calculated as 60 - number of keys below Middle C
    connected = False              # Boolean to indicate if currently connected
    listen = True                  # Boolean to control threaded listen loop
    kb_device = None               # HID keyboard device handle
    port_name = ""                 # Name of LoopBe1 MIDI loopback port
    thread_handle = None           # Handle for thread
    map_palette_dialog = None      # Handle for Map Palette dialog
    map_palette_index = None       # Handle for index label
    map_palette_color = None       # Handle for color swatch
    map_palette_dict = None        # Dictionary containing mapped palette values


    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        if master != None:
            master.title("Synthesia To Komplete Kontrol")
            master.geometry("640x420")
        self.grid(column=0, row=0)
        self.createWidgets()

    def createWidgets(self):
        """Creates the GUI widgets"""

        # Read user prefs from the .ini file
        uprefs = self.readUserPrefs()

        # Keyboard combobox label
        self.kb_combobox_label = tk.Label(self)
        self.kb_combobox_label["text"] = "Komplete Kontrol model"
        self.kb_combobox_label.grid(column=0, row=0, padx=10, pady=5, columnspan=2, sticky='W')

        # Keyboard listbox
        self.kb_combobox = Combobox(self)
        self.kb_combobox['values'] = [
            "Komplete Kontrol S61 MK2",
            "Komplete Kontrol S88 MK2",
            "Komplete Kontrol S49 MK2",
            "Komplete Kontrol S61 MK1",
            "Komplete Kontrol S88 MK1",
            "Komplete Kontrol S49 MK1",
            "Komplete Kontrol S25 MK1"]
        self.kb_combobox.current(uprefs['selectedkeyboard'])
        self.kb_combobox.grid(column=0, row=1, ipadx=10, padx=10, pady=5, columnspan=2, sticky='W')

        # Color labels & buttons
        self.colors_label = tk.Label(self)
        self.colors_label["text"] = "Key Colors:"
        self.colors_label.grid(column=0, row=2, padx=10, sticky='W')

        self.color0_label = tk.Label(self)
        self.color0_label["text"] = "Default (Unknown hand/finger)"
        self.color0_label.grid(column=1, row=3, padx=5, sticky='W')
        self.color0_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(0), bg=uprefs['defaultcolor'])
        self.color0_button.grid(column=0, row=3, pady=1, sticky='E')
        self.colorButtons.append(self.color0_button)

        self.color1_label = tk.Label(self)
        self.color1_label["text"] = "Left thumb"
        self.color1_label.grid(column=1, row=4, padx=5, sticky='W')
        self.color1_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(1), bg=uprefs['leftthumb'])
        self.color1_button.grid(column=0, row=4, pady=1, sticky='E')
        self.colorButtons.append(self.color1_button)

        self.color2_label = tk.Label(self)
        self.color2_label["text"] = "Left index"
        self.color2_label.grid(column=1, row=5, padx=5, sticky='W')
        self.color2_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(2), bg=uprefs['leftindex'])
        self.color2_button.grid(column=0, row=5, pady=1, sticky='E')
        self.colorButtons.append(self.color2_button)

        self.color3_label = tk.Label(self)
        self.color3_label["text"] = "Left middle"
        self.color3_label.grid(column=1, row=6, padx=5, sticky='W')
        self.color3_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(3), bg=uprefs['leftmiddle'])
        self.color3_button.grid(column=0, row=6, pady=1, sticky='E')
        self.colorButtons.append(self.color3_button)

        self.color4_label = tk.Label(self)
        self.color4_label["text"] = "Left ring"
        self.color4_label.grid(column=1, row=7, padx=5, sticky='W')
        self.color4_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(4), bg=uprefs['leftring'])
        self.color4_button.grid(column=0, row=7, pady=1, sticky='E')
        self.colorButtons.append(self.color4_button)

        self.color5_label = tk.Label(self)
        self.color5_label["text"] = "Left pinky"
        self.color5_label.grid(column=1, row=8, padx=5, sticky='W')
        self.color5_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(5), bg=uprefs['leftpinky'])
        self.color5_button.grid(column=0, row=8, pady=1, sticky='E')
        self.colorButtons.append(self.color5_button)

        self.color6_label = tk.Label(self)
        self.color6_label["text"] = "Right thumb"
        self.color6_label.grid(column=3, row=4, padx=5, sticky='W')
        self.color6_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(6), bg=uprefs['rightthumb'])
        self.color6_button.grid(column=2, row=4, pady=1, sticky='E')
        self.colorButtons.append(self.color6_button)

        self.color7_label = tk.Label(self)
        self.color7_label["text"] = "Right index"
        self.color7_label.grid(column=3, row=5, padx=5, sticky='W')
        self.color7_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(7), bg=uprefs['rightindex'])
        self.color7_button.grid(column=2, row=5, pady=1, sticky='E')
        self.colorButtons.append(self.color7_button)

        self.color8_label = tk.Label(self)
        self.color8_label["text"] = "Right middle"
        self.color8_label.grid(column=3, row=6, padx=5, sticky='W')
        self.color8_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(8), bg=uprefs['rightmiddle'])
        self.color8_button.grid(column=2, row=6, pady=1, sticky='E')
        self.colorButtons.append(self.color8_button)

        self.color9_label = tk.Label(self)
        self.color9_label["text"] = "Right ring"
        self.color9_label.grid(column=3, row=7, padx=5, sticky='W')
        self.color9_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(9), bg=uprefs['rightring'])
        self.color9_button.grid(column=2, row=7, pady=1, sticky='E')
        self.colorButtons.append(self.color9_button)

        self.color10_label = tk.Label(self)
        self.color10_label["text"] = "Right pinky"
        self.color10_label.grid(column=3, row=8, padx=5, sticky='W')
        self.color10_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(10), bg=uprefs['rightpinky'])
        self.color10_button.grid(column=2, row=8, pady=1, sticky='E')
        self.colorButtons.append(self.color10_button)

        self.color11_label = tk.Label(self)
        self.color11_label["text"] = "Left hand (Unknown finger)"
        self.color11_label.grid(column=1, row=9, padx=5, sticky='W')
        self.color11_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(11), bg=uprefs['lefthand'])
        self.color11_button.grid(column=0, row=9, pady=1, sticky='E')
        self.colorButtons.append(self.color11_button)

        self.color12_label = tk.Label(self)
        self.color12_label["text"] = "Right hand (Unknown finger)"
        self.color12_label.grid(column=3, row=9, padx=5, sticky='W')
        self.color12_button = tk.Button(self, width=5, command=lambda:self.colorButtonClick(12), bg=uprefs['righthand'])
        self.color12_button.grid(column=2, row=9, pady=1, sticky='E')
        self.colorButtons.append(self.color12_button)

        # Control buttons
        self.connectButton = tk.Button(self, text=" Connect  ", command=self.start, bg='#fefefe')
        self.connectButton.grid(column=0, row=10, pady=10)
        self.disconnectButton = tk.Button(self, text="Disconnect", command=self.stop, bg='#fefefe', state='disabled')
        self.disconnectButton.grid(column=1, row=10, pady=10)
        self.exitButton = tk.Button(self, text="  Exit  ", command=self.quit, bg='#fefefe')
        self.exitButton.grid(column=2, row=10, pady=10)
        self.mapPaletteButton = tk.Button(self, text="Map Palette", state='disabled', command=self.mapPalette, bg='#fefefe')
        self.mapPaletteButton.grid(column=3, row=10, pady=10)

    def colorButtonClick(self, button_num):
        """Color button click handler, opens color picker to set
           button's color"""
        start_color = self.colorButtons[button_num].cget('bg')
        result = askcolor(start_color)
        if result[1]:
            self.colorButtons[button_num].configure(bg=result[1])

    def enableGUIControls(self, enable = True):
        """Enable or disable GUI elements while connected"""
        for button in self.colorButtons:
            if enable:
                button.configure(state = 'normal')
            else:
                button.configure(state = 'disabled')
        if enable:
            self.kb_combobox.configure(state='normal')
        else:
            self.kb_combobox.configure(state='disabled')

    def start(self):
        """Connect button click handler"""
        if not self.connected:
            self.setAttributes()
            self.connected = self.connectToKeyboard()
            if self.connected:
                if self.findMIDIPort():
                    self.enableGUIControls(False)
                    self.disconnectButton.configure(state='normal')
                    self.mapPaletteButton.configure(state='normal')
                    self.listen = True
                    self.lightsOut()
                    self.thread_handle = threading.Thread(target=self.lightKeyboardThread, args=())
                    self.thread_handle.daemon = True
                    self.thread_handle.start()
                else:
                    self.kb_device.close()
                    self.connected = False


    def stop(self):
        """Disconnect button click handler"""
        self.listen = False
        self.connected = False # Disconnect from keyboard is handled in thread
        self.thread_handle.join()
        self.thread_handle = None
        self.enableGUIControls()
        self.mapPaletteButton.configure(state='disabled')
        self.disconnectButton.configure(state='disabled')


    def quit(self):
        """Exit button click handler"""
        self.listen = False
        self.writeUserPrefs()
        if self.thread_handle:
            self.thread_handle.join()
        if self.map_palette_dialog:
            self.map_palette_dialog.destroy()
        root.destroy()

    def setAttributes(self):
        """Sets the object's attributes based on KK model"""

        # Get the index of the currently selected keyboard
        selected = self.kb_combobox.current()

        # Setup variables according to keyboard model
        if selected == 0:  # Komplete Kontrol S61 MK2
            self.kb_num_keys = 61
            self.kb_note_offset = -36
            self.kb_hid_id = S61_MK2_ID
            self.header_value = MK2_HEADER_VAL
            self.buffer_scale = 1
            self.off_color = (0x00,)
            self.color_list = self.ButtonsToPaletteColorList()
        elif selected == 1:  # Komplete Kontrol S88 MK2
            self.kb_num_keys = 88
            self.kb_note_offset = -21
            self.kb_hid_id = S88_MK2_ID
            self.header_value = MK2_HEADER_VAL
            self.buffer_scale = 1
            self.off_color = (0x00,)
            self.color_list = self.ButtonsToPaletteColorList()
        elif selected == 2:  # Komplete Kontrol S49 MK2
            self.kb_num_keys = 49
            self.kb_note_offset = -36
            self.kb_hid_id = S49_MK2_ID
            self.header_value = MK2_HEADER_VAL
            self.buffer_scale = 1
            self.off_color = (0x00,)
            self.color_list = self.ButtonsToPaletteColorList()
        elif selected == 3:  # Komplete Kontrol S61 MK1
            self.kb_num_keys = 61
            self.kb_note_offset = -36
            self.kb_hid_id = S61_MK1_ID
            self.header_value = MK1_HEADER_VAL
            self.buffer_scale = 3
            self.off_color = (0x00,0x00,0x00)
            self.color_list = self.ButtonsToRGBColorList()
        elif selected == 4:  # Komplete Kontrol S88 MK1
            self.kb_num_keys = 88
            self.kb_note_offset = -21
            self.kb_hid_id = S88_MK1_ID
            self.header_value = MK1_HEADER_VAL
            self.buffer_scale = 3
            self.off_color = (0x00,0x00,0x00)
            self.color_list = self.ButtonsToRGBColorList()
        elif selected == 5:  # Komplete Kontrol S49 MK1
            self.kb_num_keys = 49
            self.kb_note_offset = -36
            self.kb_hid_id = S49_MK1_ID
            self.header_value = MK1_HEADER_VAL
            self.buffer_scale = 3
            self.off_color = (0x00,0x00,0x00)
            self.color_list = self.ButtonsToRGBColorList()
        elif selected == 6:  # Komplete Kontrol S25 MK1
            self.kb_num_keys = 25
            self.kb_note_offset = -48
            self.kb_hid_id = S25_MK1_ID
            self.header_value = MK1_HEADER_VAL
            self.buffer_scale = 3
            self.off_color = (0x00,0x00,0x00)
            self.color_list = self.ButtonsToRGBColorList()
        else:
            return False

        # Create the buffer for the color values
        self.lights_buffer = [0x00] * (self.kb_num_keys * self.buffer_scale + 1)
        self.lights_buffer[0] = self.header_value

        return True

    def connectToKeyboard(self):
        """Attempts to connect to keyboard as HID"""
        self.kb_device=hid.device()
        try:
            self.kb_device.open(NI_HID_ID, self.kb_hid_id)
        except Exception as e:
            showerror("Could not connect to KK", 'Connection error: ' + str(e))
            return False

        # Set the keyboard to receive Light Guide data
        self.kb_device.write([LIGHT_GUIDE_CMD])
        return True

    def findMIDIPort(self):
        """Looks for the LoopBe1 MIDI port"""
        ports = mido.get_input_names()
        for port in ports:
            if "LoopBe" in port:
                self.port_name = port
        if self.port_name == "":
            showerror("MIDI Port Error",
                "Please install LoopBe1 from http://www.nerds.de/en/download.html.")
            return False
        return True

    def lightsOut(self):
        """Turn off all lights"""
        for i in range(1, len(self.lights_buffer)):
            self.lights_buffer[i] = 0x00
        self.kb_device.write(self.lights_buffer)
    
    def MIDIMsgToLightGuide(self, note, status, channel, velocity):
        """Use MIDI messages to update KK's Light Guide"""

        # Turn off light
        if status == 'note_off':
            self.writeColorToBuffer(self.off_color, note + self.kb_note_offset)

        # Turn on light
        elif status == 'note_on' and channel >= 0 and channel < len(self.color_list): 
            self.writeColorToBuffer(self.color_list[channel], note + self.kb_note_offset)

        # Write the buffer to the keyboard device
        self.kb_device.write(self.lights_buffer)

    def writeColorToBuffer(self, color, index):
        """Writes a color to the lights buffer -
           color should be a tuple -
           index should be an int between 0 and (number of keys - 1), inclusive"""
        
        # Calculate the index for the lights buffer
        index = 1 + (index  * self.buffer_scale)

        # Check the index is within range of the buffer
        if index < 1 or index > (len(self.lights_buffer) - self.buffer_scale):
            return  

        # Write the color value to the lights buffer
        for color_val in color:
            self.lights_buffer[index] = color_val
            index += 1

    def krSweep(self, loopcount):
        """Performs a red light sweep across Light Guide"""
        speed = 0.01

        if self.buffer_scale == 3:
            color1 = (0x7F, 0x00, 0x00)
            color2 = (0x3F, 0x00, 0x00)
            color3 = (0x0F, 0x00, 0x00)
        else:
            color1 = (0x07,)
            color2 = (0x05,)
            color3 = (0x04,)

        while loopcount > 0:
            # Forward
            for x in range(0, self.kb_num_keys):
                for i in range(1, len(self.lights_buffer)):
                    self.lights_buffer[i] = 0x00
                self.writeColorToBuffer(color1, x)
                if x + 1 < self.kb_num_keys:
                    self.writeColorToBuffer(color2, x + 1)
                if x + 2 < self.kb_num_keys:
                    self.writeColorToBuffer(color3, x + 2)
                if x - 1 >= 0:
                    self.writeColorToBuffer(color2, x - 1)
                if x - 2 >= 0:
                    self.writeColorToBuffer(color3, x - 2)
                self.kb_device.write(self.lights_buffer)
                time.sleep(speed)
            # Backward
            for x in range(self.kb_num_keys - 1, -1, -1):
                for i in range(1, len(self.lights_buffer)):
                    self.lights_buffer[i] = 0x00
                self.writeColorToBuffer(color1, x)
                if x + 1 < self.kb_num_keys:
                    self.writeColorToBuffer(color2, x + 1)
                if x + 2 < self.kb_num_keys:
                    self.writeColorToBuffer(color3, x + 2)
                if x - 1 >= 0:
                    self.writeColorToBuffer(color2, x - 1)
                if x - 2 >= 0:
                    self.writeColorToBuffer(color3, x - 2)
                self.kb_device.write(self.lights_buffer)
                time.sleep(speed)
            loopcount -= 1
        self.lightsOut()
        
    def lightKeyboardThread(self):
        """Threaded method to update KK Light Guide"""
        self.krSweep(2)
        midiPort = mido.open_input(self.port_name)
        while self.listen:
            for message in midiPort.iter_pending():
                if message.type in ('note_on', 'note_off'):
                    self.MIDIMsgToLightGuide(message.note, message.type, message.channel, message.velocity)
        self.lightsOut()
        self.kb_device.close()
        midiPort.close()

    def readUserPrefs(self):
        """Reads user preferences from STKKConfig.ini"""
        prefs = {}

        prefs_file = cfg.ConfigParser()
        files = prefs_file.read('STKKConfig.ini')
        if len(files) == 1 and 'UserPrefs' in prefs_file:
            up = prefs_file['UserPrefs']
            prefs['selectedkeyboard'] = up.getint('selectedkeyboard', fallback=3)
            prefs['defaultcolor'] = up.get('defaultcolor', fallback='#ff0000')
            prefs['leftthumb'] = up.get('leftthumb', fallback='#00ff00')
            prefs['leftindex'] = up.get('leftindex', fallback='#00ff00')
            prefs['leftmiddle'] = up.get('leftmiddle', fallback='#00ff00')
            prefs['leftring'] = up.get('leftring', fallback='#00ff00')
            prefs['leftpinky'] = up.get('leftpinky', fallback='#00ff00')
            prefs['lefthand'] = up.get('lefthand', fallback='#00ff00')
            prefs['rightthumb'] = up.get('rightthumb', fallback='#0000ff')
            prefs['rightindex'] = up.get('rightindex', fallback='#0000ff')
            prefs['rightmiddle'] = up.get('rightmiddle', fallback='#0000ff')
            prefs['rightring'] = up.get('rightring', fallback='#0000ff')
            prefs['rightpinky'] = up.get('rightpinky', fallback='#0000ff')
            prefs['righthand'] = up.get('righthand', fallback='#0000ff')
        else:
            # STKKConfig.ini not found, set defaults
            prefs['selectedkeyboard'] = 3
            prefs['defaultcolor'] = '#ff0000'
            prefs['leftthumb'] = '#00ffff'
            prefs['leftindex'] = '#0099ff'
            prefs['leftmiddle'] = '#0000ff'
            prefs['leftring'] = '#6600ff'
            prefs['leftpinky'] = '#ff00ff'
            prefs['lefthand'] = '#0000ff'
            prefs['rightthumb'] = '#ff8000'
            prefs['rightindex'] = '#ffd900'
            prefs['rightmiddle'] = '#b3ff00'
            prefs['rightring'] = '#00ff00'
            prefs['rightpinky'] = '#00ffbf'
            prefs['righthand'] = '#00ff00'

        return prefs

    def writeUserPrefs(self):
        """Writes user preferences to STKKConfig.ini"""
        config = cfg.ConfigParser()
        config['UserPrefs'] = {}
        up = config['UserPrefs']
        up['selectedkeyboard'] = str(self.kb_combobox.current())
        up['defaultcolor'] = self.colorButtons[0].cget('bg')
        up['leftthumb'] = self.colorButtons[1].cget('bg')
        up['leftindex'] = self.colorButtons[2].cget('bg')
        up['leftmiddle'] = self.colorButtons[3].cget('bg')
        up['leftring'] = self.colorButtons[4].cget('bg')
        up['leftpinky'] = self.colorButtons[5].cget('bg')
        up['lefthand'] = self.colorButtons[11].cget('bg')
        up['rightthumb'] = self.colorButtons[6].cget('bg')
        up['rightindex'] = self.colorButtons[7].cget('bg')
        up['rightmiddle'] = self.colorButtons[8].cget('bg')
        up['rightring'] = self.colorButtons[9].cget('bg')
        up['rightpinky'] = self.colorButtons[10].cget('bg')
        up['righthand'] = self.colorButtons[12].cget('bg')
        with open('STKKConfig.ini', 'w') as configfile:
            config.write(configfile)

    def ButtonsToRGBColorList(self):
        """Takes the attribute list of color Buttons and returns a list of 
            7-bit RGB tuples containing their background colors"""
        colors = []
        for button in self.colorButtons:
            if isinstance(button, tk.Button):
                colors.append(RGBStringToTuple(button.cget('bg')))
        return colors

    def ButtonsToPaletteColorList(self):
        """Takes the attribute list of color Buttons and returns a list of 
        one element tuples containing their background colors
        mapped to palette indices"""
        colors = []
        # Load the palette map from the .ini file
        prefs_file = cfg.ConfigParser()
        files = prefs_file.read('PaletteMap.ini')

        # If the .ini contains the palette map, map
        # button background colors to palette
        if len(files) == 1 and 'PaletteMap' in prefs_file:
            palette_map = prefs_file['PaletteMap']
            for button in self.colorButtons:
                if isinstance(button, tk.Button):
                    colors.append(mapRGBStringToPalette(button.cget('bg'), palette_map))
        else:
            # Palette map not loaded, map to arbitrary colors
            colors.append((0x07,))
            colors.append((0x2D,))
            colors.append((0x2F,))
            colors.append((0x2F,))
            colors.append((0x2F,))
            colors.append((0x2F,))
            colors.append((0x1F,))
            colors.append((0x1B,))
            colors.append((0x1B,))
            colors.append((0x1B,))
            colors.append((0x1B,))
            colors.append((0x2F,))
            colors.append((0x1B,))
        return colors

    ###
    # Map Palette methods
    ###
    def mapPalette(self):
        """Map Palette button click handler"""

        # If the keyboard is not connected, show an error
        if not self.connected:
            showerror(title='Not Connected',
                message='Connect to keyboard before mapping palette')
            return

        # If the buffer scale is 3, assume this is a MK1 keyboard
        # and show an error
        if self.buffer_scale == 3:
            showerror(title="Unmappable",
                message="MK1 keyboards do not need to be mapped")
            return

        # Disable buttons
        self.enableGUIControls(False)
        self.disconnectButton.configure(state='disabled')
        self.mapPaletteButton.configure(state='disabled')

        # If the palette dialog doesn't exist, create it
        if not self.map_palette_dialog:
            # Create window
            self.map_palette_dialog = tk.Toplevel(self)
            self.map_palette_dialog.title('Map MK2 Palette')
            # Create labels
            valueLabel = tk.Label(self.map_palette_dialog)
            valueLabel["text"] = "Index:"
            valueLabel.grid(column=0, row=0, padx=5, pady=10, sticky='E')
            colorLabel = tk.Label(self.map_palette_dialog)
            colorLabel["text"] = "Color:"
            colorLabel.grid(column=2, row=0, padx=5, pady=10, sticky='W')
            #Create index and color displays
            self.map_palette_index = tk.Label(self.map_palette_dialog)
            self.map_palette_index["text"] = "0x01"
            self.map_palette_index.grid(column=1, row=0, sticky='W')
            self.map_palette_color = tk.Button(self.map_palette_dialog, width=8, state='disabled', bg='#000000')
            self.map_palette_color.grid(column=3, row=0, padx=2, sticky='W')
            # Create buttons
            previousButton = tk.Button(self.map_palette_dialog, text="< Prev", command=self.mapPalettePrev, bg='#fefefe')
            previousButton.grid(column=0, row=2, sticky='E')
            nextButton = tk.Button(self.map_palette_dialog, text="Next >", command=self.mapPaletteNext, bg='#fefefe')
            nextButton.grid(column=1, row=2, sticky='W')
            setButton = tk.Button(self.map_palette_dialog, text="Set Color", command=self.mapPaletteSetColor, bg='#fefefe')
            setButton.grid(column=3, row=2, sticky='W')
            saveButton = tk.Button(self.map_palette_dialog, text=" Save ", command=self.mapPaletteSave, bg='#fefefe')
            saveButton.grid(column=0, row=3, padx=10, pady=10, sticky='W')
            cancelButton = tk.Button(self.map_palette_dialog, text="Cancel", command=self.mapPaletteCancel, bg='#fefefe')
            cancelButton.grid(column=1, row=3, padx=10, sticky='W')
            # Capture the Close Window event and
            # map it to the Cancel button handler
            self.map_palette_dialog.protocol("WM_DELETE_WINDOW", self.mapPaletteCancel)
        elif self.map_palette_dialog.state() == 'iconic':
            # Else show the window
            self.map_palette_dialog.deiconify()
        
        # If there is no palette map dictionary
        if not self.map_palette_dict:
            # Try to load the palette map from the .ini file
            prefs_file = cfg.ConfigParser()
            files = prefs_file.read('PaletteMap.ini')
            # If the .ini contains the palette map, set the dictionary
            if len(files) == 1 and 'PaletteMap' in prefs_file:
                self.map_palette_dict = prefs_file['PaletteMap']
            else:
                # Else create a new dictionary
                self.map_palette_dict = {}
        # Display the current palette map color in the dialog
        self.showCurrentMapColor()

    def showCurrentMapColor(self):
        """Displays the color of the current index in the map palette dialog"""
        # Get the current palette index from the dialog
        currentIndex = self.map_palette_index.cget('text')
        currentColor = '#000000'
        # Read the currently mapped color if the palette map dictionary exists
        if self.map_palette_dict:
            if currentIndex in self.map_palette_dict:
                currentColor = self.map_palette_dict[currentIndex]
        # Display the color in the dialog
        self.map_palette_color.configure(bg=currentColor)
        # Display the palette index on the keyboard
        self.displayPaletteIndex(currentIndex)

    def displayPaletteIndex(self, index):
        """Displays the palette index on the keyboard"""
        # Make sure the keyboard is connected
        if not self.connected:
            return
        # If the passed index is not an int, convert it
        if not isinstance(index, int):
            index = int(index, 16)
        # Create the tuple
        indexTuple = (index,)
        # Display the palette index in the first 12 keys
        for i in range(0, 12):
            self.writeColorToBuffer(indexTuple, i)
        self.kb_device.write(self.lights_buffer)

    def mapPalettePrev(self):
        """Map Palette dialog Prev button handler"""
        # Read the current index from the dialog
        currentIndex = self.map_palette_index.cget('text')
        # Convert the index to an int
        currentIndex = int(currentIndex, 16)
        # If the index is > 1
        if currentIndex > 1:
            # Decrement the index
            currentIndex -= 1
            # Update the dialog and keyboard
            currentIndex = '0x' + ("%02x" % (currentIndex,))
            self.map_palette_index.configure(text=currentIndex)
            self.showCurrentMapColor()

    def mapPaletteNext(self):
        """Map Palette dialog Next button handler"""
        # Read the current index from the dialog
        currentIndex = self.map_palette_index.cget('text')
        # Convert the index to an int
        currentIndex = int(currentIndex, 16)
        # If the index is < 255
        if currentIndex < 255:
            # Increment the index
            currentIndex += 1
            # Update the dialog and keyboard
            currentIndex = '0x' + ("%02x" % (currentIndex,))
            self.map_palette_index.configure(text=currentIndex)
            self.showCurrentMapColor()

    def mapPaletteSetColor(self):
        """Map Palette dialog Set Color button handler"""
        # Get the current color from the dialog
        currentColor = self.map_palette_color.cget('bg')
        # Show the color picker
        result = askcolor(currentColor, parent=self.map_palette_dialog)
        # If a color was selected
        if result[1]:
            # Update the dialog with the new color
            self.map_palette_color.configure(bg=result[1])
            # Get the current index from the dialog
            currentIndex = self.map_palette_index.cget('text')
            # Store in the palette map dictionary
            self.map_palette_dict[currentIndex] = result[1]

    def mapPaletteSave(self):
        """Map Palette dialog Save button handler"""
        # Create a ConfigParser
        config = cfg.ConfigParser()
        # Set the palette map dictionary
        config['PaletteMap'] = self.map_palette_dict
        # Write the palette map to the config file
        with open('PaletteMap.ini', 'w') as configfile:
            config.write(configfile)
        # Turn off keyboard lights
        self.lightsOut()
        # Enable buttons
        self.enableGUIControls()
        self.disconnectButton.configure(state='normal')
        self.mapPaletteButton.configure(state='normal')
        # Destroy the Map Palette dialog
        self.map_palette_dialog.destroy()
        self.map_palette_dialog = None

    def mapPaletteCancel(self):
        """Map Palette dialog Cancel button handler"""
        # Turn off keyboard lights
        self.lightsOut()
        # Enable buttons
        self.enableGUIControls()
        self.disconnectButton.configure(state='normal')
        self.mapPaletteButton.configure(state='normal')
        # Destroy the Map Palette dialog
        self.map_palette_dialog.destroy()
        self.map_palette_dialog = None


def RGBTupleToString(rgb_tuple):
    """Takes a tuple containing three ints and returns an RGB string code"""
    rtn_str = "#%02x%02x%02x" % rgb_tuple
    return rtn_str

def RGBStringToTuple(rgb_str, make7bit = True):
    """Takes a color string of format #ffffff and returns an RGB tuple. 
    By default the values of the tuple are converted to 7-bits. 
    Pass False as the second parameter for 8-bits."""
    rgb_tuple = (0, 0, 0)
    if (len(rgb_str) >= 7) and (rgb_str[0] == "#"):
        red = int(rgb_str[1:3], 16)
        green = int(rgb_str[3:5], 16)
        blue = int(rgb_str[5:7], 16)
        if make7bit:
            red = red // 2
            green = green // 2
            blue = blue // 2
        rgb_tuple = (red, green, blue)
    return rgb_tuple

def mapRGBStringToPalette(RGBstring, palette_map):
    """Takes an RGB string of format #ffffff and returns
    a single element tuple containing the palette index
    of the nearest matching color. Palette map has palette
    indices in 0xFF format for keys and RGB strings as values"""
    rgb_tuple = RGBStringToTuple(RGBstring, False)
    distance = 1000.0
    index_tuple = (0x07,)
    for key in palette_map:
        palette_tuple = RGBStringToTuple(palette_map[key], False)
        # Calculate the relative distance between the two colors,
        # weighting the RGB values with typical luminance ratios
        red_distance = abs(rgb_tuple[0] - palette_tuple[0])
        green_distance = abs(rgb_tuple[1] - palette_tuple[1])
        blue_distance = abs(rgb_tuple[2] - palette_tuple[2])
        cur_dist = red_distance * 0.299 + green_distance * 0.587 + blue_distance * 0.114
        # If the colors are closer than any previous comparison,
        # store the distance and create a new tuple
        if cur_dist < distance:
            distance = cur_dist
            index_tuple = (int(key, 16),)
    return index_tuple

# Create the toplevel widget
root = tk.Tk()
# Create the application object
my_app = STKKApplication(root)
# Capture the Close Window event and
# map it to the Exit button handler
root.protocol("WM_DELETE_WINDOW", my_app.quit)
# Start the GUI's main loop
root.mainloop()
