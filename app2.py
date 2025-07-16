"""
Asisten Memasak Hands Free
"""

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

def command_classification(command):
    url = "https://api.together.xyz/v1/chat/completions"
    command_class = (
        "Klasifikasikan teks perintah ini untuk lanjut ke langkah berikutnya, ulangi membaca langkah saat ini, membaca langkah sebelumnya, bertanya tentang sesuatu, meminta pewaktu, meminta proses memasak selesai, atau perintah tidak dikenali. "
        "Ketikkan 1 untuk lanjut ke langkah berikutnya, ketikkan 2 untuk membaca ulang langkah saat ini, ketikkan 3 untuk kembali ke langkah sebelumnya, ketikkan 4 untuk bertanya tentang sesuatu, ketikkan 5 untuk meminta pewaktu, ketikkan 6 untuk proses memasak dihentikan, dan ketikkan 7 apabila perintah tidak dikenali. "
        "Jangan berikan output apapun kecuali salah satu dari angka tersebut!"
    )

    headers = {
        "Authorization" : f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "system", "content": command_class},
            {"role": "user", "content": command}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Gagal menggunakan API: {e}")
        return "Maaf, saya tidak bisa mendapatkan informasi"


def question(resep_text, quest):
    url = "https://api.together.xyz/v1/chat/completions"

    # Prompt sistem
    system_prompt = (
        "Kamu adalah asisten memasak yang membantu menjawab pertanyaan seputar bahan dan langkah memasak dari resep berikut.\n"
        f"{resep_text}\n"
        "Berikan jalan keluar atas permasalahannya."
        "Katakan tidak bisa, atau akan sangat mengubah rasa jika permasalahan yang ditanyakan adalah hal fatal."
        "Jawabanmu harus relevan, ringkas, dan tidak keluar dari konteks resep tersebut.\n"
        "Sesuaikan jawaban agar rasa masakan tidak menjadi aneh."
        "Gunakan kata ganti orang kedua tunggal."
        "output 1-3 kalimat saja, dilarang lebih dari itu"
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": quest}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Gagal menggunakan API: {e}")
        return "Maaf, saya tidak bisa mendapatkan informasi"


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
                "Dilarang menulis karakter '*'"
                "Jangan menawarkan langkah-langkah"
            )
        },
        {
            "role" : "user",
            "content" : (
                f"Buat langkah memasak dari resep berikut: \n{resep_text}.\n"
                "Bacakan dulu hanya judul resep apa yang akan dimasak dan bahan-bahannya.\n"
                "Dilarang menulis karakter'*'"
                "gunakan kata ganti orang kedua tunggal"
            )


        },

    ]

    # langkah-langkah
    # intro pembuka
    step = get_step_from_llama(chat_history)
    print(f"\n {step}")
    speak(step)
    chat_history.append({"role": "assistant", "content": step})

    while True:
        command = input("Masukkan perintah: ")
        command_class = command_classification(command)

        if command_class == "6":
            goodbye = "Sesi memasak selesai! Selamat menikmati masakanmu"
            print(f"{goodbye}")
            speak(goodbye)
            break
        elif command_class == "1":
            chat_history.append({"role": "user", "content": "lanjutkan ke langkah berikutnya."})
            step = get_step_from_llama(chat_history)
            print(f"\n {step}")
            speak(step)
            chat_history.append({"role": "assistant", "content": step})
        elif command_class == "2":
            chat_history.append({"role": "user", "content": "ulangi langkah ini."})
            step = get_step_from_llama(chat_history)
            print(f"\n {step}")
            speak(step)
            chat_history.append({"role": "assistant", "content": step})
        elif command_class == "3":
            chat_history.append({"role": "user", "content": "bacakan langkah sebelumnya."})
            step = get_step_from_llama(chat_history)
            print(f"\n {step}")
            speak(step)
            chat_history.append({"role": "assistant", "content": step})
        elif command_class == "5":
            print("Memulai waktu")
        else:
            answer = question(resep_text, command)
            print(answer)
            speak(answer)
            chat_history.append(({"role": "assistant", "content": answer}))

if __name__ == "__main__":
    main()