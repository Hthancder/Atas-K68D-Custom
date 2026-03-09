import customtkinter as ctk
import tkcolorpicker
import json
import os
from gui.tabs.base_tab import BaseTab
from gui.tooltip import ToolTip
from core.protocol import MODES
from core.utils import get_base_dir

# --- Configuration Directory Setup ---
# Đường dẫn gốc là thư mục Atas-K68D-Custom (chứa main.py)
BASE_DIR = get_base_dir()
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def get_config_file_path():
    default_config_dir_name = "configSystem"
    config_dir = os.path.join(BASE_DIR, default_config_dir_name)
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                saved_dir = settings.get("config_directory", default_config_dir_name)
                # Nếu đường dẫn là tương đối, nối nó với BASE_DIR
                if not os.path.isabs(saved_dir):
                    config_dir = os.path.join(BASE_DIR, saved_dir)
                else:
                    config_dir = saved_dir
    except Exception:
        pass 
    
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "static_config.json")

class StaticTab(BaseTab):
    def __init__(self, master, usb_driver, **kwargs):
        super().__init__(master, usb_driver, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title = ctk.CTkLabel(self, text=self.master.i18n.t("static_title"), font=ctk.CTkFont(size=22, weight="bold"))
        self.title.grid(row=0, column=0, padx=30, pady=(30, 15), sticky="w")
        
        # Main Scrollable or content frame
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)

        # --- Configuration Card ---
        self.config_frame = ctk.CTkFrame(self.container, fg_color="#252525", corner_radius=12)
        self.config_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.config_frame.grid_columnconfigure(1, weight=1)
        
        # --- Chế độ ---
        ctk.CTkLabel(self.config_frame, text=self.master.i18n.t("static_mode_label")).grid(row=0, column=0, padx=25, pady=(25, 10), sticky="w")
        self.mode_var = ctk.StringVar(value=self.get_localized_mode_name("Fixed / Static"))
        self.mode_menu = ctk.CTkOptionMenu(
            self.config_frame, 
            values=list(self.get_localized_modes().keys()),
            variable=self.mode_var,
            command=self.on_mode_change,
            height=35
        )
        self.mode_menu.grid(row=0, column=1, padx=25, pady=(25, 10), sticky="ew")
        
        # --- Màu sắc ---
        ctk.CTkLabel(self.config_frame, text=self.master.i18n.t("static_color_label")).grid(row=1, column=0, padx=25, pady=10, sticky="w")
        self.color_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.color_frame.grid(row=1, column=1, padx=25, pady=10, sticky="ew")
        self.color_frame.grid_columnconfigure((0,1,2), weight=1)
        
        entry_style = {"height": 35, "corner_radius": 6}
        self.r_entry = ctk.CTkEntry(self.color_frame, placeholder_text="R", **entry_style)
        self.r_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.r_entry.insert(0, "0")
        self.r_entry.bind("<KeyRelease>", self.on_color_input_change)
        
        self.g_entry = ctk.CTkEntry(self.color_frame, placeholder_text="G", **entry_style)
        self.g_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.g_entry.insert(0, "255")
        self.g_entry.bind("<KeyRelease>", self.on_color_input_change)
        
        self.b_entry = ctk.CTkEntry(self.color_frame, placeholder_text="B", **entry_style)
        self.b_entry.grid(row=0, column=2, padx=(5, 5), sticky="ew")
        self.b_entry.insert(0, "255")
        self.b_entry.bind("<KeyRelease>", self.on_color_input_change)

        self.color_btn = ctk.CTkButton(self.color_frame, text="🎨", width=40, height=35, command=self.choose_color)
        self.color_btn.grid(row=0, column=3, sticky="e")
        
        # --- Độ sáng ---
        self.bright_label_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.bright_label_frame.grid(row=2, column=0, padx=25, pady=10, sticky="w")
        ctk.CTkLabel(self.bright_label_frame, text=self.master.i18n.t("static_bright_label")).pack(side="left")
        self.bright_val_label = ctk.CTkLabel(self.bright_label_frame, text="255", text_color="#00f2ff", font=ctk.CTkFont(weight="bold"))
        self.bright_val_label.pack(side="left", padx=5)
        
        self.bright_slider = ctk.CTkSlider(self.config_frame, from_=0, to=255, number_of_steps=255, command=self.on_generic_change, button_color="#00f2ff", button_hover_color="#00c8d4")
        self.bright_slider.set(255)
        self.bright_slider.grid(row=2, column=1, padx=25, pady=10, sticky="ew")

        # --- Tốc độ ---
        self.speed_label_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.speed_label_frame.grid(row=3, column=0, padx=25, pady=10, sticky="w")
        ctk.CTkLabel(self.speed_label_frame, text=self.master.i18n.t("static_speed_label")).pack(side="left")
        self.speed_val_label = ctk.CTkLabel(self.speed_label_frame, text="4", text_color="#00f2ff", font=ctk.CTkFont(weight="bold"))
        self.speed_val_label.pack(side="left", padx=5)
        
        self.speed_slider = ctk.CTkSlider(self.config_frame, from_=1, to=4, number_of_steps=3, command=self.on_generic_change, button_color="#00f2ff", button_hover_color="#00c8d4")
        self.speed_slider.set(4)
        self.speed_slider.grid(row=3, column=1, padx=25, pady=10, sticky="ew")
        
        # --- Đổi màu tự động ---
        self.auto_color_var = ctk.BooleanVar(value=True)
        self.auto_color_switch = ctk.CTkSwitch(
            self.config_frame, 
            text=self.master.i18n.t("static_auto_color"), 
            variable=self.auto_color_var,
            command=self.on_generic_change,
            progress_color="#00f2ff"
        )
        self.auto_color_switch.grid(row=4, column=0, columnspan=2, padx=25, pady=(15, 25), sticky="w")
        ToolTip(self.auto_color_switch, "Tắt chức năng này nếu bạn muốn hiển thị màu đơn sắc (Static) do bạn tự chọn.")

        # --- Nút Áp dụng & Realtime ---
        self.apply_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.apply_frame.grid(row=1, column=0, padx=0, pady=20, sticky="ew")
        self.apply_frame.grid_columnconfigure(0, weight=1)

        self.apply_btn = ctk.CTkButton(self.apply_frame, text=self.master.i18n.t("static_btn_apply"), command=self.apply_mode, height=45, corner_radius=10, font=ctk.CTkFont(weight="bold"), fg_color="#0055ff", hover_color="#0044cc")
        self.apply_btn.grid(row=0, column=0, padx=(0, 15), sticky="ew")
        ToolTip(self.apply_btn, "Nhấn để gửi tín hiệu tới bàn phím. Không cần nhấn nếu đã bật 'Tự động áp dụng'.")

        self.realtime_var = ctk.BooleanVar(value=True)
        self.realtime_switch = ctk.CTkSwitch(self.apply_frame, text=self.master.i18n.t("static_realtime"), variable=self.realtime_var, progress_color="#00f2ff")
        self.realtime_switch.grid(row=0, column=1, sticky="e")
        ToolTip(self.realtime_switch, "Gửi tín hiệu ngay lập tức mỗi khi bạn thay đổi thông số trên giao diện.")
        
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="w")
        
        # Thêm Tooltips cho các Widget khác
        ToolTip(self.mode_menu, "Chọn chế độ LED phát sáng từ danh sách.")
        ToolTip(self.color_btn, "Mở bảng màu trực quan để chọn nhanh màu sắc.")
        ToolTip(self.bright_slider, "Thay đổi độ sáng đèn nền LED. 0 là tắt hẳn, 255 là sáng nhất.")
        ToolTip(self.speed_slider, "Điều chỉnh tốc độ hiệu ứng: 1 (Chậm nhất) đến 4 (Nhanh nhất).")

        self.load_config()

    def load_config(self):
        try:
            config_file = get_config_file_path()
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.mode_var.set(self.get_localized_mode_name(config.get("mode", "Fixed / Static")))
                
                r, g, b = config.get("r", 0), config.get("g", 255), config.get("b", 255)
                self.r_entry.delete(0, 'end'); self.r_entry.insert(0, str(r))
                self.g_entry.delete(0, 'end'); self.g_entry.insert(0, str(g))
                self.b_entry.delete(0, 'end'); self.b_entry.insert(0, str(b))

                self.bright_slider.set(config.get("brightness", 255))
                ui_speed = 5 - config.get("speed", 1)
                self.speed_slider.set(ui_speed)

                self.auto_color_var.set(config.get("auto_color", True))
                self.realtime_var.set(config.get("realtime_apply", True))
                
                # Cập nhật nhãn thông số
                self.bright_val_label.configure(text=str(int(self.bright_slider.get())))
                self.speed_val_label.configure(text=str(int(self.speed_slider.get())))

                self.status_label.configure(text="Cấu hình đã tải.", text_color="gray")
            else:
                self.status_label.configure(text="Dùng cấu hình mặc định.", text_color="gray")
        except Exception as e:
            self.status_label.configure(text=f"Lỗi load config: {e}", text_color="red")
            print(f"[StaticTab] Lỗi load_config: {e}")
        finally:
            self.after(200, self.apply_mode)
            self.after(400, self.apply_mode)

    def save_config(self):
        try:
            ui_speed = int(self.speed_slider.get())
            config = {
                "mode": self.get_original_name_from_localized(self.mode_var.get()),
                "r": int(self.r_entry.get() or 0),
                "g": int(self.g_entry.get() or 0),
                "b": int(self.b_entry.get() or 0),
                "brightness": int(self.bright_slider.get()),
                "speed": 5 - ui_speed,
                "auto_color": self.auto_color_var.get(),
                "realtime_apply": self.realtime_var.get()
            }
            config_file = get_config_file_path()
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"[StaticTab] Lỗi save_config: {e}")

    def choose_color(self):
        try:
            curr_r = int(self.r_entry.get() or 0)
            curr_g = int(self.g_entry.get() or 0)
            curr_b = int(self.b_entry.get() or 0)
        except: curr_r, curr_g, curr_b = 255, 255, 255
            
        picker = tkcolorpicker.ColorPicker(self, color=(curr_r, curr_g, curr_b), title="Chọn màu LED")
        
        def on_picker_change(*args):
            try:
                r, g, b = picker.red.get(), picker.green.get(), picker.blue.get()
                self.r_entry.delete(0, 'end'); self.r_entry.insert(0, str(r))
                self.g_entry.delete(0, 'end'); self.g_entry.insert(0, str(g))
                self.b_entry.delete(0, 'end'); self.b_entry.insert(0, str(b))
                self.auto_color_var.set(False)
                self.trigger_apply()
            except: pass

        picker.red.trace_add("write", on_picker_change)
        picker.green.trace_add("write", on_picker_change)
        picker.blue.trace_add("write", on_picker_change)
        self.wait_window(picker)

    def on_show(self):
        """Khi chuyển lại tab Static, tự động ép cấu hình xuống bàn phím (nếu đang bật Tự động)."""
        if hasattr(self, 'realtime_var') and self.realtime_var.get():
            self.trigger_apply()

    def on_mode_change(self, choice):
        self.mode_var.set(choice)
        if self.realtime_var.get():
            self.after(20, self.apply_mode)
            self.after(250, self.apply_mode)

    def on_color_input_change(self, event):
        self.auto_color_var.set(False)
        self.trigger_apply()

    def on_generic_change(self, *args):
        self.bright_val_label.configure(text=str(int(self.bright_slider.get())))
        self.speed_val_label.configure(text=str(int(self.speed_slider.get())))
        self.trigger_apply()

    def trigger_apply(self):
        if self.realtime_var.get():
            if hasattr(self, 'apply_timer'):
                self.after_cancel(self.apply_timer)
            self.apply_timer = self.after(50, self.apply_mode)

    def apply_mode(self):
        try:
            mode_name = self.mode_var.get()
            mode_hex = self.get_hex_from_localized_name(mode_name)
            r = max(0, min(255, int(self.r_entry.get() or 0)))
            g = max(0, min(255, int(self.g_entry.get() or 0)))
            b = max(0, min(255, int(self.b_entry.get() or 0)))
            brightness = int(self.bright_slider.get())
            real_speed = 5 - int(self.speed_slider.get())
            auto_color = self.auto_color_var.get()

            self.usb_driver.apply_mode(mode_hex, (r, g, b), brightness, real_speed, auto_color)
            self.status_label.configure(text=f"Đã áp dụng: {mode_name}", text_color="green")
            
            # Debounce the file save operation to prevent excessive disk I/O when sliding
            if hasattr(self, 'save_timer') and self.save_timer is not None:
                self.after_cancel(self.save_timer)
            self.save_timer = self.after(1000, self.save_config)
            
        except Exception as e:
            self.status_label.configure(text=f"Lỗi: {e}", text_color="red")