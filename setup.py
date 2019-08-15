import sys
import os
from cx_Freeze import setup, Executable

os.environ['TCL_LIBRARY'] = r'C:\Users\John\AppData\Local\Programs\Python\Python36\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\John\AppData\Local\Programs\Python\Python36\tcl\tk8.6'

base = None
if sys.platform=='win32':
        base="WIN32GUI"

executables = [
        Executable("SynthesiaToKK.py", base=base)
]
   
buildOptions = dict(
        includes = ["mido.backends.rtmidi"],
        include_files = [r'C:\Users\John\AppData\Local\Programs\Python\Python36\DLLs\tcl86t.dll',
                 r'C:\Users\John\AppData\Local\Programs\Python\Python36\DLLs\tk86t.dll']
)

setup(
    name = "SynthesiaToKK",
    version = "1.0",
    description = "Let Synthesia control Komplete Kontrol keyboards Light Guide",
    options = dict(build_exe = buildOptions),
    executables = executables
)