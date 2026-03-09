import hid
import time
import threading
from core import protocol

class USBDriver:
    def __init__(self, vid=None, pid=None):
        self.vid = vid
        self.pid = pid
        self.device = None
        self.connected = False
        self.log_callback = None
        self.delay_time = 0.01 # Mặc định 0.01s (10ms)
        self.lock = threading.Lock() # Thêm Lock để tránh xung đột dữ liệu giữa các thread
        
        # Thêm biến để theo dõi thời gian kết nối và chuỗi thử nghiệm
        self.last_successful_send = time.time()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2  # Giây
        self.auto_reconnect_enabled = True  # Cho phép bật/tắt tính năng tự động kết nối lại

    def set_logger(self, callback):
        """Gắn hàm callback để in log ra GUI."""
        self.log_callback = callback

    def log(self, message):
        """Hàm in log nội bộ và đẩy ra GUI."""
        print(f"[USB] {message}")
        if self.log_callback:
            self.log_callback(message)

    def auto_detect_and_connect(self, target_vid=0x5566, target_pid=0x000A):
        """Tự động quét và tìm đúng cổng Vendor-Defined (0xFF00) của bàn phím."""
        self.log(f"Đang quét tìm thiết bị VID: {hex(target_vid)} PID: {hex(target_pid)}...")
        
        target_path = None
        devices = hid.enumerate()
        
        for d in devices:
            if d['vendor_id'] == target_vid and d['product_id'] == target_pid:
                usage_page = d.get('usage_page', 0)
                usage = d.get('usage', 0)
                path = d['path']
                
                self.log(f"Tìm thấy Interface: UP={hex(usage_page)} U={hex(usage)} Path={path}")
                
                # Bàn phím custom thường dùng Usage Page 0xFF00 (Vendor Defined)
                if usage_page == 0xff00:
                    target_path = path
                    self.log(f"-> CHỌN GIAO DIỆN VENDOR-DEFINED NÀY!")
                    break

        if not target_path:
            self.connected = False
            return False, "Không tìm thấy cổng điều khiển LED (Usage Page 0xFF00) của bàn phím."

        try:
            self.device = hid.device()
            self.device.open_path(target_path)
            self.device.set_nonblocking(True)
            self.vid = target_vid
            self.pid = target_pid
            self.connected = True
            self.reconnect_attempts = 0  # Reset số lần thử lại khi kết nối thành công
            
            # Gửi thử 1 lệnh handshake để xem có lỗi không
            self.send_packet(protocol.build_handshake_1())
            
            return True, f"Kết nối THÀNH CÔNG tới Path: {target_path}"
        except Exception as e:
            self.connected = False
            self.device = None
            return False, f"Lỗi mở thiết bị: {str(e)}"

    def reconnect_if_needed(self, target_vid=0x5566, target_pid=0x000A):
        """Tự động thử kết nối lại nếu phát hiện mất kết nối."""
        if not self.auto_reconnect_enabled:
            return False
            
        if not self.connected or self.device is None:
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                self.log(f"Đang thử kết nối lại lần {self.reconnect_attempts}/{self.max_reconnect_attempts}...")
                
                # Chờ một chút trước khi thử lại
                time.sleep(self.reconnect_delay)
                
                success, message = self.auto_detect_and_connect(target_vid, target_pid)
                if success:
                    self.log("Kết nối lại THÀNH CÔNG!")
                    self.reconnect_attempts = 0  # Reset attempts counter
                    return True
                else:
                    self.log(f"Thử lại thất bại: {message}")
            else:
                self.log("Đã vượt quá số lần thử lại tối đa. Ngừng thử kết nối lại.")
        return False

    def send_packet(self, packet: list, retries=3):
        """Gửi gói 64-byte qua HID API."""
        if not self.connected or self.device is None:
            # Thử kết nối lại nếu bị mất kết nối
            if self.reconnect_if_needed():
                # Sau khi kết nối lại thành công, thử gửi lại
                try:
                    # Report ID = 0x00, độ dài tổng cộng 65 byte
                    data_to_send = [0x00] + packet
                    
                    for attempt in range(retries):
                        bytes_written = self.device.write(data_to_send)
                        
                        if bytes_written != -1:
                            self.last_successful_send = time.time()  # Cập nhật thời gian gửi thành công
                            return True
                        
                        # Nếu trả về -1 (tràn bộ đệm USB), đợi một chút rồi thử lại
                        time.sleep(0.005)
                        
                    self.log("Cảnh báo: Hàm write trả về -1 liên tục (Tràn bộ đệm USB hoặc sai cổng)")
                    return False
                except Exception as e:
                    self.log(f"LỖI gửi dữ liệu HID sau khi kết nối lại: {e}")
                    self.connected = False 
                    self.device = None
                    return False
            else:
                return False
            
        try:
            # Report ID = 0x00, độ dài tổng cộng 65 byte
            data_to_send = [0x00] + packet
            
            for attempt in range(retries):
                bytes_written = self.device.write(data_to_send)
                
                if bytes_written != -1:
                    self.last_successful_send = time.time()  # Cập nhật thời gian gửi thành công
                    return True
                
                # Nếu trả về -1 (tràn bộ đệm USB), đợi một chút rồi thử lại
                time.sleep(0.005)
                
            self.log("Cảnh báo: Hàm write trả về -1 liên tục (Tràn bộ đệm USB hoặc sai cổng)")
            return False
        except Exception as e:
            self.log(f"LỖI gửi dữ liệu HID: {e}")
            # Nếu lỗi phần cứng (như rút cáp), đánh dấu ngắt kết nối
            self.connected = False 
            self.device = None
            
            # Thử kết nối lại tự động
            self.reconnect_if_needed()
            return False

    def apply_mode(self, mode_hex: int, color: tuple, brightness: int = 4, speed: int = 1, auto_color: bool = True):
        """Thực thi quy trình 4 bước như trong Log. Sử dụng Lock để an toàn với Thread."""
        with self.lock:
            r, g, b = color
            
            self.send_packet(protocol.build_handshake_1())
            time.sleep(self.delay_time) 
            
            self.send_packet(protocol.build_handshake_2())
            time.sleep(self.delay_time)
            
            # Gửi Mode, Color, Brightness, Speed và Auto Color
            self.send_packet(protocol.build_mode_command(mode_hex, r, g, b, brightness, speed, auto_color))
            time.sleep(self.delay_time)
            
            self.send_packet(protocol.build_end_sequence())

    def close(self):
        self.auto_reconnect_enabled = False  # Tắt cơ chế tự động kết nối khi đóng
        if self.device:
            self.device.close()
            self.connected = False
            self.log("Đã đóng kết nối.")
