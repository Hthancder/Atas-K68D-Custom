import customtkinter as ctk
import tkinter as tk
import tkcolorpicker
import os
import json
from gui.tabs.base_tab import BaseTab
from gui.tooltip import ToolTip
from core.protocol import MODES
from effects.audio_visualizer import AudioVisualizer
from core.utils import get_base_dir

# --- Configuration Directory Setup ---
BASE_DIR = get_base_dir()
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def get_audio_config_path():
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
    return os.path.join(config_dir, "audio_config.json")

class AudioTab(BaseTab):
    def __init__(self, master, usb_driver, **kwargs):
        super().__init__(master, usb_driver, **kwargs)
        
        # Màu sắc tùy chỉnh cho các dải tần
        self.bass_color = (255, 0, 0)
        self.mid_color = (0, 255, 0)
        self.treble_color = (0, 0, 255)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Tiêu đề chính
        self.title = ctk.CTkLabel(self, text=self.master.i18n.t("audio_title"), font=ctk.CTkFont(size=22, weight="bold"))
        self.title.grid(row=0, column=0, padx=30, pady=(30, 15), sticky="w")
        
        # Main Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # --- NHÓM 1: ĐIỀU KHIỂN CHÍNH ---
        self.main_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.main_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.main_frame, text=self.master.i18n.t("audio_effect_style"), font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self.effect_styles = {
            self.master.i18n.t("style_freq_colors"): "freq_colors",
            self.master.i18n.t("style_rainbow_bass"): "rainbow_bass",
            self.master.i18n.t("style_volume_pulse"): "volume_pulse",
            self.master.i18n.t("style_band_subbass"): "band_subbass",
            self.master.i18n.t("style_band_bass"): "band_bass",
            self.master.i18n.t("style_band_lowmid"): "band_lowmid",
            self.master.i18n.t("style_band_mid"): "band_mid",
            self.master.i18n.t("style_band_uppermid"): "band_uppermid",
            self.master.i18n.t("style_band_treble"): "band_treble",
            self.master.i18n.t("style_dual_band_bt"): "dual_band_bt",
            self.master.i18n.t("style_fire_effect"): "fire_effect",
            self.master.i18n.t("style_smart_pitch"): "smart_pitch"
        }
        self.style_var = ctk.StringVar(value=list(self.effect_styles.keys())[0])
        self.style_menu = ctk.CTkOptionMenu(self.main_frame, values=list(self.effect_styles.keys()), variable=self.style_var, command=self.on_style_changed, height=35)
        self.style_menu.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="ew")

        # Khung chứa cài đặt riêng cho từng hiệu ứng
        self.effect_settings_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.effect_settings_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        self.effect_settings_frame.grid_columnconfigure(1, weight=1)

        self.device_label = ctk.CTkLabel(self.main_frame, text=self.master.i18n.t("audio_wasapi"), text_color="#00f2ff", font=ctk.CTkFont(size=11, weight="bold"))
        self.device_label.grid(row=2, column=1, padx=20, pady=(0, 5), sticky="e")

        self.auto_saturation_var = ctk.BooleanVar(value=True)
        self.auto_saturation_switch = ctk.CTkSwitch(self.main_frame, text=self.master.i18n.t("audio_auto_sat"), variable=self.auto_saturation_var, command=self.update_visualizer_config, progress_color="#00f2ff")
        self.auto_saturation_switch.grid(row=3, column=1, padx=20, pady=(0, 15), sticky="e")

        self.is_running = False
        self.toggle_btn = ctk.CTkButton(self.main_frame, text=self.master.i18n.t("audio_btn_start"), command=self.toggle_audio, height=50, font=ctk.CTkFont(weight="bold"), fg_color="#28a745", hover_color="#218838", corner_radius=10)
        self.toggle_btn.grid(row=4, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        # --- NHÓM 2: HIỆU CHỈNH ÂM THANH (EQ) ---
        self.eq_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.eq_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.eq_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.eq_frame, text=self.master.i18n.t("audio_eq_title"), font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, columnspan=2, padx=20, pady=15, sticky="w")

        # Slider Helper Function to reduce code
        def create_slider_row(parent, row, label_text, from_val, to_val, current_val, label_attr):
            lbl_frame = ctk.CTkFrame(parent, fg_color="transparent")
            lbl_frame.grid(row=row, column=0, padx=20, pady=5, sticky="w")
            ctk.CTkLabel(lbl_frame, text=label_text).pack(side="left")
            val_lbl = ctk.CTkLabel(lbl_frame, text=str(current_val), text_color="#00f2ff", font=ctk.CTkFont(weight="bold"))
            val_lbl.pack(side="left", padx=5)
            setattr(self, label_attr, val_lbl)
            
            slider = ctk.CTkSlider(parent, from_=from_val, to=to_val, number_of_steps=100 if to_val > 10 else 50, command=self.update_visualizer_config, button_color="#00f2ff", button_hover_color="#00c8d4")
            slider.set(current_val)
            slider.grid(row=row, column=1, padx=20, pady=5, sticky="ew")
            return slider

        self.sens_slider = create_slider_row(self.eq_frame, 1, self.master.i18n.t("audio_eq_total"), 0.1, 3.0, 1.0, "sens_val_label")
        
        self.agc_var = ctk.BooleanVar(value=False)
        self.agc_switch = ctk.CTkSwitch(self.eq_frame, text=self.master.i18n.t("audio_auto_eq"), variable=self.agc_var, command=self.update_visualizer_config, progress_color="#00f2ff")
        self.agc_switch.grid(row=1, column=2, padx=20)
        
        self.bass_slider = create_slider_row(self.eq_frame, 2, "Bass:", 0.1, 5.0, 1.0, "bass_val_label")
        self.mid_slider = create_slider_row(self.eq_frame, 3, "Mid:", 0.1, 5.0, 1.0, "mid_val_label")
        self.treble_slider = create_slider_row(self.eq_frame, 4, "Treble:", 0.1, 5.0, 1.0, "treble_val_label")

        # --- NHÓM 3: THÔNG SỐ KỸ THUẬT ---
        self.tech_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.tech_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.tech_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.tech_frame, text=self.master.i18n.t("audio_tech_title"), font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, columnspan=2, padx=20, pady=15, sticky="w")

        ctk.CTkLabel(self.tech_frame, text=self.master.i18n.t("audio_bg_mode")).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.mode_var = ctk.StringVar(value=self.get_localized_mode_name("Fixed / Static"))
        self.mode_menu = ctk.CTkOptionMenu(self.tech_frame, values=list(self.get_localized_modes().keys()), variable=self.mode_var, command=self.update_visualizer_config, height=35)
        self.mode_menu.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        self.attack_slider = create_slider_row(self.tech_frame, 2, self.master.i18n.t("audio_attack"), 0.05, 1.0, 0.8, "attack_val_label")
        self.decay_slider = create_slider_row(self.tech_frame, 3, self.master.i18n.t("audio_decay"), 0.01, 1.0, 0.2, "decay_val_label")
        self.noise_gate_slider = create_slider_row(self.tech_frame, 4, self.master.i18n.t("audio_noise_gate"), 0, 1000, 10, "noise_gate_val_label")
        self.fps_slider = create_slider_row(self.tech_frame, 5, self.master.i18n.t("audio_fps"), 5, 60, 20, "fps_val_label")
        self.bright_slider = create_slider_row(self.tech_frame, 6, self.master.i18n.t("audio_max_bright"), 10, 255, 255, "bright_val_label")
        
        ctk.CTkLabel(self.tech_frame, text="").grid(row=7, column=0, pady=5) # Spacer

        # --- NHÓM 4: CẤU HÌNH KHI IM LẶNG ---
        self.silent_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.silent_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.silent_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.silent_frame, text=self.master.i18n.t("audio_silent_title"), font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, columnspan=2, padx=20, pady=15, sticky="w")

        ctk.CTkLabel(self.silent_frame, text=self.master.i18n.t("audio_silent_mode")).grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.silent_mode_var = ctk.StringVar(value=self.get_localized_mode_name("Fixed / Static"))
        self.silent_mode_menu = ctk.CTkOptionMenu(self.silent_frame, values=list(self.get_localized_modes().keys()), variable=self.silent_mode_var, command=self.update_visualizer_config, height=35)
        self.silent_mode_menu.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        # Màu sắc im lặng
        ctk.CTkLabel(self.silent_frame, text=self.master.i18n.t("audio_color_rgb")).grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.s_color_frame = ctk.CTkFrame(self.silent_frame, fg_color="transparent")
        self.s_color_frame.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        self.s_color_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.sr_entry = ctk.CTkEntry(self.s_color_frame, placeholder_text="R", height=35); self.sr_entry.grid(row=0, column=0, padx=(0, 2), sticky="ew"); self.sr_entry.insert(0, "255"); self.sr_entry.bind("<KeyRelease>", self.update_visualizer_config)
        self.sg_entry = ctk.CTkEntry(self.s_color_frame, placeholder_text="G", height=35); self.sg_entry.grid(row=0, column=1, padx=2, sticky="ew"); self.sg_entry.insert(0, "255"); self.sg_entry.bind("<KeyRelease>", self.update_visualizer_config)
        self.sb_entry = ctk.CTkEntry(self.s_color_frame, placeholder_text="B", height=35); self.sb_entry.grid(row=0, column=2, padx=(2, 5), sticky="ew"); self.sb_entry.insert(0, "255"); self.sb_entry.bind("<KeyRelease>", self.update_visualizer_config)
        self.silent_color_btn = ctk.CTkButton(self.s_color_frame, text="🎨", width=40, height=35, command=self.pick_silent_color); self.silent_color_btn.grid(row=0, column=3)

        self.min_bright_slider = create_slider_row(self.silent_frame, 3, self.master.i18n.t("audio_silent_bright"), 0, 255, 0, "min_bright_val_label")
        
        self.silence_timeout_slider = create_slider_row(self.silent_frame, 4, self.master.i18n.t("audio_silent_timeout"), 0.0, 5.0, 0.5, "silence_timeout_val_label")
        
        self.silent_auto_color_var = ctk.BooleanVar(value=False)
        self.silent_auto_switch = ctk.CTkSwitch(self.silent_frame, text=self.master.i18n.t("audio_silent_auto_color"), variable=self.silent_auto_color_var, command=self.update_visualizer_config, progress_color="#00f2ff")
        self.silent_auto_switch.grid(row=5, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="w")

        # --- NHÓM 5: MINH HỌA ---
        self.visual_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#252525", corner_radius=12)
        self.visual_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.visual_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.visual_frame, text=self.master.i18n.t("audio_visualizer_title"), font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        self.canvas_width = 500
        self.canvas_height = 100
        self.spectrum_canvas = tk.Canvas(self.visual_frame, width=self.canvas_width, height=self.canvas_height, bg="#1a1a1a", highlightthickness=0)
        self.spectrum_canvas.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.spectrum_canvas.create_text(self.canvas_width/2, self.canvas_height/2, text=self.master.i18n.t("audio_canvas_text"), fill="gray", font=ctk.CTkFont(family="Consolas"))

        # Thêm ToolTips
        ToolTip(self.toggle_btn, "Bật/tắt việc phân tích âm thanh hệ thống để điều khiển LED bàn phím.")
        ToolTip(self.style_menu, "Chọn kiểu phản ứng của LED với âm thanh.")
        ToolTip(self.sens_slider, "Điều chỉnh độ nhạy chung.")
        ToolTip(self.mode_menu, "Chế độ LED dùng làm nền khi phát nhạc.")
        ToolTip(self.attack_slider, "Tốc độ nháy lên: Gần 1 là chớp ngay lập tức, gần 0 là sáng lên từ từ.")
        ToolTip(self.decay_slider, "Tốc độ mờ dần: Gần 1 là tắt ngay lập tức, gần 0 là mờ từ từ (tạo vệt đuôi).")
        ToolTip(self.noise_gate_slider, "Lọc ồn: Tăng lên nếu đèn hay bị nháy do tiếng ồn môi trường hoặc tiếng sôi của loa.")
        ToolTip(self.fps_slider, "Tốc độ cập nhật tín hiệu USB (giây).")
        ToolTip(self.bright_slider, "Độ sáng cao nhất khi nhạc đánh cực mạnh.")
        ToolTip(self.min_bright_slider, "Độ sáng khi im lặng. Tránh việc bàn phím bị tắt đen hoàn toàn.")
        ToolTip(self.silent_mode_menu, "Chế độ LED sẽ hiển thị khi không có âm thanh.")
        ToolTip(self.silent_color_btn, "Chọn màu sắc cố định khi im lặng.")

        self.load_config()

    def build_color_picker(self, label_text, band, row):
        """Helper để tạo nút chọn màu động."""
        lbl_frame = ctk.CTkFrame(self.effect_settings_frame, fg_color="transparent")
        lbl_frame.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
        self.effect_settings_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(lbl_frame, text=label_text).pack(side="left")
        
        # Lấy màu hiện tại
        current_color = getattr(self, f"{band}_color", (255,255,255))
        hex_color = f"#{current_color[0]:02x}{current_color[1]:02x}{current_color[2]:02x}"
        
        btn = ctk.CTkButton(lbl_frame, text="", width=40, height=25, fg_color=hex_color, corner_radius=6, command=lambda b=band: self.pick_band_color(b))
        btn.pack(side="right")
        # Lưu reference để cập nhật màu nút sau này
        setattr(self, f"{band}_color_btn", btn)

    def update_effect_settings_ui(self, *args):
        """Cập nhật Bảng hiệu chỉnh tùy theo hiệu ứng được chọn."""
        # Xóa các widget cũ
        for widget in self.effect_settings_frame.winfo_children():
            widget.destroy()
            
        effect_id = self.effect_styles.get(self.style_var.get(), "")
        
        # Map các hiệu ứng với các tùy chọn màu tương ứng
        if effect_id == "freq_colors":
            self.build_color_picker(self.master.i18n.t("audio_color_bass"), "bass", 0)
            self.build_color_picker(self.master.i18n.t("audio_color_mid"), "mid", 1)
            self.build_color_picker(self.master.i18n.t("audio_color_treble"), "treble", 2)
        elif effect_id == "dual_band_bt":
            self.build_color_picker(self.master.i18n.t("audio_color_bass"), "bass", 0)
            self.build_color_picker(self.master.i18n.t("audio_color_treble"), "treble", 1)
        elif effect_id in ["volume_pulse", "band_subbass", "band_bass"]:
            self.build_color_picker(self.master.i18n.t("audio_color_effect"), "bass", 0)
        elif effect_id in ["band_lowmid", "band_mid", "band_uppermid"]:
            self.build_color_picker(self.master.i18n.t("audio_color_effect"), "mid", 0)
        elif effect_id == "band_treble":
            self.build_color_picker(self.master.i18n.t("audio_color_effect"), "treble", 0)
        else:
            # Các hiệu ứng không có tùy chỉnh màu riêng (thông minh, lửa, cầu vồng...)
            ctk.CTkLabel(self.effect_settings_frame, text=self.master.i18n.t("audio_no_custom_color"), text_color="gray").grid(row=0, column=0, padx=20, pady=5)


    def load_config(self):
        try:
            config_file = get_audio_config_path()
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                style_id = config.get("effect_id", "freq_colors")
                for name, eid in self.effect_styles.items():
                    if eid == style_id:
                        self.style_var.set(name)
                        break
                
                self.sens_slider.set(config.get("sensitivity", 1.0))
                self.mode_var.set(self.get_localized_mode_name(config.get("mode_name", "Fixed / Static")))
                self.bass_slider.set(config.get("bass_mult", 1.0))
                self.mid_slider.set(config.get("mid_mult", 1.0))
                self.treble_slider.set(config.get("treble_mult", 1.0))
                self.agc_var.set(config.get("auto_gain", False))
                self.attack_slider.set(config.get("attack", 0.8))
                self.decay_slider.set(config.get("decay", 0.2))
                self.noise_gate_slider.set(config.get("noise_gate", 10))
                self.fps_slider.set(config.get("fps", 20))
                self.bright_slider.set(config.get("max_brightness", 255))
                self.min_bright_slider.set(config.get("min_brightness", 0))
                self.silence_timeout_slider.set(config.get("silence_timeout", 0.5))
                self.auto_saturation_var.set(config.get("auto_saturation", True))
                
                self.bass_color = tuple(config.get("bass_color", [255, 0, 0]))
                self.mid_color = tuple(config.get("mid_color", [0, 255, 0]))
                self.treble_color = tuple(config.get("treble_color", [0, 0, 255]))

                # Silent config
                self.silent_mode_var.set(self.get_localized_mode_name(config.get("silent_mode", "Fixed / Static")))
                sc = config.get("silent_color_rgb", [255, 255, 255])
                self.sr_entry.delete(0, 'end'); self.sr_entry.insert(0, str(sc[0]))
                self.sg_entry.delete(0, 'end'); self.sg_entry.insert(0, str(sc[1]))
                self.sb_entry.delete(0, 'end'); self.sb_entry.insert(0, str(sc[2]))
                self.silent_auto_color_var.set(config.get("silent_auto_color", False))
                
                # Update button colors
                self.silent_color_btn.configure(fg_color=f"#{sc[0]:02x}{sc[1]:02x}{sc[2]:02x}")
                
                # Update effect specific ui
                self.update_effect_settings_ui()

                # Update labels
                self.update_visualizer_config()
        except: pass

    def save_config(self):
        try:
            config = {
                "effect_id": self.effect_styles[self.style_var.get()],
                "sensitivity": self.sens_slider.get(),
                "mode_name": self.get_original_name_from_localized(self.mode_var.get()),
                "bass_mult": self.bass_slider.get(),
                "mid_mult": self.mid_slider.get(),
                "treble_mult": self.treble_slider.get(),
                "auto_gain": self.agc_var.get(),
                "attack": self.attack_slider.get(),
                "decay": self.decay_slider.get(),
                "noise_gate": self.noise_gate_slider.get(),
                "fps": int(self.fps_slider.get()),
                "max_brightness": int(self.bright_slider.get()),
                "min_brightness": int(self.min_bright_slider.get()),
                "silence_timeout": float(self.silence_timeout_slider.get()),
                "auto_saturation": bool(self.auto_saturation_var.get()),
                "bass_color": list(self.bass_color),
                "mid_color": list(self.mid_color),
                "treble_color": list(self.treble_color),
                "silent_mode": self.get_original_name_from_localized(self.silent_mode_var.get()),
                "silent_color_rgb": [int(self.sr_entry.get() or 0), int(self.sg_entry.get() or 0), int(self.sb_entry.get() or 0)],
                "silent_auto_color": bool(self.silent_auto_color_var.get())
            }
            config_file = get_audio_config_path()
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Lỗi khi lưu audio config: {e}")

    def pick_band_color(self, band):
        initial_color = getattr(self, f"{band}_color")
        picker = tkcolorpicker.ColorPicker(self, color=initial_color, title=self.master.i18n.t("audio_color_picker_title") + band.upper())
        
        def on_picker_change(*args):
            try:
                r, g, b = picker.red.get(), picker.green.get(), picker.blue.get()
                setattr(self, f"{band}_color", (r, g, b))
                # Cập nhật màu nút bấm
                btn = getattr(self, f"{band}_color_btn")
                btn.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
                self.update_visualizer_config()
            except: pass

        picker.red.trace_add("write", on_picker_change)
        picker.green.trace_add("write", on_picker_change)
        picker.blue.trace_add("write", on_picker_change)
        self.wait_window(picker)

    def pick_silent_color(self):
        try:
            r = int(self.sr_entry.get() or 0)
            g = int(self.sg_entry.get() or 0)
            b = int(self.sb_entry.get() or 0)
        except: r, g, b = 255, 255, 255
            
        picker = tkcolorpicker.ColorPicker(self, color=(r, g, b), title=self.master.i18n.t("audio_color_picker_silent"))
        
        def on_picker_change(*args):
            try:
                nr, ng, nb = picker.red.get(), picker.green.get(), picker.blue.get()
                self.sr_entry.delete(0, 'end'); self.sr_entry.insert(0, str(nr))
                self.sg_entry.delete(0, 'end'); self.sg_entry.insert(0, str(ng))
                self.sb_entry.delete(0, 'end'); self.sb_entry.insert(0, str(nb))
                self.silent_color_btn.configure(fg_color=f"#{nr:02x}{ng:02x}{nb:02x}")
                self.silent_auto_color_var.set(False)
                self.update_visualizer_config()
            except: pass

        picker.red.trace_add("write", on_picker_change)
        picker.green.trace_add("write", on_picker_change)
        picker.blue.trace_add("write", on_picker_change)
        self.wait_window(picker)

    def get_current_config(self):
        return {
            'effect_type': self.effect_styles[self.style_var.get()],
            'sensitivity': self.sens_slider.get(),
            'mode_hex': self.get_hex_from_localized_name(self.mode_var.get()),
            'bass_mult': self.bass_slider.get(),
            'mid_mult': self.mid_slider.get(),
            'treble_mult': self.treble_slider.get(),
            'auto_gain': self.agc_var.get(),
            'attack': float(self.attack_slider.get()),
            'decay': float(self.decay_slider.get()),
            'noise_gate': int(self.noise_gate_slider.get()),
            'fps': int(self.fps_slider.get()),
            'max_brightness': int(self.bright_slider.get()),
            'min_brightness': int(self.min_bright_slider.get()),
            'silence_timeout': float(self.silence_timeout_slider.get()),
            'auto_saturation': bool(self.auto_saturation_var.get()),
            'bass_color': self.bass_color,
            'mid_color': self.mid_color,
            'treble_color': self.treble_color,
            'silent_mode_hex': self.get_hex_from_localized_name(self.silent_mode_var.get()),
            'silent_color': (int(self.sr_entry.get() or 0), int(self.sg_entry.get() or 0), int(self.sb_entry.get() or 0)),
            'silent_auto_color': self.silent_auto_color_var.get()
        }

    def on_style_changed(self, *args):
        self.update_effect_settings_ui()
        self.update_visualizer_config()

    def update_visualizer_config(self, *args):
        # Cập nhật nhãn thông số trên giao diện
        try:
            self.sens_val_label.configure(text=f"{self.sens_slider.get():.1f}")
            self.bass_val_label.configure(text=f"{self.bass_slider.get():.1f}")
            self.mid_val_label.configure(text=f"{self.mid_slider.get():.1f}")
            self.treble_val_label.configure(text=f"{self.treble_slider.get():.1f}")
            self.attack_val_label.configure(text=f"{self.attack_slider.get():.2f}")
            self.decay_val_label.configure(text=f"{self.decay_slider.get():.2f}")
            self.noise_gate_val_label.configure(text=str(int(self.noise_gate_slider.get())))
            self.fps_val_label.configure(text=str(int(self.fps_slider.get())))
            self.bright_val_label.configure(text=str(int(self.bright_slider.get())))
            self.min_bright_val_label.configure(text=str(int(self.min_bright_slider.get())))
            self.silence_timeout_val_label.configure(text=f"{self.silence_timeout_slider.get():.1f}s")
        except: pass

        # Kích hoạt áp dụng cấu hình (Real-time Preview)
        self.trigger_apply()
        
        # Lưu cấu hình mỗi khi có thay đổi (sử dụng debounce để tránh ghi file liên tục)
        if hasattr(self, 'save_timer') and self.save_timer is not None:
            self.after_cancel(self.save_timer)
        self.save_timer = self.after(1000, self.save_config)

    def trigger_apply(self):
        """Áp dụng cấu hình ngay lập tức lên bàn phím để xem trước (Preview)."""
        if hasattr(self, 'apply_timer'):
            self.after_cancel(self.apply_timer)
        self.apply_timer = self.after(50, self.apply_now)

    def apply_now(self):
        try:
            config = self.get_current_config()
            
            # 1. Cập nhật cho Thread đang chạy (nếu có)
            if hasattr(self, 'visualizer') and self.is_running:
                self.visualizer.set_config(**config)
            
            # 2. Ép áp dụng Silent Mode lên bàn phím để Preview
            # Nếu đang chạy âm nhạc, việc này có thể gây giật nhẹ nhưng đảm bảo "áp dụng ngay"
            # Nếu không chạy, nó hoạt động như chế độ tĩnh để người dùng chỉnh màu im lặng.
            sr, sg, sb = config['silent_color']
            self.usb_driver.apply_mode(
                config['silent_mode_hex'], 
                (sr, sg, sb), 
                brightness=config['min_brightness'], 
                speed=1, 
                auto_color=config['silent_auto_color']
            )
        except: pass

    def toggle_audio(self, from_shutdown=False):
        if not self.is_running:
            self.is_running = True
            self.toggle_btn.configure(text=self.master.i18n.t("audio_btn_stop"), fg_color="red", hover_color="darkred")
            config = self.get_current_config()
            
            # Áp dụng cấu hình im lặng ngay lập tức để người dùng thấy phản hồi tức thì
            # trước khi Thread xử lý âm thanh khởi động hoàn tất (mất khoảng ~1s)
            sr, sg, sb = config['silent_color']
            self.usb_driver.apply_mode(
                config['silent_mode_hex'], 
                (sr, sg, sb), 
                brightness=config['min_brightness'], 
                speed=1, 
                auto_color=config['silent_auto_color']
            )
            
            self.visualizer = AudioVisualizer(self.usb_driver, gui_callback=self.draw_spectrum, **config)
            self.visualizer.start()
        else:
            self.is_running = False
            if not from_shutdown:
                try:
                    self.toggle_btn.configure(text=self.master.i18n.t("audio_btn_start"), fg_color="green", hover_color="darkgreen")
                except: pass
                
            if hasattr(self, 'visualizer'):
                self.visualizer.stop()
            
            # Khôi phục lại chế độ tĩnh khi dừng hiệu ứng
            self.master.restore_static_settings()
            
            if not from_shutdown:
                try:
                    self.spectrum_canvas.delete("all")
                    self.spectrum_canvas.create_text(self.canvas_width/2, self.canvas_height/2, text=self.master.i18n.t("audio_canvas_text"), fill="gray")
                except: pass

    def draw_spectrum(self, fft_bands):
        if not self.is_running: return
        
        def rgb_to_hex(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        def update_gui():
            if not self.is_running: return
            try:
                self.spectrum_canvas.delete("all")
                if not fft_bands: return
                
                num_bands = len(fft_bands)
                bar_width = self.canvas_width / num_bands
                
                # Sử dụng màu sắc người dùng đã chọn
                b_hex = rgb_to_hex(self.bass_color)
                m_hex = rgb_to_hex(self.mid_color)
                t_hex = rgb_to_hex(self.treble_color)

                for i, val in enumerate(fft_bands):
                    height = min(max(val, 0.0), 1.0) * self.canvas_height
                    
                    # Ánh xạ màu theo dải tần tương ứng
                    if i < num_bands / 3: color = b_hex
                    elif i < 2 * num_bands / 3: color = m_hex
                    else: color = t_hex
                    
                    x0, y0 = i * bar_width, self.canvas_height - height
                    x1 = x0 + bar_width - 1
                    y1 = self.canvas_height
                    self.spectrum_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            except: pass
        self.after(0, update_gui)
                
    def on_hide(self):
        if self.is_running: 
            self.toggle_audio(from_shutdown=True)
        else:
            self.master.restore_static_settings()
