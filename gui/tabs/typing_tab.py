import customtkinter as ctk
import tkcolorpicker
import os
import json
from gui.tabs.base_tab import BaseTab
from gui.tooltip import ToolTip
from core.protocol import MODES
from effects.typing_monitor import TypingMonitor

# --- Configuration Directory Setup ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def get_typing_config_path():
    default_config_dir_name = "configSystem"
    config_dir = os.path.join(BASE_DIR, default_config_dir_name)
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                saved_dir = settings.get("config_directory", default_config_dir_name)
                if not os.path.isabs(saved_dir):
                    config_dir = os.path.join(BASE_DIR, saved_dir)
                else:
                    config_dir = saved_dir
    except: pass
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "typing_config.json")

class TypingTab(BaseTab):
    def __init__(self, master, usb_driver, **kwargs):
        super().__init__(master, usb_driver, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Tiêu đề
        self.title = ctk.CTkLabel(self, text=self.master.i18n.t("typing_title"), font=ctk.CTkFont(size=22, weight="bold"))
        self.title.grid(row=0, column=0, padx=30, pady=(30, 15), sticky="w")
        
        # Main Scrollable Frame để chứa nhiều tuỳ chọn
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Display WPM Card
        self.wpm_display_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.wpm_display_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.wpm_label = ctk.CTkLabel(self.wpm_display_frame, text="0", font=ctk.CTkFont(size=72, weight="bold", family="Consolas"), text_color="#00f2ff")
        self.wpm_label.pack(pady=(20, 5))
        ctk.CTkLabel(self.wpm_display_frame, text=self.master.i18n.t("typing_wpm_title"), font=ctk.CTkFont(weight="bold", size=12)).pack(pady=(0, 20))

        # --- Settings Card ---
        self.settings_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.settings_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure(1, weight=1)

        # Chế độ nền
        ctk.CTkLabel(self.settings_frame, text=self.master.i18n.t("typing_mode_label")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.mode_var = ctk.StringVar(value=self.get_localized_mode_name("Fixed / Static"))
        self.mode_menu = ctk.CTkOptionMenu(self.settings_frame, values=list(self.get_localized_modes().keys()), variable=self.mode_var, command=self.update_monitor_config, height=35)
        self.mode_menu.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="ew")

        # Tốc độ phản hồi
        ctk.CTkLabel(self.settings_frame, text=self.master.i18n.t("typing_decay_label")).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.decay_slider = ctk.CTkSlider(self.settings_frame, from_=0.1, to=2.0, command=self.update_monitor_config, button_color="#00f2ff")
        self.decay_slider.set(0.5)
        self.decay_slider.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        # Độ sáng Max
        ctk.CTkLabel(self.settings_frame, text=self.master.i18n.t("typing_bright_label")).grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.bright_slider = ctk.CTkSlider(self.settings_frame, from_=50, to=255, number_of_steps=205, command=self.update_monitor_config, button_color="#00f2ff")
        self.bright_slider.set(255)
        self.bright_slider.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        
        # --- Đổi màu tự động (Auto Color / RGB) ---
        self.auto_color_var = ctk.BooleanVar(value=False)
        self.auto_color_switch = ctk.CTkSwitch(
            self.settings_frame, 
            text=self.master.i18n.t("typing_auto_color_label"), 
            variable=self.auto_color_var,
            command=self.update_monitor_config,
            progress_color="#00f2ff"
        )
        self.auto_color_switch.grid(row=3, column=0, columnspan=2, padx=20, pady=(5, 20), sticky="w")
        
        # --- Khung chọn màu theo WPM Card ---
        self.color_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.color_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.color_low = (0, 255, 255) # Cyan
        self.color_mid = (255, 255, 0) # Yellow
        self.color_high = (255, 0, 0) # Red

        btn_style = {"height": 40, "corner_radius": 8, "font": ctk.CTkFont(weight="bold")}
        self.btn_low = ctk.CTkButton(self.color_frame, text=self.master.i18n.t("typing_speed_low"), fg_color="#00ffff", text_color="black", hover_color="#00cccc", command=lambda: self.pick_color("low"), **btn_style)
        self.btn_low.grid(row=1, column=0, padx=(20, 5), pady=(0, 20), sticky="ew")
        
        self.btn_mid = ctk.CTkButton(self.color_frame, text=self.master.i18n.t("typing_speed_mid"), fg_color="#ffff00", text_color="black", hover_color="#cccc00", command=lambda: self.pick_color("mid"), **btn_style)
        self.btn_mid.grid(row=1, column=1, padx=5, pady=(0, 20), sticky="ew")
        
        self.btn_high = ctk.CTkButton(self.color_frame, text=self.master.i18n.t("typing_speed_high"), fg_color="#ff0000", hover_color="#cc0000", command=lambda: self.pick_color("high"), **btn_style)
        self.btn_high.grid(row=1, column=2, padx=(5, 20), pady=(0, 20), sticky="ew")

        self.color_frame.grid_columnconfigure((0,1,2), weight=1)

        # Nút Bật/Tắt
        self.is_running = False
        self.toggle_btn = ctk.CTkButton(self.scroll_frame, text=self.master.i18n.t("typing_btn_start"), command=self.toggle_typing, height=50, font=ctk.CTkFont(weight="bold"), fg_color="#28a745", hover_color="#218838", corner_radius=10)
        self.toggle_btn.grid(row=3, column=0, padx=10, pady=20, sticky="ew")
        ToolTip(self.toggle_btn, "Kích hoạt chức năng theo dõi tốc độ gõ bàn phím.\nCần cấp quyền theo dõi phím (Keylogger) nếu hệ thống yêu cầu.")
        ToolTip(self.toggle_btn, "Kích hoạt chức năng theo dõi tốc độ gõ bàn phím.\nCần cấp quyền theo dõi phím (Keylogger) nếu hệ thống yêu cầu.")
        
        self.load_config()

    def load_config(self):
        try:
            config_file = get_typing_config_path()
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.mode_var.set(self.get_localized_mode_name(config.get("mode_name", "Fixed / Static")))
                self.decay_slider.set(config.get("decay", 0.5))
                self.bright_slider.set(config.get("max_brightness", 255))
                self.auto_color_var.set(config.get("auto_color", False))
                
                self.color_low = tuple(config.get("color_low", [0, 255, 255]))
                self.color_mid = tuple(config.get("color_mid", [255, 255, 0]))
                self.color_high = tuple(config.get("color_high", [255, 0, 0]))
                
                # Update button colors
                self.btn_low.configure(fg_color=f"#{self.color_low[0]:02x}{self.color_low[1]:02x}{self.color_low[2]:02x}")
                self.btn_mid.configure(fg_color=f"#{self.color_mid[0]:02x}{self.color_mid[1]:02x}{self.color_mid[2]:02x}")
                self.btn_high.configure(fg_color=f"#{self.color_high[0]:02x}{self.color_high[1]:02x}{self.color_high[2]:02x}")
        except Exception as e:
            print(f"[TypingTab] Lỗi load_config: {e}")

    def save_config(self):
        try:
            config = {
                "mode_name": self.get_original_name_from_localized(self.mode_var.get()),
                "decay": self.decay_slider.get(),
                "max_brightness": int(self.bright_slider.get()),
                "auto_color": self.auto_color_var.get(),
                "color_low": list(self.color_low),
                "color_mid": list(self.color_mid),
                "color_high": list(self.color_high)
            }
            config_file = get_typing_config_path()
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"[TypingTab] Lỗi save_config: {e}")

    def pick_color(self, level):
        initial_color = getattr(self, f"color_{level}")
        picker = tkcolorpicker.ColorPicker(self, color=initial_color, title=self.master.i18n.t("typing_color_picker") + level.upper())
        
        def on_picker_change(*args):
            try:
                r, g, b = picker.red.get(), picker.green.get(), picker.blue.get()
                setattr(self, f"color_{level}", (r, g, b))
                # Cập nhật màu nút bấm
                btn = getattr(self, f"btn_{level}")
                btn.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
                self.update_monitor_config()
            except: pass

        picker.red.trace_add("write", on_picker_change)
        picker.green.trace_add("write", on_picker_change)
        picker.blue.trace_add("write", on_picker_change)
        self.wait_window(picker)
        self.save_config()

    def update_wpm_gui(self, wpm, current_color):
        self.wpm_label.configure(text=str(int(wpm)))
        hex_color = f"#{current_color[0]:02x}{current_color[1]:02x}{current_color[2]:02x}"
        self.wpm_label.configure(text_color=hex_color)

    def get_current_config(self):
        return {
            'mode_hex': self.get_hex_from_localized_name(self.mode_var.get()),
            'decay': self.decay_slider.get(),
            'max_brightness': int(self.bright_slider.get()),
            'auto_color': self.auto_color_var.get(),
            'color_low': self.color_low,
            'color_mid': self.color_mid,
            'color_high': self.color_high
        }

    def update_monitor_config(self, *args):
        if hasattr(self, 'monitor') and self.is_running:
            self.monitor.set_config(**self.get_current_config())
        
        # Debounce the file save operation to prevent excessive disk I/O when sliding
        if hasattr(self, 'save_timer') and self.save_timer is not None:
            self.after_cancel(self.save_timer)
        self.save_timer = self.after(1000, self.save_config)

    def toggle_typing(self, from_shutdown=False):
        if not self.is_running:
            self.is_running = True
            self.toggle_btn.configure(text=self.master.i18n.t("typing_btn_stop"), fg_color="red", hover_color="darkred")
            self.monitor = TypingMonitor(self.usb_driver, callback=self.update_wpm_gui, **self.get_current_config())
            self.monitor.start()
        else:
            self.is_running = False
            if not from_shutdown:
                try:
                    self.toggle_btn.configure(text=self.master.i18n.t("typing_btn_start"), fg_color="green", hover_color="darkgreen")
                except: pass
                
            if hasattr(self, 'monitor'):
                self.monitor.stop()
                
            # Khôi phục lại chế độ tĩnh khi dừng hiệu ứng
            self.master.restore_static_settings()
                
    def on_hide(self):
        if self.is_running:
            self.toggle_typing(from_shutdown=True)
        else:
            self.master.restore_static_settings()
