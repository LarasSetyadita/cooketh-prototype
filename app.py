import speech_recognition as sr
import pyttsx3

# Inisialisasi TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # kecepatan bicara

# Fungsi untuk bicara
def speak(text):
    print("Asisten:", text)
    engine.say(text)
    engine.runAndWait()

# Intent sederhana (rule-based)
def detect_intent(command):
    command = command.lower()
    if "next" in command:
        return "NEXT"
    elif "repeat" in command or "again" in command:
        return "REPEAT"
    elif "ingredient" in command:
        return "INGREDIENTS"
    elif "minute" in command or "how long" in command:
        return "DURATION"
    else:
        return "UNKNOWN"

# Fungsi untuk respon sesuai intent
def respond_to_intent(intent):
    if intent == "NEXT":
        speak("Okay. Moving to the next step.")
    elif intent == "REPEAT":
        speak("Sure. Here is the step again.")
    elif intent == "INGREDIENTS":
        speak("The ingredients are two eggs, one cup of milk, and flour.")
    elif intent == "DURATION":
        speak("It takes about 20 minutes to cook.")
    else:
        speak("Sorry, I didn't understand that.")

# Proses utama
def main():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        speak("Hi, I'm your cooking assistant. Say something!")
        while True:
            try:
                print("🎤 Listening...")
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio)
                print("You said:", command)

                intent = detect_intent(command)
                respond_to_intent(intent)

            except sr.WaitTimeoutError:
                print("⚠️ Timeout, no speech detected.")
                continue
            except sr.UnknownValueError:
                speak("Sorry, I couldn't understand.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                break

if __name__ == "__main__":
    main()
