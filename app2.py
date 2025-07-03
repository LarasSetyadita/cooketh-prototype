import requests
import speech_recognition as sr
import json
from gtts import gTTS
import os
#from playsound import playsound

# ========== Konfigurasi ==========
TOGETHER_API_KEY = ""  #
RESEP_FILE = "resep.json"
BAHASA = 'id'  # Bahasa Indonesia untuk TTS

import pygame
import time

# ======== Text-to-Speech ========
def speak(text, lang=BAHASA):
    """Bacakan teks dengan Google TTS dan pygame"""
    tts = gTTS(text=text, lang=lang)
    filename = "temp_speech.mp3"
    tts.save(filename)

    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

    pygame.mixer.music.unload()
    os.remove(filename)

# ======== Load Resep dari JSON ========
def load_resep_dari_json(nama_file):
    """Membaca data resep dari file JSON"""
    try:
        with open(nama_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        bahan_text = "\n".join(data['bahan'])
        resep_text = (
            f"Judul: {data['judul']}\n"
            f"Bahan-bahan:\n{bahan_text}\n"
            f"Catatan: {data.get('catatan', '')}"
        )
        return resep_text
    except Exception as e:
        print(f"❌ Gagal membaca file JSON: {e}")
        return None

# ======== Kirim ke Together API ========
def get_step_from_llama(chat_history):
    """Kirim percakapan ke Together API"""
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": chat_history,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ Gagal menghubungi Together API: {e}")
        return "Maaf, saya tidak bisa mendapatkan langkah selanjutnya."

# ======== Dengarkan Perintah ========
def listen_command():
    """Mendengarkan suara dan mengubah jadi teks"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Dengarkan perintah...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio, language='id-ID').lower()
            print(f"👤 Kamu bilang: {command}")
            return command
        except sr.WaitTimeoutError:
            print("⌛ Tidak ada suara.")
            return ""
        except sr.UnknownValueError:
            print("😕 Tidak mengenali suara.")
            return ""
        except sr.RequestError as e:
            print(f"❌ Error: {e}")
            return ""

# ======== Program Utama ========
def main():
    resep_text = load_resep_dari_json(RESEP_FILE)
    if not resep_text:
        print("🚫 Resep tidak ditemukan.")
        return

    # Inisialisasi riwayat percakapan
    chat_history = [
        {
            "role": "system",
            "content": (
                "Kamu adalah asisten memasak yang membacakan langkah demi langkah resep masakan.\n"
                "Gunakan hanya Bahasa Indonesia.\n"
                "Berikan hanya satu langkah memasak setiap kali diminta.\n"
                "Tunggu perintah 'lanjut' untuk memberikan langkah selanjutnya.\n"
                "Jangan mengulang langkah sebelumnya atau bahan-bahan.\n"
                "Jangan menyebut 'Langkah 1' berulang kali."
                "Jangan pernah menulis karakter *"
            )
        },
        {
            "role": "user",
            "content": f"Buat langkah memasak dari resep berikut:\n{resep_text}\nBacakan dulu judul resepnya dan bahan-bahannya."
        }
    ]

    # Ambil langkah pertama saja dulu
    step = get_step_from_llama(chat_history)
    print(f"\n🧠 {step}\n")
    speak(step)
    chat_history.append({"role": "assistant", "content": step})

    # Mulai mendengarkan perintah user
    while True:
        command = listen_command()

        if any(word in command for word in ["selesai", "cukup", "done", "i'm done"]):
            goodbye = "Sesi memasak selesai! Selamat menikmati masakanmu 🍽️"
            print(f"✅ {goodbye}")
            speak(goodbye)
            break

        elif any(word in command for word in ["lanjut", "next", "terus", "selanjutnya"]):
            chat_history.append({"role": "user", "content": "Lanjutkan ke langkah berikutnya."})
            step = get_step_from_llama(chat_history)
            print(f"\n🧠 {step}\n")
            speak(step)
            chat_history.append({"role": "assistant", "content": step})

        else:
            speak("Perintah tidak dikenali. Tolong ucapkan 'lanjut' atau 'selesai'.")

# ======== Jalankan ========
if __name__ == "__main__":
    main()