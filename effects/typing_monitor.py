import threading
import time
from pynput import keyboard

class TypingMonitor(threading.Thread):
    def __init__(self, usb_driver, callback=None, mode_hex=0x06, decay=0.5, max_brightness=255, 
                 color_low=(0, 255, 255), color_mid=(255, 255, 0), color_high=(255, 0, 0), auto_color=False):
        super().__init__()
        self.usb_driver = usb_driver
        self.callback = callback
        self.running = False
        self.daemon = True
        self.key_presses = []
        self.last_update_time = 0
        self.update_interval = 0.5  # CHỈ CẬP NHẬT ĐÈN 2 LẦN / GIÂY (Tránh lag phím)
        self.last_wpm = -1
        self.current_r, self.current_g, self.current_b = 0, 0, 0
        
        self.set_config(mode_hex, decay, max_brightness, color_low, color_mid, color_high, auto_color)
        
    def set_config(self, mode_hex, decay, max_brightness, color_low, color_mid, color_high, auto_color=False):
        self.mode_hex = mode_hex
        self.decay = decay
        self.max_brightness = max_brightness
        self.color_low = color_low
        self.color_mid = color_mid
        self.color_high = color_high
        self.auto_color = auto_color

    def on_press(self, key):
        """Bắt sự kiện phím nhanh nhất có thể, chỉ lưu thời gian."""
        self.key_presses.append(time.time())

    def run(self):
        self.running = True
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        
        try:
            while self.running:
                now = time.time()
                
                # Dọn dẹp mảng: Giữ lại các lần bấm trong 5 giây gần nhất
                # Tối ưu: Chỉ giữ tối đa 100 lần bấm gần nhất để tránh mảng phình to (100 phím/5s = ~240 WPM)
                self.key_presses = [t for t in self.key_presses[-100:] if now - t <= 5.0]
                
                # Tính WPM (Word = ~5 ký tự). 
                cpm = len(self.key_presses) * (60 / 5) # Char per minute
                wpm = int(cpm / 5)
                
                # Fade out brightness if not typing based on decay
                time_since_last_press = now - (self.key_presses[-1] if self.key_presses else 0)
                if time_since_last_press > 0.5:
                    fade_ratio = max(0, 1.0 - (time_since_last_press - 0.5) / self.decay)
                else:
                    fade_ratio = 1.0
                    
                target_brightness = int(self.max_brightness * fade_ratio)

                # Chỉ xử lý và gửi USB nếu đã qua khoảng thời gian chờ (Rate Limit)
                if now - self.last_update_time >= self.update_interval:
                    self.last_update_time = now
                    
                    # Nội suy màu theo WPM (Chậm -> Vừa -> Nhanh)
                    # Giả định: Chậm < 40, Vừa < 80, Nhanh > 80
                    if wpm <= 40:
                        ratio = wpm / 40.0
                        r = int(self.color_low[0] * (1 - ratio) + self.color_mid[0] * ratio)
                        g = int(self.color_low[1] * (1 - ratio) + self.color_mid[1] * ratio)
                        b = int(self.color_low[2] * (1 - ratio) + self.color_mid[2] * ratio)
                    elif wpm <= 80:
                        ratio = (wpm - 40) / 40.0
                        r = int(self.color_mid[0] * (1 - ratio) + self.color_high[0] * ratio)
                        g = int(self.color_mid[1] * (1 - ratio) + self.color_high[1] * ratio)
                        b = int(self.color_mid[2] * (1 - ratio) + self.color_high[2] * ratio)
                    else:
                        r, g, b = self.color_high

                    self.current_r, self.current_g, self.current_b = r, g, b
                    
                    if self.callback:
                        # Cập nhật GUI qua thread an toàn
                        try:
                            self.callback(wpm, (r, g, b))
                        except:
                            pass
                    
                # Tối ưu hiệu suất: Gửi lệnh
                # Gửi xuống bàn phím kèm độ sáng fade out. Chỉ gửi nếu độ sáng thay đổi hoặc màu thay đổi.
                if hasattr(self, 'last_sent_brightness') and abs(self.last_sent_brightness - target_brightness) < 5 and wpm == self.last_wpm:
                    pass # Bỏ qua nếu không có sự thay đổi đáng kể
                else:
                    self.last_sent_brightness = target_brightness
                    self.last_wpm = wpm
                    
                    if target_brightness > 5:
                        self.usb_driver.apply_mode(self.mode_hex, (self.current_r, self.current_g, self.current_b), brightness=target_brightness, auto_color=self.auto_color)
                    else:
                        self.usb_driver.apply_mode(self.mode_hex, (0, 0, 0), brightness=0, auto_color=self.auto_color)
                
                # Ngủ ngắn để không ăn CPU, không chặn luồng gõ phím
                time.sleep(0.05) 
                
        finally:
            listener.stop()

    def stop(self):
        self.running = False

