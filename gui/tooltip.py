import tkinter as tk
import customtkinter as ctk

class ToolTip:
    """
    Tạo Balloon Tooltip cho các widget trong CustomTkinter.
    """
    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.id = None
        self.tw = None
        self.widget.bind("<Enter>", self.schedule, add="+")
        self.widget.bind("<Leave>", self.hide, add="+")
        self.widget.bind("<ButtonPress>", self.hide, add="+")

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        self.unschedule()
        if self.tw:
            return
        
        # Lấy tọa độ của widget
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Sử dụng tk.Toplevel để không làm mất focus của cửa sổ chính
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.attributes('-topmost', True)
        
        # Lấy theme hiện tại để tooltip tự đồng bộ màu sắc
        mode = ctk.get_appearance_mode()
        bg_color = "#2b2b2b" if mode == "Dark" else "#e0e0e0"
        fg_color = "#ffffff" if mode == "Dark" else "#000000"
        border_color = "#555555" if mode == "Dark" else "#aaaaaa"

        # Khung label
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background=bg_color, foreground=fg_color,
                         relief='solid', borderwidth=1, highlightbackground=border_color,
                         font=("Segoe UI", 9))
        label.pack(ipadx=6, ipady=4)

    def hide(self, event=None):
        self.unschedule()
        if self.tw:
            self.tw.destroy()
            self.tw = None
