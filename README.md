# SynthesiaToKompleteKontrol

### Let [Synthesia](https://synthesiagame.com) control Native Instruments Komplete Kontrol keyboard's Light Guide

[![Synthesia To Komplete Kontrol](https://img.youtube.com/vi/mMjFYRL6QJw/0.jpg)](https://www.youtube.com/watch?v=mMjFYRL6QJw)

(Click pic for demo video)

SynthesiaToKK is a GUI-based application that allows [Synthesia](https://synthesiagame.com) to control the Light Guide of Native Instruments' Komplete Kontrol line of keyboards.  This can be useful when learning a new song, or it can be entertaining to watch, like a player piano.

Unfortunately, SynthesiaToKK is Windows-only at this time.  I do not have a Mac to test it on, but I will work with anyone willing to attempt a port.

## Usage

SynthesiaToKK requires a virtual MIDI port to operate.  It is currently coded to use LoopBe1.

### Synthesia setup
* Download and install the [LoopBe1](http://www.nerds.de/en/download.html) virtual MIDI port driver.
* In [Synthesia](https://synthesiagame.com):
  * Go to __Settings__->__Music Devices__
  * Under __Music Output__ select __LoopBe Internal MIDI__
  * Select __Use this device__
  * Under __Use this device for:__
    * Turn off all settings that were automatically selected
    * Select __Key Lights__
    * Select __Finger-based channel__

### SynthesiaToKK setup
![ ](https://github.com/johnawerner/SynthesiaToKompleteKontrol/blob/master/STKKScreenCap.jpg)

* Download the current release and unzip it
* Start the SynthesiaToKK application
    * Select the correct model from the dropdown menu
    * Click each colored button and select the desired color from the color picker dialog
    * Click the __Connect__ button - A successful connection is indicated by a red light sweep across the Light Guide
    * Start using [Synthesia](https://synthesiagame.com)

#### Remapping the MK2 Palette
__Note to MK2 keyboard users:__  Because of the differences between MK1 and MK2 keyboards, the Light Guide colors may not be correct.  The MK1 Light Guide uses RGB values to control colors, but the MK2 uses a palette.  SynthesiaToKK will automatically convert the user-selected RGB values to the palette, but the palette map must be correct first.  I have made an attempt at mapping the MK2 palette using details from other Github projects.  If the colors are incorrect, the palette can be remapped.  This is a tedious process but only needs to be done once.  If remapping is necessary, please contact me so I can update the code and current release with the remapped config file.

* Delete the PaletteMap.ini file from the directory where SynthesiaToKK was unzipped
* Start the SynthesiaToKK application
* Connect to the keyboard
* Click the __Map Palette__ button to bring up the dialog
* Use the __Prev__ and __Next__ buttons to cycle through the palette values
* For each palette value, the lowest octave of your keyboard should light with a color.  If it does not, the Light Guide does not use that palette value and no color should be selected.
* For every palette value that produces a color on the keyboard, click the __Set Color__ button and select the color that is the closest match in the color picker
* When finished mapping the palette, click the __Save__ button to dismiss the dialog and create the new PaletteMap.ini file
* Disconnect then reconnect to the keyboard to be sure the new palette map is being used

I believe the MK2 palette uses 64 colors.  In any case it should be contiguous, so once the palette values stop displaying colors on the keyboard, you should be finished.

# Further Development
This project is released under the MIT license, and further development is encouraged.

Although I have decades of experience developing software, I originally wrote this project to learn Python.  I am open to any suggestions where the code can be improved.

The code requires the following Python modules:
* hidapi
* mido
* python-rtmidi

All code is in the SynthesiaToKK.py file, and requires Python 3.

Two errors in the code will be reported by pylint.  It reports that the mido module has no members named 'get_input_names' or 'open_input'.  These errors can be ignored, the code will still execute.  I am assuming the two functions are not properly exported by the mido module.

The setup.py file can be used to build an excutable using the cx-freeze module.  However, the paths for the tcl/tk environment variables and DLLs must be modified for your system.

Although the code for this project will run under Python 3.7, the cx-freeze module will not.  The release executables were built using Python 3.6.8.


# Acknowledgements

This project would not be possible without the ground-breaking work of others.

Thanks to:
* [Nicholas Piegdon](https://github.com/npiegdon) for creating the excellent game [Synthesia](https://synthesiagame.com)
* [AnykeyNL](https://github.com/AnykeyNL) for investigating the Komplete Kontrol USB protocol
* [ojacques](https://github.com/ojacques) for expanding the USB protocol to include MK2 keyboards
