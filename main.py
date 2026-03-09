import sys
import os
import json

# Fix for double-click running (when python/pythonw is used without a proper console)
class DummyWriter:
    def write(self, x): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = DummyWriter()
if sys.stderr is None:
    sys.stderr = DummyWriter()

from core.utils import get_base_dir
# Đảm bảo có thể import các module bên trong thư mục (chỉ cần thiết khi chạy từ mã nguồn)
sys.path.insert(0, get_base_dir())

from gui.app import KBLightStudioApp
from core.usb_driver import USBDriver

def main():
    print("Khởi động Atas-K68D-Custom...")
    
    target_vid = 0x5566
    target_pid = 0x000A
    
    # Đọc cấu hình VID/PID từ file
    settings_path = os.path.join(get_base_dir(), "settings.json")
    try:
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                target_vid = settings.get("target_vid", 0x5566)
                target_pid = settings.get("target_pid", 0x000A)
    except Exception as e:
        print(f"Lỗi đọc settings.json: {e}")
    
    # Khởi tạo USB Driver với VID/PID đã cấu hình
    usb_driver = USBDriver(vid=target_vid, pid=target_pid) 
    
    print(f"Đang tự động tìm kiếm và kết nối bàn phím (VID:{hex(target_vid)} PID:{hex(target_pid)})...")
    usb_driver.auto_detect_and_connect(target_vid=target_vid, target_pid=target_pid)
    
    # Khởi tạo và chạy GUI chính
    app = KBLightStudioApp(usb_driver)
    
    # Kiểm tra tham số chạy ngầm (Auto-start)
    if "--minimized" in sys.argv:
        # Kiểm tra xem người dùng có cho phép khởi động thu nhỏ hay không
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                start_minimized = settings.get("autostart_minimized", True)
        except:
            start_minimized = True
            
        if start_minimized:
            print("[System] Chạy ở chế độ thu nhỏ (Auto-start)")
            app.after(100, app.minimize_to_tray) # Đợi một chút để UI khởi tạo xong rồi thu nhỏ
        
    app.mainloop()

if __name__ == "__main__":
    main()
