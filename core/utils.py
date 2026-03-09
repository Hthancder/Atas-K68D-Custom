import sys
import os

def get_base_dir():
    """
    Returns the absolute path to the directory where the application is running from.
    When running as a python script, it returns the directory of the script.
    When running as a PyInstaller executable (OneDirectory or OneFile), it returns the directory containing the .exe file.
    """
    if getattr(sys, 'frozen', False):
        # The application is frozen (compiled into an executable)
        # sys.executable is the path to the .exe file
        return os.path.dirname(sys.executable)
    else:
        # The application is running as a standard python script
        # __file__ is the path to this module (core/utils.py)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_resource_dir():
    """
    Returns the base directory for accessing bundled resources (like images, json templates).
    When running as a OneFile executable, resources are extracted to a temporary folder (sys._MEIPASS).
    Otherwise, they are in the base directory.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return get_base_dir()
