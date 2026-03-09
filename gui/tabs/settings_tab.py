import customtkinter as ctk
import json
import os
from gui.tabs.base_tab import BaseTab
from gui.tooltip import ToolTip
import core.autostart as autostart

# Đường dẫn gốc là thư mục KBLightStudio (chứa main.py)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
DEFAULT_CONFIG_DIR_NAME = "configSystem"

class SettingsTab(BaseTab):
    def __init__(self, master, usb_driver, **kwargs):
        super().__init__(master, usb_driver, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title = ctk.CTkLabel(self, text=self.master.i18n.t("settings_title"), font=ctk.CTkFont(size=22, weight="bold"))
        self.title.grid(row=0, column=0, padx=30, pady=(30, 15), sticky="w")
        
        self.container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)

        # ------------------- CARD 1: CẤU HÌNH USB -------------------
        self.config_frame = ctk.CTkFrame(self.container, fg_color="#252525", corner_radius=12)
        self.config_frame.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="nsew")
        self.config_frame.grid_columnconfigure(1, weight=1)
        
        # --- Cấu hình USB ---
        ctk.CTkLabel(self.config_frame, text=self.master.i18n.t("settings_vid")).grid(row=0, column=0, padx=25, pady=(25, 10), sticky="w")
        self.vid_entry = ctk.CTkEntry(self.config_frame, height=35)
        self.vid_entry.grid(row=0, column=1, padx=25, pady=(25, 10), sticky="ew")
        self.vid_entry.insert(0, "0x5566")
        
        ctk.CTkLabel(self.config_frame, text=self.master.i18n.t("settings_pid")).grid(row=1, column=0, padx=25, pady=10, sticky="w")
        self.pid_entry = ctk.CTkEntry(self.config_frame, height=35)
        self.pid_entry.grid(row=1, column=1, padx=25, pady=10, sticky="ew")
        self.pid_entry.insert(0, "0x000A")
        
        # --- Cấu hình thư mục lưu trữ ---
        ctk.CTkLabel(self.config_frame, text=self.master.i18n.t("settings_config_dir")).grid(row=2, column=0, padx=25, pady=10, sticky="w")
        self.config_dir_entry = ctk.CTkEntry(self.config_frame, placeholder_text=DEFAULT_CONFIG_DIR_NAME, height=35)
        self.config_dir_entry.grid(row=2, column=1, padx=25, pady=10, sticky="ew")
        
        # --- Cấu hình USB Delay ---
        self.delay_label_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.delay_label_frame.grid(row=3, column=0, padx=25, pady=10, sticky="w")
        ctk.CTkLabel(self.delay_label_frame, text=self.master.i18n.t("settings_delay")).pack(side="left")
        self.delay_val_label = ctk.CTkLabel(self.delay_label_frame, text="0.010s", text_color="#00f2ff", font=ctk.CTkFont(weight="bold"))
        self.delay_val_label.pack(side="left", padx=5)
        
        self.usb_delay_slider = ctk.CTkSlider(self.config_frame, from_=0.0, to=0.05, number_of_steps=50, command=self.on_delay_slider_change, button_color="#00f2ff")
        self.usb_delay_slider.set(0.01) # Mặc định 0.01s
        self.usb_delay_slider.grid(row=3, column=1, padx=25, pady=10, sticky="ew")
        
        # --- Cấu hình Thông báo ---
        self.notify_var = ctk.BooleanVar(value=True)
        self.notify_switch = ctk.CTkSwitch(self.config_frame, text=self.master.i18n.t("settings_notify"), variable=self.notify_var, progress_color="#00f2ff")
        self.notify_switch.grid(row=4, column=0, columnspan=2, padx=25, pady=(10, 5), sticky="w")
        
        # --- Cấu hình Thu nhỏ vào khay ---
        self.tray_pref_var = ctk.BooleanVar(value=True)
        self.tray_pref_switch = ctk.CTkSwitch(self.config_frame, text=self.master.i18n.t("settings_minimize"), variable=self.tray_pref_var, progress_color="#00f2ff")
        self.tray_pref_switch.grid(row=5, column=0, columnspan=2, padx=25, pady=(5, 10), sticky="w")

        # Nút bấm
        self.btn_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, columnspan=2, padx=25, pady=(10, 25), sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.save_settings_btn = ctk.CTkButton(self.btn_frame, text=self.master.i18n.t("settings_btn_save"), command=self.save_app_settings, fg_color="#28a745", hover_color="#218838", height=40, font=ctk.CTkFont(weight="bold"))
        self.save_settings_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.auto_btn = ctk.CTkButton(self.btn_frame, text=self.master.i18n.t("settings_btn_test_usb"), command=self.auto_connect, height=40, font=ctk.CTkFont(weight="bold"))
        self.auto_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.reset_btn = ctk.CTkButton(self.btn_frame, text=self.master.i18n.t("settings_btn_reset"), command=self.reset_all_settings, fg_color="#882222", hover_color="#aa3333", height=35)
        self.reset_btn.grid(row=1, column=0, columnspan=2, padx=0, pady=(15, 0), sticky="ew")
        
        # ------------------- CARD 2: AUTO START -------------------
        self.startup_frame = ctk.CTkFrame(self.container, fg_color="#252525", corner_radius=12)
        self.startup_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.startup_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.startup_frame, text=self.master.i18n.t("settings_autostart_title"), font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, columnspan=2, padx=25, pady=(25, 10), sticky="w")
        
        self.startup_method_var = ctk.StringVar(value=self.master.i18n.t("settings_autostart_reg"))
        self.startup_methods = {
            self.master.i18n.t("settings_autostart_reg"): "registry",
            self.master.i18n.t("settings_autostart_folder"): "startup_folder",
            self.master.i18n.t("settings_autostart_task"): "task_scheduler"
        }
        
        # Row 1: Method Selection
        ctk.CTkLabel(self.startup_frame, text=self.master.i18n.t("settings_autostart_method")).grid(row=1, column=0, padx=25, pady=10, sticky="w")
        self.startup_menu = ctk.CTkOptionMenu(self.startup_frame, values=list(self.startup_methods.keys()), variable=self.startup_method_var, height=35, command=self.update_autostart_ui_state)
        self.startup_menu.grid(row=1, column=1, padx=25, pady=10, sticky="ew")

        # Row 2: Status Indicator
        self.startup_status_lbl = ctk.CTkLabel(self.startup_frame, text=self.master.i18n.t("settings_autostart_status_checking"), text_color="gray", font=ctk.CTkFont(weight="bold"))
        self.startup_status_lbl.grid(row=2, column=0, columnspan=2, padx=25, pady=5, sticky="w")

        # Row 3: Minimize to tray on autostart toggle
        self.autostart_minimized_var = ctk.BooleanVar(value=True)
        self.autostart_minimized_switch = ctk.CTkSwitch(self.startup_frame, text=self.master.i18n.t("settings_autostart_minimized"), variable=self.autostart_minimized_var, progress_color="#00f2ff")
        self.autostart_minimized_switch.grid(row=3, column=0, columnspan=2, padx=25, pady=5, sticky="w")

        # Row 4: Action Buttons
        self.startup_btn_frame = ctk.CTkFrame(self.startup_frame, fg_color="transparent")
        self.startup_btn_frame.grid(row=4, column=0, columnspan=2, padx=25, pady=(15, 25), sticky="ew")
        self.startup_btn_frame.grid_columnconfigure(0, weight=1)

        self.install_startup_btn = ctk.CTkButton(self.startup_btn_frame, text=self.master.i18n.t("settings_btn_install_autostart"), command=self.install_autostart, height=40, font=ctk.CTkFont(weight="bold"))
        self.install_startup_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.uninstall_startup_btn = ctk.CTkButton(self.startup_btn_frame, text=self.master.i18n.t("settings_btn_uninstall_autostart"), command=self.uninstall_autostart, fg_color="transparent", border_width=1, border_color="#882222", text_color="#ff5555", hover_color="#331111", height=40, width=130)
        self.uninstall_startup_btn.grid(row=0, column=1, padx=(10, 0), sticky="e")

        # ------------------- STATUS -------------------
        self.status = ctk.CTkLabel(self, text=self.master.i18n.t("settings_status_ready"), text_color="orange")
        self.status.grid(row=2, column=0, padx=30, pady=(0, 15), sticky="w")
        
        # --- Tooltips ---
        ToolTip(self.vid_entry, "Mã Vendor ID của bàn phím. Mặc định là 0x5566.")
        ToolTip(self.pid_entry, "Mã Product ID của bàn phím. Mặc định là 0x000A.")
        ToolTip(self.config_dir_entry, "Thư mục lưu các file config (VD: static_config.json).\nNên để đường dẫn tương đối (VD: configSystem).")
        ToolTip(self.usb_delay_slider, "Độ trễ giữa mỗi lần gửi gói tin USB. Mặc định 0.01s. Tăng lên nếu bị lỗi mất kết nối.")
        ToolTip(self.startup_menu, "Chọn cách Windows khởi động phần mềm.\n- Registry: Nhanh, chuẩn nhưng dễ bị Antivirus soi.\n- Startup Folder: Tạo shortcut rõ ràng.\n- Task Scheduler: Chạy ngầm mạnh nhất, vượt cảnh báo UAC (Cần cấp quyền Admin lúc cài).")
        
        self.active_autostart_methods = []
        self.load_app_settings()
        self.check_autostart_status()

    def check_autostart_status(self):
        status = autostart.check_status()
        self.active_autostart_methods = []
        installed_names = []
        
        if status["registry"]: 
            self.active_autostart_methods.append("registry")
            installed_names.append("Registry")
        if status["startup_folder"]: 
            self.active_autostart_methods.append("startup_folder")
            installed_names.append("Startup Folder")
        if status.get("task_scheduler"): 
            self.active_autostart_methods.append("task_scheduler")
            installed_names.append("Task Scheduler")
        
        if installed_names:
            self.startup_status_lbl.configure(text=f"{self.master.i18n.t('settings_autostart_status_running')}{', '.join(installed_names)}", text_color="#00f2ff")
            self.uninstall_startup_btn.grid(row=0, column=1, padx=(10, 0), sticky="e")
        else:
            self.startup_status_lbl.configure(text=self.master.i18n.t("settings_autostart_status_none"), text_color="gray")
            self.uninstall_startup_btn.grid_forget()
            
        self.update_autostart_ui_state()

    def update_autostart_ui_state(self, *args):
        selected_name = self.startup_method_var.get()
        selected_id = self.startup_methods.get(selected_name)
        
        if selected_id in self.active_autostart_methods:
            # Phương thức đang chọn đã được cài đặt
            self.install_startup_btn.configure(
                text=self.master.i18n.t("settings_autostart_installed"), 
                fg_color="#333333", 
                text_color="gray",
                hover_color="#333333", 
                state="disabled"
            )
        else:
            # Phương thức đang chọn chưa cài đặt
            self.install_startup_btn.configure(state="normal")
            if self.active_autostart_methods:
                self.install_startup_btn.configure(
                    text=self.master.i18n.t("settings_autostart_switch"), 
                    fg_color="#0055ff", 
                    text_color="white",
                    hover_color="#0044cc"
                )
            else:
                self.install_startup_btn.configure(
                    text=self.master.i18n.t("settings_btn_install_autostart"), 
                    fg_color="#28a745", 
                    text_color="white",
                    hover_color="#218838"
                )


    def install_autostart(self):
        method_name = self.startup_method_var.get()
        method_id = self.startup_methods[method_name]
        
        # 1. Gỡ bỏ các phương thức cũ để tránh xung đột (mở app nhiều lần)
        autostart.remove_from_registry()
        autostart.remove_from_startup_folder()
        autostart.remove_from_task_scheduler()
        
        # 2. Cài đặt phương thức mới
        if method_id == "registry":
            success, msg = autostart.add_to_registry()
        elif method_id == "task_scheduler":
            success, msg = autostart.add_to_task_scheduler()
        else:
            success, msg = autostart.add_to_startup_folder()
            
        if success:
            self.status.configure(text=f"Khởi động cùng hệ thống: {msg}", text_color="green")
        else:
            self.status.configure(text=f"Lỗi: {msg}", text_color="red")
        
        # Trì hoãn việc kiểm tra lại trạng thái để Task Scheduler kịp cập nhật
        self.after(2000, self.check_autostart_status)

    def uninstall_autostart(self):
        from tkinter import messagebox
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn tắt tính năng khởi động cùng hệ thống không?"):
            return
            
        # Luôn cố gắng xóa ở tất cả các nơi để sạch sẽ
        success_reg, msg_reg = autostart.remove_from_registry()
        success_folder, msg_folder = autostart.remove_from_startup_folder()
        success_task, msg_task = autostart.remove_from_task_scheduler()
        
        self.status.configure(text="Đã gửi lệnh gỡ bỏ khởi động cùng hệ thống.", text_color="green")
        self.after(2000, self.check_autostart_status)

    def reset_all_settings(self):
        """Xóa toàn bộ file cấu hình và đưa app về trạng thái ban đầu."""
        from tkinter import messagebox
        
        confirm = messagebox.askyesno(
            "Xác nhận Reset", 
            "Bạn có chắc chắn muốn XÓA TOÀN BỘ cài đặt (bao gồm màu sắc, hiệu ứng âm thanh và cấu hình hệ thống)?\n\nThao tác này không thể hoàn tác!"
        )
        
        if confirm:
            try:
                # 1. Tìm đường dẫn config hiện tại để xóa
                config_dir = self.config_dir_entry.get().strip() or DEFAULT_CONFIG_DIR_NAME
                full_config_path = config_dir if os.path.isabs(config_dir) else os.path.join(BASE_DIR, config_dir)
                
                # 2. Danh sách các file cần xóa
                files_to_delete = [
                    SETTINGS_FILE,
                    os.path.join(full_config_path, "static_config.json"),
                    os.path.join(full_config_path, "audio_config.json")
                ]
                
                deleted_count = 0
                for f_path in files_to_delete:
                    if os.path.exists(f_path):
                        os.remove(f_path)
                        deleted_count += 1
                
                self.append_log(f"Đã xóa {deleted_count} file cấu hình.")
                
                # 3. Reset UI về mặc định
                self.vid_entry.delete(0, 'end'); self.vid_entry.insert(0, "0x5566")
                self.pid_entry.delete(0, 'end'); self.pid_entry.insert(0, "0x000A")
                self.config_dir_entry.delete(0, 'end'); self.config_dir_entry.insert(0, DEFAULT_CONFIG_DIR_NAME)
                self.usb_delay_slider.set(0.01)
                self.delay_val_label.configure(text="0.010s")
                self.usb_driver.delay_time = 0.01
                
                self.status.configure(text="Đã Reset toàn bộ cài đặt!", text_color="green")
                messagebox.showinfo("Thành công", "Đã khôi phục cài đặt mặc định. Vui lòng khởi động lại ứng dụng để các tab khác cập nhật hoàn toàn.")
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể reset cài đặt: {e}")

    def load_app_settings(self):
        """Tải settings.json từ thư mục script."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                config_dir = settings.get("config_directory", DEFAULT_CONFIG_DIR_NAME)
                self.config_dir_entry.delete(0, 'end')
                self.config_dir_entry.insert(0, config_dir)
                
                # Load USB Delay
                usb_delay = settings.get("usb_delay", 0.01)
                self.usb_delay_slider.set(usb_delay)
                self.delay_val_label.configure(text=f"{usb_delay:.3f}s")
                self.usb_driver.delay_time = usb_delay

                # Load Notification pref
                self.notify_var.set(settings.get("show_tray_notification", True))
                
                # Load Minimize to tray pref
                self.tray_pref_var.set(settings.get("minimize_to_tray", True))
                
                # Load autostart minimized pref
                self.autostart_minimized_var.set(settings.get("autostart_minimized", True))
                
                # Load VID PID
                saved_vid = settings.get("target_vid", 0x5566)
                saved_pid = settings.get("target_pid", 0x000A)
                self.vid_entry.delete(0, 'end'); self.vid_entry.insert(0, hex(saved_vid))
                self.pid_entry.delete(0, 'end'); self.pid_entry.insert(0, hex(saved_pid))
                
                self.status.configure(text="Đã tải cài đặt hệ thống.", text_color="gray")
            else:
                self.config_dir_entry.insert(0, DEFAULT_CONFIG_DIR_NAME)
                self.usb_driver.delay_time = 0.01
                self.vid_entry.insert(0, "0x5566")
                self.pid_entry.insert(0, "0x000A")
        except Exception as e:
            self.usb_driver.log(f"Lỗi tải settings: {e}")

    def save_app_settings(self):
        """Lưu đường dẫn cấu hình và các thông số khác vào settings.json."""
        config_dir = self.config_dir_entry.get().strip() or DEFAULT_CONFIG_DIR_NAME
        usb_delay = float(self.usb_delay_slider.get())
        show_notify = self.notify_var.get()
        minimize_to_tray = self.tray_pref_var.get()
        autostart_minimized = self.autostart_minimized_var.get()
        
        try:
            target_vid = int(self.vid_entry.get(), 16)
            target_pid = int(self.pid_entry.get(), 16)
        except ValueError:
            self.status.configure(text="Lỗi định dạng VID/PID. Phải là mã Hex (VD: 0x5566)", text_color="red")
            return
            
        try:
            settings = {
                "config_directory": config_dir,
                "usb_delay": usb_delay,
                "show_tray_notification": show_notify,
                "minimize_to_tray": minimize_to_tray,
                "autostart_minimized": autostart_minimized,
                "target_vid": target_vid,
                "target_pid": target_pid
            }
            # Sử dụng hàm save từ app để đồng bộ
            self.master.save_all_settings(settings)
            
            # Cập nhật ngay vào usb_driver
            self.usb_driver.delay_time = usb_delay
            # Cập nhật biến thông báo và thu nhỏ của app chính
            self.master.show_tray_notification = show_notify
            self.master.minimize_to_tray_pref = minimize_to_tray
            
            # Tạo thư mục nếu chưa có (tương đối so với script)
            full_path = config_dir if os.path.isabs(config_dir) else os.path.join(BASE_DIR, config_dir)
            os.makedirs(full_path, exist_ok=True)
            
            self.status.configure(text=f"Đã lưu cài đặt hệ thống!", text_color="green")
        except Exception as e:
            self.status.configure(text=f"Lỗi khi lưu: {e}", text_color="red")

    def on_delay_slider_change(self, value):
        self.delay_val_label.configure(text=f"{value:.3f}s")

    def auto_connect(self):
        try:
            vid = int(self.vid_entry.get(), 16)
            pid = int(self.pid_entry.get(), 16)
            self.usb_driver.log(f"\n--- THỬ KẾT NỐI VID:{hex(vid)} PID:{hex(pid)} ---")
            success, msg = self.usb_driver.auto_detect_and_connect(vid, pid)
            self.usb_driver.log(msg)
            if success: self.status.configure(text="USB: Đã kết nối", text_color="green")
            else: self.status.configure(text="USB: Thất bại", text_color="red")
        except: self.status.configure(text="Lỗi định dạng VID/PID", text_color="red")
