import os
import json
import glob

from core.utils import get_base_dir

class I18n:
    def __init__(self, settings_file_path):
        self.settings_file = settings_file_path
        self.current_lang = "vi" # Default fallback
        self.translations = {}
        self.available_langs = {} # { "vi": {"name": "Tiếng Việt", "author": "System"} }
        
        # Thư mục chứa các file ngôn ngữ (ngang hàng với core/)
        base_dir = get_base_dir()
        self.lang_dir = os.path.join(base_dir, 'languages')
        
        self.load_external_languages()
        self.load_lang_preference()

    def load_external_languages(self):
        """Quét thư mục languages và nạp tất cả các file .json (ngoại trừ template)."""
        self.translations.clear()
        self.available_langs.clear()
        
        if not os.path.exists(self.lang_dir):
            try:
                os.makedirs(self.lang_dir)
            except:
                pass
            return
            
        json_files = glob.glob(os.path.join(self.lang_dir, "*.json"))
        
        for file_path in json_files:
            filename = os.path.basename(file_path)
            # Bỏ qua các file template
            if "template" in filename.lower():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                meta = data.get("_meta", {})
                code = meta.get("code")
                trans = data.get("translations", {})
                
                if code and trans:
                    self.translations[code] = trans
                    self.available_langs[code] = {
                        "name": meta.get("name", filename.replace('.json', '')),
                        "author": meta.get("author", "Unknown")
                    }
            except Exception as e:
                print(f"[I18n] Lỗi đọc file ngôn ngữ {filename}: {e}")

    def get_available_languages(self):
        """Trả về dictionary metadata các ngôn ngữ hiện có."""
        return self.available_langs

    def load_lang_preference(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Chỉ áp dụng nếu ngôn ngữ trong settings.json thực sự tồn tại
                    saved_lang = settings.get("language", "vi")
                    if saved_lang in self.translations:
                        self.current_lang = saved_lang
                    elif "vi" in self.translations:
                        self.current_lang = "vi"
                    elif "en" in self.translations:
                        self.current_lang = "en"
                    elif self.translations:
                        self.current_lang = list(self.translations.keys())[0]
        except:
            if "vi" in self.translations:
                self.current_lang = "vi"
            elif self.translations:
                self.current_lang = list(self.translations.keys())[0]

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.current_lang = lang_code
            try:
                settings = {}
                if os.path.exists(self.settings_file):
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                settings["language"] = lang_code
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
            except Exception as e:
                print(f"[I18n] Error saving language: {e}")

    def t(self, key):
        """Translate a key to the current language. Fallback to English, then the key itself."""
        lang_dict = self.translations.get(self.current_lang, {})
        en_dict = self.translations.get("en", {})
        
        # 1. Thử ngôn ngữ hiện tại
        if key in lang_dict:
            return lang_dict[key]
        # 2. Fallback sang tiếng Anh nếu thiếu
        elif key in en_dict:
            return en_dict[key]
        # 3. Trả về chính key
        return key
