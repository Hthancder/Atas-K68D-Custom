import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
from gui.tabs.base_tab import BaseTab

class ConsoleTab(BaseTab):
    def __init__(self, master, usb_driver, **kwargs):
        super().__init__(master, usb_driver, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.title = ctk.CTkLabel(self, text=self.master.i18n.t("console_title"), font=ctk.CTkFont(size=22, weight="bold"))
        self.title.grid(row=0, column=0, padx=30, pady=(30, 15), sticky="w")
        
        # --- Toolbar ---
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=1, column=0, padx=30, pady=(0, 15), sticky="ew")
        
        self.clear_btn = ctk.CTkButton(self.toolbar, text=self.master.i18n.t("console_btn_clear"), width=100, height=35, font=ctk.CTkFont(weight="bold"), fg_color="#882222", hover_color="#aa3333", command=self.clear_log)
        self.clear_btn.pack(side="left", padx=(0, 10))
        
        self.save_btn = ctk.CTkButton(self.toolbar, text=self.master.i18n.t("console_btn_save"), width=120, height=35, font=ctk.CTkFont(weight="bold"), command=self.save_log)
        self.save_btn.pack(side="left", padx=(0, 10))
        
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_cb = ctk.CTkCheckBox(self.toolbar, text=self.master.i18n.t("console_auto_scroll"), variable=self.auto_scroll_var, fg_color="#00f2ff")
        self.auto_scroll_cb.pack(side="left", padx=(10, 0))

        # --- Console Textbox Container ---
        self.log_container = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=12)
        self.log_container.grid(row=2, column=0, padx=30, pady=(0, 30), sticky="nsew")
        self.log_container.grid_columnconfigure(0, weight=1)
        self.log_container.grid_rowconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(self.log_container, font=ctk.CTkFont(family="Consolas", size=13), fg_color="transparent", text_color="#00f2ff")
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Setup Logger
        self.usb_driver.set_logger(self.append_log)
        
        # Initial greeting
        self.append_log("--- Atas-K68D-Custom Console Initialized ---")

    def append_log(self, text):
        """Hàm nhận text từ driver và nhét vào ô text."""
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        
        # Nếu đang thao tác trên giao diện, cần dùng after để tránh lỗi thead
        def update():
            self.log_textbox.insert("end", timestamp + text + "\n")
            if self.auto_scroll_var.get():
                self.log_textbox.see("end")
                
        self.after(0, update)

    def clear_log(self):
        self.log_textbox.delete("1.0", "end")

    def save_log(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                initialfile=f"kblight_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if file_path:
                content = self.log_textbox.get("1.0", "end-1c")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo(self.master.i18n.t("console_msg_success_title"), self.master.i18n.t("console_msg_success_desc") + file_path)
        except Exception as e:
            messagebox.showerror(self.master.i18n.t("console_msg_error_title"), self.master.i18n.t("console_msg_error_desc") + str(e))
