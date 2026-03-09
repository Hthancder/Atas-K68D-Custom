# Danh sách 12 Chế độ LED chuẩn xác (Từ 0x00 đến 0x0B)
MODES = {
    "Wave Mode 1": 0x00,
    "Wave Light": 0x01,
    "Spectrum": 0x02,
    "Wave Mode 2": 0x03,
    "Mutant": 0x04,
    "Breathe": 0x05,
    "Fixed / Static": 0x06,
    "Proliferate": 0x07,
    "One Line Radial": 0x08,
    "Shinning": 0x09,
    "Ring Running": 0x0A,
    "Runners Lamp": 0x0B
}

def create_packet(payload: list) -> list:
    """Tạo một gói tin 64 byte hợp lệ (thêm padding 0x00)."""
    packet = list(payload)
    while len(packet) < 64:
        packet.append(0x00)
    return packet[:64]

def build_handshake_1() -> list:
    return create_packet([0x55, 0x01])

def build_handshake_2() -> list:
    return create_packet([0x55, 0x05, 0x00, 0x20, 0x20])

def build_end_sequence() -> list:
    return create_packet([0x55, 0x02])

def build_mode_command(mode_id: int, r: int, g: int, b: int, brightness: int = 255, speed: int = 1, auto_color: bool = True) -> list:
    """
    Xây dựng gói tin lệnh chính (55 06).
    - Index 10: Mode ID (0x00 - 0x0B)
    - Index 11: Độ sáng (Brightness: 0 - 255)
    - Index 12: Tốc độ (Speed: 1-4)
    - Index 14: Biến thể (0x01 thường là Auto Color hoặc hướng chạy, 0x00 là Static)
    """
    payload = [0x00] * 64
    
    # Header
    payload[0] = 0x55
    payload[1] = 0x06
    payload[2] = 0x00
    
    # Prefix
    payload[4] = 0x20
    
    # Ép buộc Tốc độ = 1 đối với các chế độ không cho phép đổi tốc độ.
    # Nếu gửi sai, bàn phím sẽ vứt bỏ gói tin -> Lỗi "Có mode không hoạt động"
    FIXED_SPEED_MODES = [0x04, 0x05, 0x06, 0x07, 0x08, 0x09]
    if mode_id in FIXED_SPEED_MODES:
        speed = 0x01
    
    # Configuration
    payload[10] = mode_id
    payload[11] = brightness
    payload[12] = speed
    payload[13] = 0x00 # Hướng chạy mặc định
    
    # Bật tắt đổi màu tự động / Biến thể
    payload[14] = 0x01 if auto_color else 0x00
    
    # Colors
    payload[16] = r
    payload[17] = g
    payload[18] = b
    
    # CHECKSUM = Tổng của Index 4 đến 63 & 0xFF
    checksum = sum(payload[4:64]) & 0xFF
    payload[3] = checksum
    
    return payload






