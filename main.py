# =========================================================
# NINA AI — FINAL STABLE VERSION
# Cute Assistant + Smart Memory + Voice + Notifications
# Arabic / English / Chinese / Korean Support
# FINAL CLEAN VERSION
# =========================================================

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

import requests
import threading
import speech_recognition as sr
import json
import re
import os

# =========================================================
# FONT
# =========================================================

LabelBase.register(
    name="Noto",
    fn_regular="NotoSansCJK-Regular.ttc"
)

# =========================================================
# WINDOW
# =========================================================

Window.clearcolor = (1, 0.93, 0.97, 1)
Window.softinput_mode = "below_target"

# =========================================================
# MEMORY
# =========================================================

MEMORY_FILE = "memory.json"

default_memory = {
    "name": "",
    "likes": [],
    "notes": [],
    "history": []
}

if os.path.exists(MEMORY_FILE):

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            memory = json.load(f)

    except:

        memory = default_memory

else:

    memory = default_memory

# =========================================================
# VOICE
# =========================================================

VOICE = False

try:

    from jnius import autoclass
    from time import sleep

    PythonActivity = autoclass(
        'org.kivy.android.PythonActivity'
    )

    Locale = autoclass(
        'java.util.Locale'
    )

    TextToSpeech = autoclass(
        'android.speech.tts.TextToSpeech'
    )

    activity = PythonActivity.mActivity

    tts = TextToSpeech(activity, None)

    sleep(1)

    tts.setPitch(1.0)
    tts.setSpeechRate(0.92)

    VOICE = True

except Exception as e:

    print(e)

# =========================================================
# NOTIFICATIONS
# =========================================================

try:

    from plyer import notification

    def send_notification(title, message):

        notification.notify(
            title=title,
            message=message,
            timeout=5
        )

except:

    def send_notification(title, message):
        pass

# =========================================================
# CHAT BUBBLE
# =========================================================

class Bubble(Label):

    def __init__(self, text, me=False, **kwargs):

        super().__init__(**kwargs)

        self.text = text

        self.font_name = "Noto"

        self.font_size = "18sp"

        self.markup = True

        self.size_hint_y = None

        self.padding = (25, 20)

        self.text_size = (Window.width * 0.65, None)

        self.halign = "left"

        self.valign = "middle"

        self.color = (0.15, 0.1, 0.15, 1)

        self.bind(
            texture_size=self.update_size
        )

        with self.canvas.before:

            if me:

                Color(1, 0.72, 0.86, 1)

            else:

                Color(1, 1, 1, 1)

            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[25]
            )

        self.bind(pos=self.update_rect)
        self.bind(size=self.update_rect)

    def update_size(self, *args):

        self.height = self.texture_size[1] + 40

    def update_rect(self, *args):

        self.rect.pos = self.pos
        self.rect.size = self.size

# =========================================================
# MAIN UI
# =========================================================

class ChatUI(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            spacing=10,
            padding=10,
            **kwargs
        )

        # =====================================================
        # BACKGROUND
        # =====================================================

        with self.canvas.before:

            Color(1, 0.93, 0.97, 1)

            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(pos=self.update_bg)
        self.bind(size=self.update_bg)

        # =====================================================
        # TOP BAR
        # =====================================================

        top = BoxLayout(
            size_hint=(1, 0.09)
        )

        self.title = Label(

            text="♡ NINA AI ♡",

            font_name="Noto",

            font_size="28sp",

            color=(0.92, 0.28, 0.65, 1)
        )

        top.add_widget(self.title)

        self.add_widget(top)

        # =====================================================
        # AVATAR
        # =====================================================

        self.avatar_box = AnchorLayout(
            size_hint=(1, 0.27)
        )

        self.avatar = Image(
            source="icon.png",
            size_hint=(None, None),
            size=(220, 220)
        )

        self.avatar_box.add_widget(self.avatar)

        self.add_widget(self.avatar_box)

        # =====================================================
        # CHAT AREA
        # =====================================================

        self.scroll = ScrollView(
            size_hint=(1, 0.50)
        )

        self.chat_layout = BoxLayout(
            orientation="vertical",
            spacing=12,
            padding=10,
            size_hint_y=None
        )

        self.chat_layout.bind(
            minimum_height=self.chat_layout.setter(
                'height'
            )
        )

        self.scroll.add_widget(
            self.chat_layout
        )

        self.add_widget(
            self.scroll
        )

        # =====================================================
        # INPUT AREA
        # =====================================================

        bottom = BoxLayout(
            size_hint=(1, None),
            height=dp(65),
            spacing=8
        )

        self.input = TextInput(

            hint_text="Talk to Nina...",

            multiline=False,

            font_name="Noto",

            font_size="18sp",

            size_hint=(0.65, 1),

            background_normal='',

            background_active='',

            background_color=(1, 1, 1, 1),

            foreground_color=(0.2, 0.1, 0.2, 1),

            cursor_color=(1, 0.4, 0.8, 1),

            padding=(20, 20)
        )

        # =====================================================
        # VOICE BUTTON
        # =====================================================

        self.voice_btn = Button(

            text="Voice",

            font_name="Noto",

            font_size="18sp",

            size_hint=(0.17, 1),

            background_normal='',

            background_color=(1, 0.75, 0.88, 1),

            color=(1, 1, 1, 1)
        )

        self.voice_btn.bind(
            on_press=self.listen_voice
        )

        # =====================================================
        # SEND BUTTON
        # =====================================================

        self.send_btn = Button(

            text="Send",

            font_name="Noto",

            font_size="18sp",

            size_hint=(0.18, 1),

            background_normal='',

            background_color=(1, 0.45, 0.75, 1),

            color=(1, 1, 1, 1)
        )

        self.send_btn.bind(
            on_press=self.send_message
        )

        bottom.add_widget(self.input)
        bottom.add_widget(self.voice_btn)
        bottom.add_widget(self.send_btn)

        self.add_widget(bottom)

        # =====================================================
        # WELCOME
        # =====================================================

        self.add_bot_message(
            "Nina Ready To Talk ✨"
        )

    # =====================================================
    # UPDATE BG
    # =====================================================

    def update_bg(self, *args):

        self.bg.pos = self.pos
        self.bg.size = self.size

    # =====================================================
    # USER MESSAGE
    # =====================================================

    def add_user_message(self, text):

        bubble = Bubble(
            text,
            me=True
        )

        wrapper = AnchorLayout(
            anchor_x='right',
            size_hint_y=None,
            height=bubble.height + 20
        )

        wrapper.add_widget(bubble)

        self.chat_layout.add_widget(wrapper)

        Clock.schedule_once(
            lambda dt:
            setattr(self.scroll, 'scroll_y', 0)
        )

    # =====================================================
    # BOT MESSAGE
    # =====================================================

    def add_bot_message(self, text):

        bubble = Bubble(
            text,
            me=False
        )

        wrapper = AnchorLayout(
            anchor_x='left',
            size_hint_y=None,
            height=bubble.height + 20
        )

        wrapper.add_widget(bubble)

        self.chat_layout.add_widget(wrapper)

        Clock.schedule_once(
            lambda dt:
            setattr(self.scroll, 'scroll_y', 0)
        )

    # =====================================================
    # AVATAR ANIMATION
    # =====================================================

    def start_animation(self):

        Animation.stop_all(self.avatar)

        anim = (

            Animation(
                size=(245, 245),
                duration=0.35
            )

            +

            Animation(
                size=(220, 220),
                duration=0.35
            )

        )

        anim.repeat = True

        anim.start(self.avatar)

    def stop_animation(self):

        Animation.stop_all(self.avatar)

        self.avatar.size = (220, 220)

    # =====================================================
    # SEND MESSAGE
    # =====================================================

    def send_message(self, instance):

        text = self.input.text.strip()

        if not text:
            return

        self.input.text = ""

        self.add_user_message(text)

        self.start_animation()

        threading.Thread(
            target=self.ask_nina,
            args=(text,),
            daemon=True
        ).start()

    # =====================================================
    # ASK NINA
    # =====================================================

    def ask_nina(self, text):

        global memory

        try:

            if "اسمي" in text:

                memory["name"] = text.replace(
                    "اسمي",
                    ""
                ).strip()

            if "my name is" in text.lower():

                memory["name"] = text.lower().replace(
                    "my name is",
                    ""
                ).strip()

            if "نحب" in text.lower() or "i love" in text.lower():

                memory["likes"].append(text)

            if "تذكري" in text.lower() or "remember" in text.lower():

                memory["notes"].append(text)

            memory["history"].append(
                f"User: {text}"
            )

            memory["history"] = memory["history"][-20:]

            with open(
                MEMORY_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    memory,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

        except:
            pass

        # =================================================
        # LANGUAGE
        # =================================================

        arabic = re.search(r'[\u0600-\u06FF]', text)
        chinese = re.search(r'[\u4e00-\u9fff]', text)
        korean = re.search(r'[\uac00-\ud7af]', text)

        if arabic:

            prompt = f"""
ردي بدارجة جزائرية لطيفة.

اسم المستخدم:
{memory['name']}

الاهتمامات:
{memory['likes']}

المحادثات:
{memory['history']}

رسالة المستخدم:
{text}
"""

            try:
                tts.setLanguage(Locale("ar"))
            except:
                pass

        elif chinese:

            prompt = f"""
请自然回复。

用户:
{memory['name']}

消息:
{text}
"""

            try:
                tts.setLanguage(Locale("zh"))
            except:
                pass

        elif korean:

            prompt = f"""
한국어로 자연스럽게 답해줘.

사용자:
{memory['name']}

메시지:
{text}
"""

            try:
                tts.setLanguage(Locale("ko"))
            except:
                pass

        else:

            prompt = f"""
Reply naturally in English.

User:
{memory['name']}

Message:
{text}
"""

            try:
                tts.setLanguage(Locale("en"))
            except:
                pass

        # =================================================
        # API
        # =================================================

        url = "https://text.pollinations.ai/openai"

        reply = ""

        try:

            response = requests.post(

                url,

                json={
                    "model": "openai",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },

                timeout=40
            )

            if response.status_code == 200:

                try:

                    data = response.json()

                    reply = data["choices"][0]["message"]["content"]

                except:

                    reply = response.text

            else:

                reply = "Connection Error"

        except Exception as error:

            reply = str(error)

        # =================================================
        # CLEAN
        # =================================================

        reply = str(reply)

        reply = reply.replace("*", "")
        reply = reply.replace("#", "")
        reply = reply.replace("�", "")

        reply = reply.strip()

        if reply == "":
            reply = "I couldn't reply."

        Clock.schedule_once(
            lambda dt:
            self.finish_reply(reply)
        )

    # =====================================================
    # FINISH REPLY
    # =====================================================

    def finish_reply(self, reply):

        self.stop_animation()

        self.add_bot_message(reply)

        send_notification(
            "Nina AI",
            reply[:80]
        )

        if VOICE:

            try:

                clean_voice = re.sub(
                    r'[^ء-يa-zA-Z0-9\u4e00-\u9fff\uac00-\ud7af\s]',
                    '',
                    reply
                )

                tts.speak(
                    clean_voice,
                    0,
                    None
                )

            except:
                pass

    # =====================================================
    # VOICE INPUT
    # =====================================================

    def listen_voice(self, instance):

        self.add_bot_message(
            "Listening..."
        )

        threading.Thread(
            target=self.record_voice,
            daemon=True
        ).start()

    def record_voice(self):

        recognizer = sr.Recognizer()

        try:

            with sr.Microphone() as source:

                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=1
                )

                audio = recognizer.listen(
                    source,
                    timeout=8,
                    phrase_time_limit=8
                )

            text = recognizer.recognize_google(
                audio,
                language="ar-DZ"
            )

            Clock.schedule_once(
                lambda dt:
                self.voice_result(text)
            )

        except Exception as error:

            err = str(error)

            Clock.schedule_once(
                lambda dt:
                self.add_bot_message(
                    f"Error: {err}"
                )
            )

    def voice_result(self, text):

        self.input.text = text

        self.send_message(None)

# =========================================================
# APP
# =========================================================

class NinaApp(App):

    icon = "icon.png"

    def build(self):

        return ChatUI()

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    NinaApp().run()