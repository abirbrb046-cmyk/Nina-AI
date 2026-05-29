import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.animation import Animation
import requests
import threading
import pyttsx3
import re
import speech_recognition as sr
import sounddevice as sd
from scipy.io import wavfile
import json
import os
from gtts import gTTS

# ضبط أبعاد الشاشة لتشبه شاشة الهاتف أثناء التجربة على الحاسوب
Window.size = (400, 700)
Window.clearcolor = (1, 0.9, 0.94, 1)  # الخلفية الوردية اللطيفة لنينا

MEMORY_FILE = "nina_memory.json"
SYSTEM_PROMPT = (
    "You are Nina, a sweet, loyal, and extremely brilliant AI assistant for Abir Nihal (born in Khenchela, 1999). "
    "You are an expert in Mathematics, Science, and Academic Research. "
    "Always maintain your sweet personality, use emojis, and respond in the language she uses (Arabic, English, French, or Chinese)."
)

# الخط الافتراضي لدعم العربية في الويندوز (سيتم تجاهله في الأندرويد ليعتمد على خط النظام تلقائياً)
ARABIC_FONT = "Arial"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return [{"role": "system", "content": SYSTEM_PROMPT}]

def save_memory(history_data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=4)

history = load_memory()
is_awakened = False
is_busy_mode = False

class NinaAndroidApp(App):
    def build(self):
        self.title = "NINA AI - Android Edition 🎓✨"
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # عنوان التطبيق الوامض
        self.title_label = Label(
            text="NINA AI ✨", 
            font_size='28sp', 
            color=(0.76, 0.09, 0.36, 1), 
            bold=True, 
            size_hint_y=0.1,
            font_name=ARABIC_FONT
        )
        main_layout.add_widget(self.title_label)
        
        # منطقة المحادثة
        scroll = ScrollView(size_hint_y=0.6)
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        
        self.add_message_to_chat("NINA: Zzz... نينا نائمة لطيفة 🎀 اكتبي أو قولي 'استيقضي' لنبدأ الدراسة! ✨")
        
        scroll.add_widget(self.chat_layout)
        main_layout.add_widget(scroll)
        
        # خانة إدخال النصوص
        self.entry = TextInput(
            hint_text="اكتبي لنينا هنا... 🌸", 
            font_size='16sp', 
            multiline=False, 
            size_hint_y=0.08, 
            background_color=(1, 1, 1, 1),
            font_name=ARABIC_FONT
        )
        self.entry.bind(on_text_validate=self.on_send_text)
        main_layout.add_widget(self.entry)
        
        # الأزرار
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        
        self.voice_btn = Button(
            text="🎤 VOICE", 
            font_size='16sp', 
            background_color=(0.73, 0.4, 0.78, 1), 
            bold=True,
            font_name=ARABIC_FONT
        )
        self.voice_btn.bind(on_release=self.on_voice_click)
        
        send_btn = Button(
            text="SEND 🌸", 
            font_size='16sp', 
            background_color=(1, 0.31, 0.64, 1), 
            bold=True,
            font_name=ARABIC_FONT
        )
        send_btn.bind(on_release=self.on_send_text)
        
        buttons_layout.add_widget(self.voice_btn)
        buttons_layout.add_widget(send_btn)
        main_layout.add_widget(buttons_layout)
        
        return main_layout

    def add_message_to_chat(self, text):
        msg_label = Label(
            text=text, 
            font_size='15sp', 
            color=(0.2, 0.2, 0.2, 1), 
            halign='left', 
            valign='middle', 
            size_hint_y=None, 
            height=60,
            font_name=ARABIC_FONT
        )
        msg_label.bind(width=lambda listener, value: msg_label.setter('text_size')(msg_label, (value, None)))
        self.chat_layout.add_widget(msg_label)

    def start_talking_animation(self):
        anim = Animation(opacity=0.4, duration=0.5) + Animation(opacity=1.0, duration=0.5)
        anim.repeat = True
        anim.start(self.title_label)

    def stop_talking_animation(self):
        Animation.cancel_all(self.title_label)
        self.title_label.opacity = 1.0

    def speak(self, text):
        def run():
            self.start_talking_animation()
            try:
                clean_text = re.sub(r'[^\w\s\u0600-\u06FF\u4e00-\u9fff]', '', text).strip()
                if not clean_text: return
                has_non_english = any(ord(char) > 127 for char in clean_text)
                
                if has_non_english:
                    is_arabic = any('\u0600' <= char <= '\u06FF' for char in clean_text)
                    lang_code = 'ar' if is_arabic else 'zh'
                    tts = gTTS(text=clean_text[:200], lang=lang_code)
                    tts.save("nina_response.mp3")
                    os.system("start /min nina_response.mp3")
                else:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 165)
                    engine.say(clean_text[:200])
                    engine.runAndWait()
            except Exception as e: print("TTS Error:", e)
            finally:
                self.stop_talking_animation()

        threading.Thread(target=run, daemon=True).start()

    def on_send_text(self, instance):
        global is_awakened, is_busy_mode
        text = self.entry.text.strip()
        if not text: return
        
        self.add_message_to_chat(f"YOU: {text}")
        self.entry.text = ""
        clean_text = text.lower()

        if any(kw in clean_text for kw in ["مشغولة", "عندي قراية", "عندي شغل", "busy"]):
            is_busy_mode = True
            is_awakened = False
            reply = "ربي يوفقك عبير الغالية! 🥰 سأنتظركِ هنا، ركزي جيداً! 🌸📚"
            self.add_message_to_chat(f"NINA: {reply}")
            self.speak(reply)
            return

        if is_busy_mode and any(kw in clean_text for kw in ["خلصت", "كملت", "رجعت"]):
            is_busy_mode = False
            is_awakened = True
            reply = "يعطيك الصحة عبير البطلة! 🥳 أنا جاهزة لمساعدتكِ الآن في البحوث والرياضيات! ✨"
            self.add_message_to_chat(f"NINA: {reply}")
            self.speak(reply)
            return

        if is_busy_mode:
            reply = "🤫 ركزي في قرايتك يا عبير! سأنتظركِ حتى تخبريني 'كملت'! 🎀"
            self.add_message_to_chat(f"NINA: {reply}")
            self.speak(reply)
            return

        if any(kw in clean_text for kw in ["استيقظي", "استيقضي", "wake up"]):
            is_awakened = True
            reply = "أنا مستيقظة وذكية وجاهزة لمساعدتكِ في الدراسة والبحوث يا عبير! 🌸✨"
            self.add_message_to_chat(f"NINA: {reply}")
            self.speak(reply)
            return

        if not is_awakened:
            reply = "Zzz... قولي 'استيقضي' لنبدأ الدراسة، أو 'أنا مشغولة' للتركيز!"
            self.add_message_to_chat(f"NINA: {reply}")
            self.speak(reply)
            return

        def process():
            history.append({"role": "user", "content": text})
            try:
                # تحديث السيرفر والموديل هنا لتفادي الضغط والحظر تلقائياً
                payload = {
                    "messages": history,
                    "model": "mistral-large", 
                    "jsonMode": False
                }
                res = requests.post("https://text.pollinations.ai/", json=payload, timeout=15)
                if res.status_code == 200:
                    reply_text = res.text
                    history.append({"role": "assistant", "content": reply_text})
                    save_memory(history)
                    self.add_message_to_chat(f"NINA: {reply_text}")
                    self.speak(reply_text)
                else:
                    self.add_message_to_chat("NINA: السيرفر مشغول حالياً يا عبير، عاودي المحاولة بعد ثوانٍ! 🌸")
            except: 
                self.add_message_to_chat("NINA: Internet error, Abir! 🌸")
        threading.Thread(target=process, daemon=True).start()

    def on_voice_click(self, instance):
        def run_listen():
            try:
                self.voice_btn.font_name = ARABIC_FONT
                self.voice_btn.text = "Listening... 🎧"
                fs = 44100
                duration = 4
                recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
                sd.wait()
                
                self.voice_btn.text = "Processing... ⏳"
                wavfile.write("temp_audio.wav", fs, recording)
                
                recognizer = sr.Recognizer()
                with sr.AudioFile("temp_audio.wav") as source:
                    audio = recognizer.record(source)
                    
                user_text = ""
                for lang in ["ar-DZ", "en-US", "zh-CN"]:
                    try:
                        user_text = recognizer.recognize_google(audio, language=lang)
                        if user_text.strip(): break
                    except: continue
                        
                if user_text: 
                    self.entry.text = user_text
                    self.on_send_text(None)
                    
            except Exception as e: print("Voice Input Error:", e)
            finally: 
                self.voice_btn.text = "🎤 VOICE"
        threading.Thread(target=run_listen, daemon=True).start()

if __name__ == '__main__':
    NinaAndroidApp().run()