import customtkinter as ctk
import time

class ToastNotification(ctk.CTkToplevel):
    def __init__(self, master, message, title="Thông báo", duration=5000):
        super().__init__(master)
        
        # Cấu hình cửa sổ borderless và luôn ở trên cùng
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0) # Bắt đầu từ trong suốt để tạo hiệu ứng fade-in
        self.configure(fg_color="#1e1e1e") # Khớp với sidebar color
        
        # Kích thước thông báo
        self.width = 320
        self.height = 80
        
        # Lấy kích thước màn hình
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Vị trí: Góc dưới bên phải, cách lề 20px
        self.end_x = screen_width - self.width - 20
        self.end_y = screen_height - self.height - 50 # Chừa chỗ cho taskbar
        self.start_y = self.end_y + 20 # Bắt đầu thấp hơn một chút để slide up
        
        self.geometry(f"{self.width}x{self.height}+{self.end_x}+{self.start_y}")
        
        # Layout nội dung
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Accent Border (Line mỏng bên trái màu Electric Blue)
        self.accent_frame = ctk.CTkFrame(self, width=4, corner_radius=0, fg_color="#00f2ff")
        self.accent_frame.grid(row=0, column=0, sticky="nsw")
        
        # Nội dung văn bản
        self.text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.text_frame.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        
        self.title_label = ctk.CTkLabel(self.text_frame, text=title.upper(), 
                                        font=ctk.CTkFont(size=12, weight="bold"), 
                                        text_color="#00f2ff", anchor="w")
        self.title_label.pack(fill="x", pady=(0, 2))
        
        self.msg_label = ctk.CTkLabel(self.text_frame, text=message, 
                                      font=ctk.CTkFont(size=13), 
                                      text_color="white", anchor="w", justify="left")
        self.msg_label.pack(fill="x")

        # Chạy hiệu ứng xuất hiện
        self.fade_in()
        
        # Tự đóng sau duration
        self.after(duration, self.fade_out)

    def fade_in(self):
        if not self.winfo_exists(): return
        alpha = self.attributes("-alpha")
        if alpha < 0.95:
            alpha += 0.05
            # Slide up nhẹ nhàng
            try:
                curr_geom = self.geometry().split("+")
                curr_y = int(curr_geom[2])
                if curr_y > self.end_y:
                    curr_y -= 1
                
                self.geometry(f"{self.width}x{self.height}+{self.end_x}+{curr_y}")
                self.attributes("-alpha", alpha)
                self.after(10, self.fade_in)
            except: pass

    def fade_out(self):
        if not self.winfo_exists(): return
        try:
            alpha = self.attributes("-alpha")
            if alpha > 0:
                alpha -= 0.05
                self.attributes("-alpha", alpha)
                self.after(10, self.fade_out)
            else:
                self.destroy()
        except: pass
