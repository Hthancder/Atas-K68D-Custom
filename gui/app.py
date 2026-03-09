import customtkinter as ctk
from tkinter import messagebox
import os
import json
import threading
import pystray
from PIL import Image, ImageDraw
from gui.tabs.static_tab import StaticTab
from gui.tabs.audio_tab import AudioTab
from gui.tabs.typing_tab import TypingTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.console_tab import ConsoleTab
from gui.tooltip import ToolTip
from gui.notification import ToastNotification
from core.i18n import I18n
from core.utils import get_base_dir, get_resource_dir

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BASE_DIR = get_base_dir()
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

class KBLightStudioApp(ctk.CTk):
    def __init__(self, usb_driver):
        super().__init__()
        
        self.i18n = I18n(SETTINGS_FILE)

        self.title("Atas-K68D-Custom - " + self.i18n.t("sidebar_static"))
        self.geometry("900x600")
        
        # Thiết lập Icon cho cửa sổ app
        icon_path = os.path.join(get_resource_dir(), "gui", "trayico", "K68.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Không thể thiết lập icon cửa sổ: {e}")
            
        self.usb_driver = usb_driver
        
        # Grid Layout: Sidebar (0) + Main Content (1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Load preferences
        self.settings = self.load_all_settings()
        self.minimize_to_tray_pref = self.settings.get("minimize_to_tray", None)
        self.show_tray_notification = self.settings.get("show_tray_notification", True)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1e1e1e")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Đẩy Settings xuống dưới

        # Thêm Banner trang trí vào Sidebar
        banner_path = os.path.join(get_resource_dir(), "gui", "assets", "BG.png")
        try:
            if os.path.exists(banner_path):
                # Tạo banner với chiều rộng bằng sidebar, chiều cao tự canh chỉnh cho đẹp
                banner_image = ctk.CTkImage(light_image=Image.open(banner_path), dark_image=Image.open(banner_path), size=(200, 100))
                self.banner_label = ctk.CTkLabel(self.sidebar_frame, image=banner_image, text="")
                self.banner_label.grid(row=0, column=0, padx=0, pady=(0, 10))
        except Exception as e:
            print(f"Không thể tải ảnh banner: {e}")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ATAS-K68D-CUSTOM", font=ctk.CTkFont(size=20, weight="bold", family="Consolas"))
        self.logo_label.grid(row=1, column=0, padx=20, pady=(10, 30))

        # Khởi tạo các Tabs
        self.tabs = {
            "Static": StaticTab(self, self.usb_driver),
            "Audio": AudioTab(self, self.usb_driver),
            "Typing": TypingTab(self, self.usb_driver),
            "Console": ConsoleTab(self, self.usb_driver),
            "Settings": SettingsTab(self, self.usb_driver)
        }
        
        # Sidebar Buttons
        self.tab_btns = {}
        row_idx = 2
        
        tab_info = [
            ("Static", self.i18n.t("sidebar_static"), self.i18n.t("sidebar_static_tooltip")),
            ("Audio", self.i18n.t("sidebar_audio"), self.i18n.t("sidebar_audio_tooltip")),
            ("Typing", self.i18n.t("sidebar_typing"), self.i18n.t("sidebar_typing_tooltip")),
            ("Console", self.i18n.t("sidebar_console"), self.i18n.t("sidebar_console_tooltip"))
        ]
        
        for tab_name, text, tooltip_text in tab_info:
            btn = ctk.CTkButton(self.sidebar_frame, text=text, fg_color="transparent", text_color=("gray10", "gray90"), hover_color="#333333", corner_radius=8, height=35, anchor="w", command=lambda name=tab_name: self.select_tab(name))
            btn.grid(row=row_idx, column=0, padx=20, pady=8, sticky="ew")
            ToolTip(btn, text=tooltip_text)
            self.tab_btns[tab_name] = btn
            row_idx += 1
            
        # Donate / Support button
        donate_text = self.i18n.t("sidebar_donate")
        if donate_text == "sidebar_donate": # Fallback if not in json
            donate_text = "Ủng hộ mình ☕" if self.i18n.current_lang == "vi" else "Buy me a Coffee ☕"
            
        self.donate_btn = ctk.CTkButton(self.sidebar_frame, text=donate_text, fg_color="#d97706", text_color="white", hover_color="#b45309", corner_radius=8, height=35, anchor="center", font=ctk.CTkFont(weight="bold"), command=self.open_donate_link)
        self.donate_btn.grid(row=7, column=0, padx=20, pady=(15, 5), sticky="ew")

        # Nút cài đặt dưới cùng
        self.settings_btn = ctk.CTkButton(self.sidebar_frame, text=self.i18n.t("sidebar_settings"), fg_color="transparent", text_color=("gray10", "gray90"), hover_color="#333333", corner_radius=8, height=35, anchor="w", command=lambda: self.select_tab("Settings"))
        self.settings_btn.grid(row=8, column=0, padx=20, pady=(5, 5), sticky="ew")
        ToolTip(self.settings_btn, text=self.i18n.t("sidebar_settings_tooltip"))
        self.tab_btns["Settings"] = self.settings_btn
        
        # Nút Language
        self.language_btn = ctk.CTkButton(self.sidebar_frame, text=self.i18n.t("sidebar_language"), fg_color="transparent", text_color=("gray10", "gray90"), hover_color="#333333", corner_radius=8, height=35, anchor="w", command=self.show_language_dialog)
        self.language_btn.grid(row=9, column=0, padx=20, pady=5, sticky="ew")
        
        # Nút thoát
        self.exit_btn = ctk.CTkButton(self.sidebar_frame, text=self.i18n.t("sidebar_exit"), fg_color="#882222", hover_color="#aa3333", anchor="center", command=self.confirm_exit)
        self.exit_btn.grid(row=10, column=0, padx=20, pady=(15, 10), sticky="ew")

        # Nút About (Clickable Text)
        self.about_label = ctk.CTkLabel(self.sidebar_frame, text="ℹ️ About Atas-K68D-Custom", text_color="gray70", cursor="hand2", font=ctk.CTkFont(size=11, underline=True))
        self.about_label.grid(row=11, column=0, pady=(5, 2), sticky="s")
        self.about_label.bind("<Button-1>", lambda e: self.show_about_dialog())

        # Footer Credit
        self.footer_label = ctk.CTkLabel(self.sidebar_frame, text="made by Hoang with love ❤️", text_color="gray50", font=ctk.CTkFont(size=10, slant="italic"))
        self.footer_label.grid(row=12, column=0, pady=(0, 15), sticky="s")

        self.current_tab_name = None
        self.select_tab("Static")
        
        # Handle Window Close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Tray icon variables
        self.tray_icon = None
        
        # Load tray preference
        self.minimize_to_tray_pref = self.load_tray_preference()

    def open_donate_link(self):
        import webbrowser
        webbrowser.open("https://buymeacoffee.com/hthan24")

    def show_about_dialog(self):
        import webbrowser
        dialog = ctk.CTkToplevel(self)
        dialog.title("About Atas-K68D-Custom")
        dialog.geometry("450x300")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (300 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="Atas-K68D-Custom", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text="Version 1.5", text_color="gray").pack(pady=(0, 20))
        
        links_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        links_frame.pack(pady=5)
        
        # Github Link
        gh_label = ctk.CTkLabel(links_frame, text="GitHub", text_color="black", cursor="hand2", font=ctk.CTkFont(weight="bold"))
        gh_label.pack(pady=4)
        gh_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Hthancder"))
        
        # Facebook Link
        fb_label = ctk.CTkLabel(links_frame, text="Facebook", text_color="#1877F2", cursor="hand2", font=ctk.CTkFont(weight="bold"))
        fb_label.pack(pady=4)
        fb_label.bind("<Button-1>", lambda e: webbrowser.open("https://www.facebook.com/profile.php?id=61587008277909"))
        
        # Youtube Link
        yt_label = ctk.CTkLabel(links_frame, text="YouTube", text_color="#FF0000", cursor="hand2", font=ctk.CTkFont(weight="bold"))
        yt_label.pack(pady=4)
        yt_label.bind("<Button-1>", lambda e: webbrowser.open("https://www.youtube.com/@LazyGappDev"))
        
        # Footer text
        footer_text = "Dự án này được phát triển bởi một cá nhân,\nHoan nghênh sự ủng hộ và đóng góp!"
        if self.i18n.current_lang != "vi":
            footer_text = "Developed by a single individual.\nSupport and contributions are welcome!"
            
        ctk.CTkLabel(dialog, text=footer_text, text_color="gray60", font=ctk.CTkFont(size=11, slant="italic"), justify="center").pack(side="bottom", pady=20)

    def show_language_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.i18n.t("lang_dialog_title"))
        dialog.geometry("400x400")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text=self.i18n.t("lang_dialog_title"), font=ctk.CTkFont(weight="bold", size=16)).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text=self.i18n.t("lang_dialog_desc"), text_color="gray").pack(pady=(0, 20))
        
        # Thêm ScrollableFrame nếu có nhiều ngôn ngữ
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        def set_lang(code):
            self.i18n.set_language(code)
            dialog.destroy()
            messagebox.showinfo(self.i18n.t("lang_dialog_title"), self.i18n.t("lang_dialog_desc"))
            self.quit_app()

        available_langs = self.i18n.get_available_languages()
        
        for code, info in available_langs.items():
            btn_text = f"{info['name']}"
            
            # Ưu tiên làm nổi bật tiếng Việt
            if code == "vi":
                btn = ctk.CTkButton(
                    scroll, 
                    text=btn_text, 
                    fg_color="#ffcc00", 
                    text_color="black", 
                    hover_color="#e6b800", 
                    font=ctk.CTkFont(weight="bold"), 
                    command=lambda c=code: set_lang(c)
                )
            else:
                btn = ctk.CTkButton(
                    scroll, 
                    text=btn_text, 
                    fg_color="#333333", 
                    command=lambda c=code: set_lang(c)
                )
            btn.pack(pady=5, fill="x", padx=20)

    def create_tray_image(self):
        # Use the specific K68.ico file for the system tray
        icon_path = os.path.join(os.path.dirname(__file__), "trayico", "K68.ico")
        try:
            image = Image.open(icon_path)
            return image
        except Exception as e:
            print(f"Không thể tải icon ({icon_path}): {e}")
            # Fallback to drawn icon if file not found
            image = Image.new('RGB', (64, 64), color=(30, 30, 30))
            draw = ImageDraw.Draw(image)
            draw.ellipse((16, 16, 48, 48), fill=(0, 255, 255))
            return image

    def init_tray(self):
        image = self.create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("Hiển thị App", self.show_window, default=True),
            pystray.MenuItem("Thoát", self.quit_app)
        )
        self.tray_icon = pystray.Icon("KBLightStudio", image, "Atas-K68D-Custom", menu)
        self.tray_icon.run_detached()

    def show_window(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.after(0, self.deiconify)

    def load_all_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
        except: pass
        return {}

    def save_all_settings(self, settings_dict):
        try:
            # Merge with existing
            current = self.load_all_settings()
            current.update(settings_dict)
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(current, f, indent=4)
            self.settings = current
        except: pass

    def load_tray_preference(self):
        return self.settings.get("minimize_to_tray", None)

    def save_tray_preference(self, pref):
        self.minimize_to_tray_pref = pref
        self.save_all_settings({"minimize_to_tray": pref})

    def show_tray_toast(self):
        if self.show_tray_notification:
            ToastNotification(self, 
                             message="Ứng dụng đã được thu nhỏ xuống khay hệ thống.", 
                             title="Atas-K68D-Custom", 
                             duration=4000)

    def on_closing(self):
        if self.minimize_to_tray_pref is True:
            self.minimize_to_tray()
        elif self.minimize_to_tray_pref is False:
            self.quit_app()
        else:
            self.ask_tray_preference()

    def ask_tray_preference(self):
        # Custom dialog with checkbox using Toplevel
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.i18n.t("settings_minimize"))
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="Bạn muốn thu nhỏ ứng dụng xuống khay hệ thống\nđể giữ hiệu ứng LED chạy nền không?", justify="center").pack(pady=(20, 10))
        
        dont_show_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(dialog, text="Không hỏi lại (Lưu lựa chọn)", variable=dont_show_var)
        checkbox.pack(pady=10)
        
        def on_yes():
            if dont_show_var.get():
                self.save_tray_preference(True)
            dialog.destroy()
            self.minimize_to_tray()
            
        def on_no():
            if dont_show_var.get():
                self.save_tray_preference(False)
            dialog.destroy()
            self.quit_app()
            
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text=self.i18n.t("tray_show"), command=on_yes).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=self.i18n.t("sidebar_exit"), fg_color="#882222", hover_color="#aa3333", command=on_no).pack(side="left", padx=10)

    def minimize_to_tray(self):
        self.withdraw() # Ẩn cửa sổ chính
        self.init_tray()
        self.show_tray_toast()

    def confirm_exit(self):
        if messagebox.askyesno(self.i18n.t("exit_title"), self.i18n.t("exit_confirm")):
            self.quit_app()

    def quit_app(self, icon=None, item=None):
        """Đảm bảo quy trình thoát luôn chạy trên Main Thread."""
        if threading.current_thread() is not threading.main_thread():
            self.after(0, lambda: self.quit_app())
            return

        print("[APP] Bắt đầu quy trình thoát...")
        
        # 1. Dừng Tray Icon trước (để tránh xung đột thread)
        if self.tray_icon:
            try:
                print("[APP] Đang dừng Tray Icon...")
                self.tray_icon.stop()
                self.tray_icon = None
            except: pass
        
        # 2. Dừng các hiệu ứng chạy ngầm (WPM, Audio) TRƯỚC khi đóng USB
        for name, tab in self.tabs.items():
            try:
                if hasattr(tab, 'on_hide'):
                    print(f"[APP] Đang dọn dẹp Tab: {name}")
                    tab.on_hide()
            except: pass
            
        # 3. Khôi phục lại chế độ LED tĩnh lần cuối
        self.restore_static_settings()
        
        # 4. Ngắt kết nối USB
        if self.usb_driver:
            try:
                self.usb_driver.close()
            except: pass
            
        # 4. Hủy UI và thoát
        try:
            print("[APP] Đang hủy cửa sổ chính...")
            self.quit()
            self.destroy()
        except: pass
        
        print("[APP] Tạm biệt!")
        os._exit(0)

    def select_tab(self, tab_name):
        # Ẩn tab hiện tại
        if self.current_tab_name:
            self.tabs[self.current_tab_name].grid_forget()
            self.tabs[self.current_tab_name].on_hide()
            self.tab_btns[self.current_tab_name].configure(fg_color="transparent", text_color=("gray10", "gray90"))
            
        # Hiện tab mới
        self.current_tab_name = tab_name
        self.tabs[tab_name].grid(row=0, column=1, sticky="nsew")
        self.tabs[tab_name].on_show()
        
        # Đổi màu nút (Active State)
        self.tab_btns[tab_name].configure(fg_color="#333333", text_color="#00f2ff")

    def restore_static_settings(self):
        """Khôi phục lại chế độ LED tĩnh đã lưu trong tab Static."""
        try:
            if "Static" in self.tabs:
                print("[APP] Đang khôi phục lại chế độ LED tĩnh...")
                # Gửi 2 lần để đảm bảo bàn phím nhận lệnh sau khi vừa thoát mode âm nhạc/typing
                self.tabs["Static"].apply_mode()
                self.after(200, self.tabs["Static"].apply_mode)
        except Exception as e:
            print(f"[APP] Lỗi khi khôi phục LED tĩnh: {e}")
