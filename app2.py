# import library yang dibutuhkan
from asyncio import timeout
from fileinput import filename

import requests
import speech_recognition as sr
import json
from gtts import gTTS
from dotenv import load_dotenv
import os
import pygame
import time

load_dotenv()

API_KEY = os.getenv("TOGETHER_API_KEY")
RESEP_FILE = "resep.json"
BAHASA = 'id'

"""Load resep dari file json"""
def load_resep(nama_file):
    try:
        with open(nama_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        bahan_text = "\n".join(data['bahan'])
        langkah_text = "\n".join(data['langkah-langkah'])
        resep_text = (
            f"Judul: {data['judul']}\n"
            f"Bahan-bahan:\n{bahan_text}\n"
            f"Catatan: {data.get('catatan', '')}\n"
            f"Langkah-langkah: \n{langkah_text}"
        )
        return resep_text
    except Exception as e:
        print(f'Gagal membaca file Json: {e}')
        return None

def get_step_from_llama(chat_history):
    """Kirim percakapan ke Together API untuk mendapatkan respon langkah masak"""
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
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
        print(f"Gagal menggunakan API: {e}")
        return "Maaf, saya tidak bisa mendapatkan informasi"

def speak(text, lang=BAHASA):
    """Membacakan hasil generative"""
    tts = gTTS(text=text, lang=lang)
    filename= "temp_speech.mp3"
    tts.save(filename)

    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

    pygame.mixer.music.unload()
    os.remove(filename)


def main():
    # Kode untuk membaca resep dari file json
    resep_text = load_resep(RESEP_FILE)
    if not resep_text:
        print('resep tidak ditemukan')
        return
    #print(resep_text)

    # inisialisasi chatbot
    chat_history = [
        {
            "role" : "system",
            "content" : (
                "Kamu adalah asisten memasak yang membacakan langkah demi langkah resep masakan.\n"
                "Hanya gunakan Bahasa Indonesia.\n"
                "Berikan hanya 1 langkah memasak setiap kali diminta.\n"
                "Tunggu perintah 'lanjut' untuk memberikan langkah selanjutnya.\n"
                "Perintah 'ulangi' untuk mengulang langkah saat ini.\n"
                "Perintah 'sebelumnya' untuk membacakan langkah sebelumnya.\n"
                "Jangan menulis karakter *"
            )
        },
        {
            "role" : "user",
            "content" : (
                f"Buat langkah memasak dari resep berikut: \n{resep_text}.\n"
                "Bacakan dulu judul resep dan bahan-bahannya."
            )


        },

    ]

    """command_class = [
        "Klasifikasikan teks perintah ini untuk lanjut ke langkah berikutnya, ulangi membaca langkah saat ini, membaca langkah sebelumnya, bertanya tentang sesuatu, meminta pewaktu, atau meminta proses memasak selesai"
        "Ketikkan 1 untuk lanjut ke langkah berikutnya, ketikkan 2 untuk membaca ulang langkah saat ini, ketikkan 3 untuk kembali ke langkah sebelumnya, ketikkan 4 untuk bertanya tentang sesuatu, ketikkan 5 untuk meminta pewaktu, dan ketikkan 6 untuk proses memasak dihentikan"
        "Jangan berikan output apapun kecuali salah satu dari angka tersebut!"
    ]"""


    # langkah-langkah
    # intro pembuka
    step = get_step_from_llama(chat_history)
    print(f"\n {step}")
    speak(step)
    chat_history.append({"role": "assistant", "content": step})

    while True:
        command = input("Masukkan perintah: ")

        if any(word in command for word in['selesai', 'cukup', 'done', "i'm done"]):
            goodbye = "Sesi memasak selesai! Selamat menikmati masakanmu"
            print(f"{goodbye}")
            speak(goodbye)
            break
        elif any(word in command for word in ["lanjut", "next", "terus", "selanjutnya"]):
            chat_history.append({"role": "user", "content": "lanjutkan ke langkah berikutnya."})
            step = get_step_from_llama(chat_history)
            print(f"\n {step}")
            speak(step)
            chat_history.append({"role": "assistant", "content": step})
        else:
            speak("Perintah tidak dikenali. Ucapkan lanjut atau selesai")





if __name__ == "__main__":
    main()