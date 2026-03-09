import os
import sys
import winreg
import tempfile
import subprocess

# Registry Path
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

from core.utils import get_base_dir

def get_executable_path():
    """Lấy đường dẫn đầy đủ đến file chạy (dù là .exe hay script python)"""
    # Nếu chạy bằng file .exe đã build (PyInstaller / auto-py-to-exe)
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}" --minimized'

    # Nếu chạy bằng script python
    base_dir = get_base_dir()
    main_script = os.path.join(base_dir, 'main.py')

    python_exe = sys.executable
    # Sử dụng pythonw.exe nếu có để không hiện console
    if python_exe.endswith("python.exe"):
        pythonw = python_exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            python_exe = pythonw

    return f'"{python_exe}" "{main_script}" --minimized'

def add_to_registry(app_name="KBLightStudio"):
    try:
        command = get_executable_path()
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        return True, "Đã thêm vào Registry thành công."
    except Exception as e:
        return False, str(e)

def remove_from_registry(app_name="KBLightStudio"):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, app_name)
        winreg.CloseKey(key)
        return True, "Đã xóa khỏi Registry."
    except FileNotFoundError:
        return True, "Không tìm thấy trong Registry."
    except Exception as e:
        return False, str(e)

def get_startup_folder_path():
    return os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")

def add_to_startup_folder(app_name="KBLightStudio"):
    startup_dir = get_startup_folder_path()
    shortcut_path = os.path.join(startup_dir, f"{app_name}.lnk")

    base_dir = get_base_dir()

    # Nếu là file .exe (frozen)
    if getattr(sys, 'frozen', False):
        target = sys.executable
        args = "--minimized"
        work_dir = os.path.dirname(sys.executable)
        # Nếu là OneDirectory, icon có thể nằm trong sys._MEIPASS
        icon_path = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else work_dir, "gui", "trayico", "K68.ico")
    else:
        # Nếu là script python
        main_script = os.path.join(base_dir, 'main.py')
        target = sys.executable
        if target.endswith("python.exe"):
            pythonw = target.replace("python.exe", "pythonw.exe")
            if os.path.exists(pythonw):
                target = pythonw
        args = f'"{main_script}" --minimized'
        work_dir = base_dir
        icon_path = os.path.join(work_dir, "gui", "trayico", "K68.ico")

    # Tạo VBScript để tạo shortcut
    vbs_content = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target}"
oLink.Arguments = "{args}"
oLink.WorkingDirectory = "{work_dir}"
oLink.IconLocation = "{icon_path}"
oLink.Save
'''
    vbs_path = os.path.join(tempfile.gettempdir(), "create_shortcut.vbs")
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        os.system(f'cscript //nologo "{vbs_path}"')
        os.remove(vbs_path)
        return True, "Đã tạo Shortcut trong thư mục Startup."
    except Exception as e:
        return False, str(e)
def remove_from_startup_folder(app_name="KBLightStudio"):
    startup_dir = get_startup_folder_path()
    shortcut_path = os.path.join(startup_dir, f"{app_name}.lnk")
    try:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
        return True, "Đã xóa Shortcut khởi động."
    except Exception as e:
        return False, str(e)

def add_to_task_scheduler(app_name="KBLightStudio"):
    """Tạo tác vụ trong Task Scheduler chạy lúc Logon với quyền cao nhất (yêu cầu Admin để cài)"""
    try:
        command = get_executable_path().replace('"', '\\"') # Cần escape quote cho command line
        
        # Lệnh PowerShell để yêu cầu quyền Admin và tạo Scheduled Task
        ps_command = (
            f"Start-Process schtasks -ArgumentList "
            f"'/create /tn \"{app_name}\" /tr \"{command}\" /sc onlogon /rl highest /f' "
            f"-Verb RunAs -WindowStyle Hidden"
        )
        
        result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
        return True, "Đã gửi yêu cầu cấp quyền Admin để cài đặt Task Scheduler.\nVui lòng nhấn 'Yes' ở hộp thoại UAC (nếu có)."
    except Exception as e:
        return False, f"Lỗi tạo Task Scheduler: {e}"

def remove_from_task_scheduler(app_name="KBLightStudio"):
    try:
        ps_command = (
            f"Start-Process schtasks -ArgumentList "
            f"'/delete /tn \"{app_name}\" /f' "
            f"-Verb RunAs -WindowStyle Hidden"
        )
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
        return True, "Đã gửi yêu cầu cấp quyền Admin để xóa Task Scheduler."
    except Exception as e:
        return False, f"Lỗi xóa Task Scheduler: {e}"

def check_status(app_name="KBLightStudio"):
    """Kiểm tra xem app đang được cài đặt khởi động bằng phương thức nào."""
    status = {"registry": False, "startup_folder": False, "task_scheduler": False}
    
    # Check Registry
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        status["registry"] = True
    except FileNotFoundError:
        pass
    except Exception:
        pass
        
    # Check Startup Folder
    startup_dir = get_startup_folder_path()
    shortcut_path = os.path.join(startup_dir, f"{app_name}.lnk")
    if os.path.exists(shortcut_path):
        status["startup_folder"] = True
        
    # Check Task Scheduler
    try:
        # Không yêu cầu quyền admin để Query task
        result = subprocess.run(["schtasks", "/query", "/tn", app_name], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            status["task_scheduler"] = True
    except:
        pass
        
    return status
