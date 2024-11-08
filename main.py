# PyQt5:
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc
# Ollama
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
# Speech
import pyttsx3
# Speech to text imports
from vosk import Model, KaldiRecognizer
import pyaudio
import threading
import sys
import time

#fill out these variables:
vosk_model_path = r"/Users/andrew/PycharmProjects/llama-bot/vosk-model-small-en-us-0.15"
wake_word = "okay door"
query_end_word = "ghost"

# Text to speech setup
engine = pyttsx3.init()
engine.setProperty('rate', 175)
engine.setProperty('volume', 1.0)

# Speech to text setup - ENTER THE PATH TO YOUR VOSK MODEL HERE
model = Model(vosk_model_path)
recognizer = KaldiRecognizer(model, 16000)
mic = pyaudio.PyAudio()

# Add any knowledge you would like the virtual assistant to know
context = ""
question = ""
template = """
My name is Andrew and your name is Nova.
You are my virtual assistant.
Sometimes I will use a speech-to-text model that is not always accurate so you might have to try and infer what I mean based on the context.
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""
model = OllamaLLM(model="llama3.2")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


class MainWindow(qtw.QWidget):
    update_conversation_signal = qtc.pyqtSignal(str)
    speak_signal = qtc.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Add a title
        self.setWindowTitle("Nova")

        # Set layout
        self.setLayout(qtw.QVBoxLayout())

        # Initialize conversation
        self.conversation = ""

        # Create a label
        self.my_label = qtw.QTextEdit()
        self.my_label.setFont(qtg.QFont('Helvetica', 18))
        self.my_label.setReadOnly(True)  # Make it read-only
        self.my_label.setFixedWidth(1000)  # Set a fixed width
        self.layout().addWidget(self.my_label)

        # Create entry box
        self.my_entry = qtw.QLineEdit()
        self.my_entry.setObjectName("input_field")
        self.layout().addWidget(self.my_entry)

        # Connect the returnPressed signal to the press_it method
        self.my_entry.returnPressed.connect(self.press_it)

        # Create a button
        my_button = qtw.QPushButton("Submit", clicked=self.press_it)
        self.layout().addWidget(my_button)

        # Toggle the speech
        self.speech_checkbox = qtw.QCheckBox("Enable Speech")
        self.speech_checkbox.setChecked(True)  # Default to enabled
        self.layout().addWidget(self.speech_checkbox)

        # Toggle mic with checkbox
        self.mic_checkbox = qtw.QCheckBox("Enable Microphone")
        self.mic_checkbox.setChecked(False)  # Default to disabled
        self.mic_checkbox.stateChanged.connect(self.mic_toggle)  # Connect to function
        self.layout().addWidget(self.mic_checkbox)

        # Show the app
        self.show()

        # Signal to update the conversation in the main thread
        self.update_conversation_signal.connect(self.update_conversation)
        self.speak_signal.connect(self.speak_text)

        self.listening = False  # To track if we are listening to the mic

    def mic_toggle(self, state):
        if state == qtc.Qt.Checked:
            print("Microphone enabled.")
            self.listening = True
            # Start microphone listening in a separate thread
            self.mic_thread = threading.Thread(target=self.listen_to_mic, daemon=True)
            self.mic_thread.start()
        else:
            print("Microphone disabled.")
            self.listening = False
            if hasattr(self, 'mic_thread') and self.mic_thread.is_alive():
                self.mic_thread.join()

    def listen_to_mic(self):
        stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2048)
        stream.start_stream()

        try:
            while self.listening:
                clean_text = ""
                # Listen for the activation phrase
                while wake_word not in clean_text and self.listening:
                    try:
                        data = stream.read(2048, exception_on_overflow=False)  # Lower buffer size and handle overflow
                        if "stop listening" in clean_text or "disable microphone" in clean_text:
                            print("stop listening")
                            self.mic_checkbox.setChecked(False)
                            clean_text = ""
                            break
                        if "disable speech" in clean_text:
                            print("speech disabled")
                            self.speech_checkbox.setChecked(False)
                            clean_text = ""
                        if "enable speech" in clean_text:
                            print("speech enabled")
                            self.speech_checkbox.setChecked(True)
                            clean_text = ""
                        if recognizer.AcceptWaveform(data):
                            text = recognizer.Result()
                            clean_text += f"{text[14:-3]} "
                            print(f"' {text[14:-3]} '")
                        time.sleep(0.05)  # Add slight delay

                    except OSError as e:
                        print("Overflow error: ", e)
                        time.sleep(0.1)  # Slight pause before retrying

                if not self.listening:
                    break

                clean_text = "okay nova "
                while query_end_word not in clean_text and self.listening:
                    try:
                        data = stream.read(2048, exception_on_overflow=False)
                        if recognizer.AcceptWaveform(data):
                            text = recognizer.Result()
                            clean_text += f"{text[14:-3]} "
                            print(f"' {text[14:-3]} '")
                        time.sleep(0.05)

                    except OSError as e:
                        print("Overflow error: ", e)
                        time.sleep(0.1)

                if not self.listening:
                    break

                clean_text = clean_text[:-6]
                result = chain.invoke({"context": self.conversation, "question": clean_text})
                print("clean_text: " + clean_text)
                print("results " + result)

                self.update_conversation_signal.emit(
                    f'\n********************************************************\nYou: {clean_text}\n\n********************************************************\nNova: {result}'
                )

                if self.speech_checkbox.isChecked():
                    self.speak_signal.emit(result)

        finally:
            stream.stop_stream()
            stream.close()

    def speak_text(self, text):
        #run the speech in a separate thread
        #threading.Thread(target=self.speak, args=(text,), daemon=True).start()
        self.speak(text)

    def speak(self, text):
        #disable microphone while speaking
        self.listening = False
        # wait for mic thread to finish if running
        if hasattr(self, 'mic_thread') and self.mic_thread.is_alive():
            self.mic_thread.join()
        #nova speaking
        engine.say(text)
        engine.runAndWait()
        #maybe add engine stop or whatever

        # Enable mic listenitng after speaking
        if self.mic_checkbox.isChecked():
            print(True)
            #self.mic_checkbox.stateChanged.connect(self.mic_toggle)
            self.mic_toggle(qtc.Qt.Checked)
            # self.mic_thread = threading.Thread(target=self.listen_to_mic, daemon=True)
            # self.mic_thread.start()

    def update_conversation(self, text):
        # Update the UI with new conversation data
        self.conversation += text
        self.my_label.setText(self.conversation)
        self.my_label.verticalScrollBar().setValue(self.my_label.verticalScrollBar().maximum())
        self.my_entry.setText("")

    def press_it(self):
        # Update conversation with new input
        result = chain.invoke({"context": self.conversation, "question": self.my_entry.text()})
        print(result)
        self.conversation += f'\n********************************************************\nYou: {self.my_entry.text()}\n\n********************************************************\nNova: {result}'
        # Update label with full conversation
        self.my_label.setText(self.conversation)
        self.my_label.verticalScrollBar().setValue(self.my_label.verticalScrollBar().maximum())

        # Check if speech is toggled:
        if self.speech_checkbox.isChecked():
            engine.say(result)
            engine.runAndWait()
        # Clear entry box
        self.my_entry.setText("")


app = qtw.QApplication([])
mw = MainWindow()

try:
    sys.exit(app.exec_())
except Exception as e:
    print(f"Application exited with an error: {e}")