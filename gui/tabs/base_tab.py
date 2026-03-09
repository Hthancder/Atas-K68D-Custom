import customtkinter as ctk

class BaseTab(ctk.CTkFrame):
    """Lớp cơ sở cho tất cả các tab trong ứng dụng, giúp dễ mở rộng."""
    def __init__(self, master, usb_driver, **kwargs):
        kwargs.setdefault('fg_color', 'transparent')
        super().__init__(master, **kwargs)
        self.usb_driver = usb_driver
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Ánh xạ tên chế độ gốc sang key i18n
        self._mode_i18n_keys = {
            "Wave Mode 1": "mode_wave_1",
            "Wave Light": "mode_wave_light",
            "Spectrum": "mode_spectrum",
            "Wave Mode 2": "mode_wave_2",
            "Mutant": "mode_mutant",
            "Breathe": "mode_breathe",
            "Fixed / Static": "mode_fixed",
            "Proliferate": "mode_proliferate",
            "One Line Radial": "mode_one_line_radial",
            "Shinning": "mode_shinning",
            "Ring Running": "mode_ring_running",
            "Runners Lamp": "mode_runners_lamp"
        }
        
    def get_localized_modes(self):
        """Trả về dict: { "Tên bản địa hóa": mã hex }"""
        from core.protocol import MODES
        return {self.master.i18n.t(self._mode_i18n_keys.get(k, k)): v for k, v in MODES.items()}
        
    def get_localized_mode_name(self, original_name):
        """Chuyển đổi tên tiếng Anh (trong config file) sang tên bản địa hóa để hiển thị lên UI."""
        key = self._mode_i18n_keys.get(original_name, original_name)
        return self.master.i18n.t(key)
        
    def get_hex_from_localized_name(self, localized_name):
        """Lấy mã hex từ tên bản địa hóa đang hiển thị trên UI."""
        loc_modes = self.get_localized_modes()
        # Default fallback to 0x06 (Fixed)
        return loc_modes.get(localized_name, 0x06)
        
    def get_original_name_from_localized(self, localized_name):
        """Lấy tên tiếng Anh nguyên bản để lưu vào file config."""
        from core.protocol import MODES
        loc_modes = self.get_localized_modes()
        hex_val = loc_modes.get(localized_name, 0x06)
        for orig, h in MODES.items():
            if h == hex_val:
                return orig
        return "Fixed / Static"

    def on_show(self):
        """Được gọi khi tab này được hiển thị."""
        pass
        
    def on_hide(self):
        """Được gọi khi người dùng chuyển sang tab khác."""
        pass
