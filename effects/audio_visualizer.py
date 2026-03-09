import threading
import time
import numpy as np
import colorsys
try:
    import pyaudiowpatch as pyaudio
except ImportError:
    pyaudio = None

class AudioVisualizer(threading.Thread):
    def __init__(self, usb_driver, effect_type="freq_colors", sensitivity=1.0, 
                 mode_hex=0x06, bass_mult=1.0, mid_mult=1.0, treble_mult=1.0, 
                 attack=0.8, decay=0.2, noise_gate=10, fps=20, max_brightness=255, min_brightness=0,
                 bass_color=(255, 0, 0), mid_color=(0, 255, 0), treble_color=(0, 0, 255),
                 auto_gain=False, auto_saturation=True,
                 silent_mode_hex=0x06, silent_color=(255, 255, 255), silent_auto_color=False,
                 silence_timeout=0.5,
                 gui_callback=None):
        super().__init__()
        self.usb_driver = usb_driver
        self.running = False
        self.daemon = True
        self.gui_callback = gui_callback
        
        self.set_config(effect_type, sensitivity, mode_hex, bass_mult, mid_mult, treble_mult, attack, decay, noise_gate, fps, max_brightness, min_brightness, bass_color, mid_color, treble_color, auto_gain, auto_saturation, silent_mode_hex, silent_color, silent_auto_color, silence_timeout)
        
        # Pre-compute FFT window to avoid recalculation
        self.precomputed_window = {}
        self.current_chunk_size = 1024
        
    def set_config(self, effect_type, sensitivity, mode_hex=0x06, bass_mult=1.0, mid_mult=1.0, treble_mult=1.0, 
                   attack=0.8, decay=0.2, noise_gate=10, fps=20, max_brightness=255, min_brightness=0,
                   bass_color=(255, 0, 0), mid_color=(0, 255, 0), treble_color=(0, 0, 255),
                   auto_gain=False, auto_saturation=True,
                   silent_mode_hex=0x06, silent_color=(255, 255, 255), silent_auto_color=False,
                   silence_timeout=0.5):
        self.effect_type = effect_type
        self.sensitivity = sensitivity
        self.mode_hex = mode_hex
        self.bass_mult = bass_mult
        self.mid_mult = mid_mult
        self.treble_mult = treble_mult
        self.attack = attack
        self.decay = decay
        self.noise_gate = noise_gate
        self.fps = max(1, fps)
        self.max_brightness = max(0, min(255, max_brightness))
        self.min_brightness = max(0, min(255, min_brightness))
        self.bass_color = bass_color
        self.mid_color = mid_color
        self.treble_color = treble_color
        self.auto_gain = auto_gain
        self.auto_saturation = auto_saturation
        self.silent_mode_hex = silent_mode_hex
        self.silent_color = silent_color
        self.silent_auto_color = silent_auto_color
        self.silence_timeout = max(0.0, silence_timeout)

    def _get_window(self, chunk_size):
        """Get precomputed window for given chunk size, create if needed"""
        if chunk_size not in self.precomputed_window:
            self.precomputed_window[chunk_size] = np.hanning(chunk_size)
        return self.precomputed_window[chunk_size]

    def _compute_fft_optimized(self, audio_data):
        """Optimized FFT computation with precomputed window"""
        chunk_size = len(audio_data)
        window = self._get_window(chunk_size)
        fft_result = np.fft.rfft(audio_data * window)
        # Compute magnitude and normalize in one step
        return np.abs(fft_result) / (chunk_size * 256.0)

    def run(self):
        if not pyaudio:
            print("[Lỗi] Thư viện pyaudiowpatch chưa được cài đặt. Vui lòng cài đặt: pip install pyaudiowpatch")
            return
            
        self.running = True
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        
        p = pyaudio.PyAudio()
        
        try:
            # Tìm thiết bị xuất âm thanh mặc định (Loa) thông qua WASAPI
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            # Tìm loopback tương ứng với thiết bị loa này
            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                        
            # Lấy thông số chuẩn của thiết bị
            CHANNELS = default_speakers["maxInputChannels"]
            RATE = int(default_speakers["defaultSampleRate"])
            
            print(f"Đang thu âm hệ thống qua: {default_speakers['name']} (Rate: {RATE}, Channels: {CHANNELS})")

            # Mở luồng thu âm Loopback
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            input_device_index=default_speakers["index"],
                            frames_per_buffer=CHUNK)
            
            # Gửi gói tin khởi tạo ngay lập tức (Silent mode) sau khi mở luồng
            sr, sg, sb = self.silent_color
            self.usb_driver.apply_mode(self.silent_mode_hex, (sr, sg, sb), brightness=self.min_brightness, speed=1, auto_color=self.silent_auto_color)

            last_update_time = 0
            
            # Biến để làm mượt chuyển màu (Exponential Smoothing)
            smooth_r, smooth_g, smooth_b = 0.0, 0.0, 0.0
            
            hue = 0.0
            last_audio_time = time.time()

            while self.running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    # Nếu có nhiều kênh (stereo), gộp lại thành 1 để tính toán dễ hơn
                    if CHANNELS > 1:
                        audio_data = audio_data[::CHANNELS]
                    
                    now = time.time()
                    update_interval = 1.0 / self.fps
                    if now - last_update_time >= update_interval:
                        last_update_time = now
                        
                        target_r, target_g, target_b = 0, 0, 0
                        
                        # --- Tính toán RMS cơ bản và Auto Gain Control ---
                        rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
                        
                        if rms > self.noise_gate:
                            last_audio_time = now # Cập nhật thời điểm cuối có tiếng

                        if getattr(self, 'auto_gain', False):
                            if rms > 500: # Chỉ tự động chỉnh khi có tiếng nhạc rõ ràng (tránh nhiễu)
                                # Ta muốn rms * sensitivity ~ 8000
                                target_sens = 8000.0 / rms
                                target_sens = max(0.2, min(5.0, target_sens)) # Giới hạn dải nhạy
                                # Làm mượt sự thay đổi độ nhạy
                                self.sensitivity = self.sensitivity * 0.98 + target_sens * 0.02
                        
                        if self.effect_type == "volume_pulse":
                            # Tính RMS để lấy âm lượng và tạo độ cong để LED nhảy rõ rệt hơn
                            rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
                            base_vol = (rms / 12000.0) * self.sensitivity * self.bass_mult
                            base_vol = min(1.0, base_vol**1.5) # Curve to make peaks stand out
                            target_brightness = int(base_vol * 255)
                            
                            # Nháy theo màu Bass tùy chọn thay vì xanh/đỏ cố định
                            br, bg, bb = self.bass_color
                            target_r = int(br * (target_brightness / 255))
                            target_g = int(bg * (target_brightness / 255))
                            target_b = int(bb * (target_brightness / 255))
                            
                        elif self.effect_type in ["freq_colors", "rainbow_bass", "dual_band_bt", "fire_effect", "smart_pitch"] or self.effect_type.startswith("band_"):
                            # Tính toán FFT một cách tối ưu
                            fft_magnitude = self._compute_fft_optimized(audio_data)
                            
                            # Phân tách chi tiết 7 dải tần (Điều chỉnh lại bin ranges và multiplier)
                            # Mỗi bin ~43-47Hz với RATE 44.1k/48k và CHUNK 1024
                            b_sub_bass = np.mean(fft_magnitude[1:3]) * self.sensitivity * 2.0 * self.bass_mult    # 40 - 130Hz (Giảm mạnh)
                            b_bass     = np.mean(fft_magnitude[3:6]) * self.sensitivity * 2.5 * self.bass_mult    # 130 - 250Hz (Giảm mạnh)
                            b_low_mid  = np.mean(fft_magnitude[6:12]) * self.sensitivity * 5.0 * self.mid_mult    # 250 - 500Hz
                            b_mid      = np.mean(fft_magnitude[12:46]) * self.sensitivity * 8.0 * self.mid_mult   # 500 - 2kHz
                            b_up_mid   = np.mean(fft_magnitude[46:92]) * self.sensitivity * 10.0 * self.mid_mult  # 2k - 4kHz
                            b_presence = np.mean(fft_magnitude[92:138]) * self.sensitivity * 15.0 * self.treble_mult # 4k - 6kHz
                            b_brill    = np.mean(fft_magnitude[138:300]) * self.sensitivity * 25.0 * self.treble_mult # 6k - 13kHz

                            # Áp dụng A-Weighting mềm hơn để các dải vẫn nổi bật
                            a_weighting = np.array([0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8]) # Giảm bass, tăng bổng
                            b_sub_bass *= a_weighting[0]; b_bass *= a_weighting[1]
                            b_low_mid *= a_weighting[2]; b_mid *= a_weighting[3]; b_up_mid *= a_weighting[4]
                            b_presence *= a_weighting[5]; b_brill *= a_weighting[6]

                            # Normalize bằng hàm mũ (Curve) để nén các giá trị lớn (tránh chạm nóc liên tục)
                            # và khuếch đại nhẹ các giá trị nhỏ.
                            def curve_val(v): 
                                # Logarithmic compression (giống tai người)
                                return np.clip(np.log10(1 + v * 9), 0, 1.0)  # Using clip instead of min for better performance
                            
                            b_sub_bass = curve_val(b_sub_bass)
                            b_bass = curve_val(b_bass)
                            b_low_mid = curve_val(b_low_mid)
                            b_mid = curve_val(b_mid)
                            b_up_mid = curve_val(b_up_mid)
                            b_presence = curve_val(b_presence)
                            b_brill = curve_val(b_brill)

                            # Gom nhóm
                            bass = max(b_sub_bass, b_bass)
                            mid = max(b_low_mid, b_mid, b_up_mid)
                            treble = max(b_presence, b_brill)

                            if self.effect_type == "freq_colors":
                                # Trộn màu Bass, Mid, Treble tùy chọn
                                br, bg, bb = self.bass_color
                                mr, mg, mb = self.mid_color
                                tr, tg, tb = self.treble_color
                                
                                target_r = min(255, int(bass*br + mid*mr + treble*tr))
                                target_g = min(255, int(bass*bg + mid*mg + treble*tg))
                                target_b = min(255, int(bass*bb + mid*mb + treble*tb))
                            
                            elif self.effect_type == "dual_band_bt":
                                br, bg, bb = self.bass_color
                                tr, tg, tb = self.treble_color
                                target_r = min(255, int(bass*br + treble*tr))
                                target_g = min(255, int(bass*bg + treble*tg))
                                target_b = min(255, int(bass*bb + treble*tb))

                            elif self.effect_type == "band_subbass":
                                br, bg, bb = self.bass_color
                                target_r, target_g, target_b = int(br*b_sub_bass), int(bg*b_sub_bass), int(bb*b_sub_bass)
                            elif self.effect_type == "band_bass":
                                br, bg, bb = self.bass_color
                                target_r, target_g, target_b = int(br*b_bass), int(bg*b_bass), int(bb*b_bass)
                            elif self.effect_type == "band_lowmid":
                                mr, mg, mb = self.mid_color
                                target_r, target_g, target_b = int(mr*b_low_mid), int(mg*b_low_mid), int(mb*b_low_mid)
                            elif self.effect_type == "band_mid":
                                mr, mg, mb = self.mid_color
                                target_r, target_g, target_b = int(mr*b_mid), int(mg*b_mid), int(mb*b_mid)
                            elif self.effect_type == "band_uppermid":
                                mr, mg, mb = self.mid_color
                                target_r, target_g, target_b = int(mr*b_up_mid), int(mg*b_up_mid), int(mb*b_up_mid)
                            elif self.effect_type == "band_treble":
                                tr, tg, tb = self.treble_color
                                target_r, target_g, target_b = int(tr*b_brill), int(tg*b_brill), int(tb*b_brill)
                            
                            elif self.effect_type == "rainbow_bass":
                                hue = (hue + (bass * 0.15)) % 1.0
                                total_vol = min(1.0, (bass + mid + treble) / 2.5)
                                if total_vol > 0.05:
                                    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, total_vol)
                                    target_r, target_g, target_b = int(r*255), int(g*255), int(b*255)
                                else: target_r, target_g, target_b = 0, 0, 0
                                
                            elif self.effect_type == "fire_effect":
                                energy = (bass * 0.7 + mid * 0.3)
                                target_r = min(255, int(energy * 255))
                                target_g = min(255, int(energy * 100)) # Cam/Vàng
                                target_b = 0
                                
                            elif self.effect_type == "strobe_police":
                                # Đổi màu Đỏ/Xanh mỗi khi Bass đập mạnh
                                if bass > 0.4:
                                    if not hasattr(self, '_police_toggle'): self._police_toggle = True
                                    self._police_toggle = not self._police_toggle
                                    if self._police_toggle:
                                        target_r, target_b = 255, 0
                                    else:
                                        target_r, target_b = 0, 255
                                    target_g = 0
                                else:
                                    target_r, target_g, target_b = 0, 0, 0
                                    
                            elif self.effect_type == "smart_pitch":
                                # Màu thông minh theo cao độ (Spectral Centroid)
                                sum_mag = np.sum(fft_magnitude)
                                if sum_mag > 0.1:
                                    # Create array of indices (each index corresponds to a frequency bin)
                                    indices = np.arange(len(fft_magnitude))
                                    centroid_idx = np.sum(indices * fft_magnitude) / sum_mag
                                    
                                    # Caculate approximate frequency (RATE=48000, CHUNK=1024 -> ~47Hz per bin)
                                    freq = centroid_idx * (RATE / CHUNK)
                                    
                                    # Logarithmic mapping (50Hz to 10000Hz)
                                    log_freq = np.log10(max(50.0, min(10000.0, float(freq))))
                                    normalized_pitch = (log_freq - np.log10(50.0)) / (np.log10(10000.0) - np.log10(50.0))
                                    
                                    # Hue range: 0.0 (Red) to 0.8 (Purple)
                                    target_hue = float(normalized_pitch) * 0.8
                                    
                                    if not hasattr(self, 'smooth_hue'): 
                                        self.smooth_hue = target_hue
                                    
                                    # Smooth hue transition slowly (0.95 momentum)
                                    self.smooth_hue = self.smooth_hue * 0.95 + target_hue * 0.05
                                    
                                    # Volume drives brightness
                                    total_vol = min(1.0, float((bass + mid + treble) / 2.5))
                                    
                                    r_hsv, g_hsv, b_hsv = colorsys.hsv_to_rgb(self.smooth_hue, 1.0, total_vol)
                                    target_r, target_g, target_b = int(r_hsv*255), int(g_hsv*255), int(b_hsv*255)
                                else:
                                    target_r, target_g, target_b = 0, 0, 0

                        # Áp dụng Noise Gate (Lọc ồn)
                        if rms < self.noise_gate:
                            target_r, target_g, target_b = 0, 0, 0

                        # Gửi dữ liệu phổ nhạc lên GUI nếu có callback
                        if self.gui_callback:
                            try:
                                # Tạo 32 dải (bands) cho visualizer trên giao diện
                                bands = []
                                num_bands = 32
                                factor = len(fft_magnitude) ** (1/num_bands)
                                for i in range(num_bands):
                                    start = int(factor**i)
                                    end = int(factor**(i+1))
                                    # Lấy trung bình và uốn cong giống logic chính
                                    val = np.mean(fft_magnitude[start:end]) * self.sensitivity * 5
                                    val = np.clip(np.log10(1 + val * 9), 0, 1.0) # Logarithmic compression with clip
                                    
                                    # Cắt nhiễu trên UI luôn
                                    if rms < self.noise_gate: val = 0
                                    bands.append(val)
                                self.gui_callback(bands)
                            except: pass

                        # --- Tự động đậm/nhạt màu theo âm lượng (Auto Saturation) ---
                        if getattr(self, 'auto_saturation', True) and (target_r > 0 or target_g > 0 or target_b > 0):
                            # Chuyển đổi RGB sang HSV để chỉnh Saturation
                            h, s, v = colorsys.rgb_to_hsv(target_r/255.0, target_g/255.0, target_b/255.0)
                            
                            # v ở đây chính là độ sáng/cường độ của dải âm (từ 0.0 đến 1.0)
                            # Nếu v nhỏ (âm thanh yếu) -> s nhỏ (màu nhạt/trắng)
                            # Nếu v lớn (âm thanh mạnh) -> s lớn (màu đậm đà, tối đa 1.0)
                            # Công thức: s_new = s * min(1.0, 0.2 + 0.8 * (v ** 0.5))
                            # Giúp âm yếu không bị chói, âm mạnh thì rực rỡ (TỐT NHẤT)
                            adjusted_s = s * min(1.0, 0.2 + 0.8 * (v ** 0.5))
                            
                            r_new, g_new, b_new = colorsys.hsv_to_rgb(h, adjusted_s, v)
                            target_r, target_g, target_b = int(r_new*255), int(g_new*255), int(b_new*255)

                        # Smooth filter: Attack & Decay
                        if target_r > smooth_r: smooth_r = smooth_r * (1 - self.attack) + target_r * self.attack
                        else: smooth_r = smooth_r * (1 - self.decay) + target_r * self.decay
                        
                        if target_g > smooth_g: smooth_g = smooth_g * (1 - self.attack) + target_g * self.attack
                        else: smooth_g = smooth_g * (1 - self.decay) + target_g * self.decay
                        
                        if target_b > smooth_b: smooth_b = smooth_b * (1 - self.attack) + target_b * self.attack
                        else: smooth_b = smooth_b * (1 - self.decay) + target_b * self.decay
                        
                        r, g, b = int(smooth_r), int(smooth_g), int(smooth_b)
                        
                        max_val = max(r, g, b)
                        
                        # Có tín hiệu nếu max_val > 5 HOẶC thời gian im lặng chưa vượt quá timeout
                        is_silent = (now - last_audio_time) > self.silence_timeout

                        if max_val > 5 and not is_silent:
                            # Tỉ lệ cường độ cao nhất hiện tại (0.0 đến 1.0)
                            intensity_ratio = max_val / 255.0
                            
                            # Căng độ sáng trong khoảng min_brightness đến max_brightness
                            # Nếu bật auto_saturation, giữ độ sáng cao hơn để ưu tiên hiển thị sự thay đổi màu sắc
                            if getattr(self, 'auto_saturation', True):
                                # Nâng mức sáng tối thiểu lên 65% của max_brightness
                                floor_bright = max(self.min_brightness, int(self.max_brightness * 0.65))
                                dyn_bright = int(floor_bright + intensity_ratio * (self.max_brightness - floor_bright))
                            else:
                                dyn_bright = int(self.min_brightness + intensity_ratio * (self.max_brightness - self.min_brightness))
                                
                            dyn_bright = max(self.min_brightness, min(self.max_brightness, dyn_bright))
                            
                            self.usb_driver.apply_mode(self.mode_hex, (r, g, b), brightness=dyn_bright, speed=1, auto_color=False)
                        elif is_silent:
                            # Khi im lặng thực sự (đã qua thời gian chờ)
                            if self.min_brightness > 0:
                                sr, sg, sb = self.silent_color
                                self.usb_driver.apply_mode(self.silent_mode_hex, (sr, sg, sb), brightness=self.min_brightness, speed=1, auto_color=self.silent_auto_color)
                            else:
                                self.usb_driver.apply_mode(self.silent_mode_hex, (0, 0, 0), brightness=0, speed=1, auto_color=False)
                        else:
                            # Đang trong thời gian chờ im lặng, giữ nguyên trạng thái hoặc giảm dần nhẹ
                            pass
                            
                except IOError:
                    pass
                except Exception as e:
                    print(f"Lỗi trong vòng lặp visualizer: {e}")
                    time.sleep(0.1)
                
        except Exception as e:
            print(f"Lỗi khởi tạo Audio Visualizer (có thể không hỗ trợ WASAPI Loopback): {e}")
        finally:
            self.running = False
            if 'stream' in locals() and stream.is_active():
                stream.stop_stream()
                stream.close()
            p.terminate()

    def stop(self):
        self.running = False
