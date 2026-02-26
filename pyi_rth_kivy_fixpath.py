"""
PyInstaller runtime hook to set kivy's resource paths correctly.
When running from a frozen exe, kivy looks for its data files relative
to sys._MEIPASS, but collect_data_files places them under kivy/data/.
This hook tells kivy where to find them.
"""
import os
import sys

if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
    # Set KIVY_DATA_DIR to the actual location of kivy data files
    kivy_data = os.path.join(base, 'kivy', 'data')
    if os.path.isdir(kivy_data):
        os.environ['KIVY_DATA_DIR'] = kivy_data
    
    # Also set KIVY_MODULES_DIR if needed
    kivy_modules = os.path.join(base, 'kivy', 'modules')
    if os.path.isdir(kivy_modules):
        os.environ['KIVY_MODULES_DIR'] = kivy_modules
