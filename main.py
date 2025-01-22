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
from datetime import datetime

# For printing each letter
from PyQt5.QtCore import QTimer

#fill out these variables:
# vosk_model_path = r"C:/Users/I570399/PycharmProjects/virtual_assist/vosk-model-small-en-us-0.15/vosk-model-small-en-us-0.15"
vosk_model_path = (r"/Users/andrew/PycharmProjects/llama-bot/vosk-model-small-en-us-0.15")
wake_word = "okay door"
query_end_word = "ghost"
#read_files_path = "C:/Users/I570399/PycharmProjects/virtual_assist/read_files/file.txt"
read_files_path = "/Users/andrew/PycharmProjects/llama-bot/read_files/file.txt"

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
Try to answer all questions directly in no more than 3-4 sentences.
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""
model_title = "llama3.2"
llm_model = OllamaLLM(model=model_title)
#llm_model = OllamaLLM(model="deepseek-r1")
print("*************INITIALIZING CURRENT MODEL*************")
print("CURRENT_MODEL = " + str(llm_model))
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | llm_model
change_model_flag = False
# Active typing flag change to False if you don't want it to type out it's responses
active_typing = False

class MainWindow(qtw.QWidget):
    update_conversation_signal = qtc.pyqtSignal(str, str)
    speak_signal = qtc.pyqtSignal(str)
    clear_chat_signal = qtc.pyqtSignal()
    update_title_signal = qtc.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Add a title
        self.setWindowTitle(str(model_title))

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
        self.speak_signal.connect(self.speak)

        #track if we are listening to mic.
        #need to change this to false when mic is off by default
        self.listening = False
        #comment below out if starting with mic off by default
        # self.mic_thread = threading.Thread(target=self.listen_to_mic, daemon=True)
        # self.mic_thread.start()
        # To track if we are listening to the mic

        # Clear chat
        self.clear_chat_signal.connect(self.clear_chat_gui)

        # Update title
        self.update_title_signal.connect(self.update_window_title)  # Connect the signal to the method

    def update_window_title(self, title):
        self.setWindowTitle(title)  # Method to safely update the window title

    def list_model(self, text):
        global model_title
        text = "list models"
        result = "Here are a list of the models available:\nllama3.2\ndeepseek-r1:7b\nCurrently, "+ model_title +" is selected."
        self.update_conversation_signal.emit(
            f'\n********************************************************\nYou: {text}\n\n********************************************************\nNova: ', result
        )
        if self.speech_checkbox.isChecked():
            self.speak_signal.emit(result)

    def clear_chat(self):
        print("**CLEARING CHAT**")
        self.conversation = ""
        print("self conversation")
        self.clear_chat_signal.emit()
        print("label")
        #self.my_label.verticalScrollBar().setValue(self.my_label.verticalScrollBar().maximum())
        self.my_entry.setText("")
        print("**CHAT CLEARED**")

    def clear_chat_gui(self):
        self.my_label.setText(self.conversation)
        self.my_entry.setText("")

    def ask_change_model(self):
        global model_title  # Declare global variables to modify them.
        text = "Change model"
        result = "Here are a list of the models available:\nllama3.2\ndeepseek-r1:7b\nCurrently, " + model_title + " is selected.\nWhat model would you like to choose?"
        self.update_conversation_signal.emit(
            f'\n********************************************************\nYou: {text}\n\n********************************************************\nNova: ', result
        )


    def change_model(self, model_name):
        mic = False
        if self.mic_checkbox.isChecked():
            mic = True
            self.mic_checkbox.setChecked(False)

        self.clear_chat() # Clear the chat before switching models
        global llm_model, prompt, chain, model_title  # Declare global variables to modify them.
        model_title = model_name
        print("model title " + model_title)
        llm_model = OllamaLLM(model=model_title)  # Updating the model
        prompt = ChatPromptTemplate.from_template(template)  # Reinitialize the prompt
        chain = prompt | llm_model  # Reinitalize the chain
        self.update_title_signal.emit(model_title)  # Emit the signal to update the title
        print("**MODEL CHANGED**")
        text = model_title
        result = "Model has been changed to: " + model_title
        self.update_conversation_signal.emit(
            f'\n********************************************************\nYou: {text}\n\n********************************************************\nNova: ', result
        )
        if mic:
            self.mic_checkbox.setChecked(True)

    def active_typing_toggle(self, command):
        global active_typing
        if "stop" in command or "off" in command:
            active_typing = False
            text = "Turn off active typing."
            result = "Active typing has been turned off."
        else:
            active_typing = True
            text = "Turn on active typing."
            result = "Active typing has been turned on."
        self.update_conversation_signal.emit(
            f'\n********************************************************\nYou: {text}\n\n********************************************************\nNova: ', result
        )
        if self.speech_checkbox.isChecked():
            self.speak_signal.emit(result)


    def get_time(self):
        current_time = datetime.now().strftime("%I:%M %p")
        message = self.my_entry.text() + " Here is the current time to answer the question: " + current_time
        return message

    #command to read files
    def read_files(self):
        with open(read_files_path, "r") as file:
            content = file.read()
        message = self.my_entry.text() + " The content of the file is within these brackets {}: {" + content + "}"
        print("**file reading** " + message)
        return message


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
        global change_model_flag

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
                            self.speak_signal.emit("microphone off")
                            break
                        if "disable speech" in clean_text:
                            print("speech disabled")
                            self.speech_checkbox.setChecked(False)
                            #self.speak_signal.emit("Speech disabled")
                            clean_text = ""
                        if "enable speech" in clean_text:
                            print("speech enabled")
                            self.speech_checkbox.setChecked(True)
                            self.speak_signal.emit("Speech enabled")
                            clean_text = ""
                        if "list models" in clean_text:
                            print("**LISTING MODELS**")
                            self.list_model(clean_text)
                            clean_text=""
                        if "clear chat" in clean_text or "clean chat" in clean_text:
                            print("**PREPARING TO CLEAR CHAT**")
                            self.clear_chat()
                            clean_text = ""
                            print("what about here?")
                        if "change model" in clean_text:
                            print("**ASK CHANGE MODEL**")
                            self.ask_change_model()
                            change_model_flag = True
                            clean_text = ""
                        if "lama" in clean_text and change_model_flag:
                            print("**CHANGING LLAMA**")
                            self.change_model("llama3.2")
                            change_model_flag = False
                            clean_text = ""
                        if "deep" in clean_text and change_model_flag:
                            print("**CHANGING deepseek**")
                            self.change_model("deepseek-r1:7b")
                            change_model_flag = False
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
                message = clean_text.lower()
                if "what time is it" in clean_text:
                    message += self.get_time()

                if "read this file" in message:
                    message += self.read_files()


                print("TEST " + message)
                # if reading_work:
                #     clean_text += "Here is the content of the text file:\n " + content
                result = chain.invoke({"context": self.conversation, "question": message})
                print("clean_text: " + clean_text)
                print("results " + result)

                self.update_conversation_signal.emit(
                    f'\n********************************************************\nYou: {clean_text}\n\n********************************************************\nNova: ', result
                )

                if self.speech_checkbox.isChecked():
                    self.speak_signal.emit(result)

        finally:
            stream.stop_stream()
            stream.close()

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
            print("mic checked")
            print(True)
            #self.mic_checkbox.stateChanged.connect(self.mic_toggle)
            self.mic_toggle(qtc.Qt.Checked)
            # self.mic_thread = threading.Thread(target=self.listen_to_mic, daemon=True)
            # self.mic_thread.start()

    def update_conversation(self, text, response):
        global active_typing # this will disable/enable active typing
        # Update the UI with new conversation data
        self.conversation += text
        self.my_label.setText(self.conversation)

        # This is for typing out the answer
        if active_typing:
            self.conversation += response
            self.text_phrase = list(response)  # Convert text to a list of characters
            # self.my_label.clear()  # Prepare for the typing effect ???????
            self.insert_phrase_char()  # Start typing out each character
        else:
            self.conversation += response
            self.my_label.setText(self.conversation)

        self.my_label.verticalScrollBar().setValue(self.my_label.verticalScrollBar().maximum())
        self.my_entry.setText("")

    def press_it(self):
        #Update conversation with new input
        original = self.my_entry.text()
        message = original.lower()
        global change_model_flag
        if "read this file" in message:
            message = self.read_files()


        if "what time is it" in message:
            message = self.get_time()



        if "list models" in message:
            print("**LISTING MODELS**")
            self.list_model(message)
        elif "clear chat" in message or "clean chat" in message:
            print("**PREPARING TO CLEAR CHAT**")
            self.clear_chat()
        elif "change model" in message:
            print("**ASK CHANGE MODEL**")
            self.ask_change_model()
            change_model_flag = True
        elif "llama3" in message and change_model_flag:
            print("**CHANGING LLAMA**")
            self.change_model("llama3.2")
            change_model_flag = False
        elif "deepseek-r1:7b" in message and change_model_flag:
            print("**CHANGING deepseek**")
            self.change_model("deepseek-r1:7b")
            change_model_flag = False
        elif "active typing" in message:
            self.active_typing_toggle(message)
        else:
            result = chain.invoke({"context": self.conversation, "question": message})
            print(result)
            self.my_entry.setText(original)
            self.update_conversation_signal.emit(
                f'\n********************************************************\nYou: {self.my_entry.text()}\n\n********************************************************\nNova: ', result
            )
            # Check if speech is toggled:
            if self.speech_checkbox.isChecked():
                self.speak_signal.emit(result)
            # Clear entry box
            self.my_entry.setText("")

    def insert_phrase_char(self):
        """Inserts each character one by one with a delay."""
        if self.text_phrase:
            cursor = self.my_label.textCursor()
            cursor.movePosition(qtg.QTextCursor.End)
            self.my_label.setTextCursor(cursor)
            next_char = self.text_phrase.pop(0)
            cursor.insertText(next_char)
            QTimer.singleShot(35, self.insert_phrase_char)  # Delay between characters
        else:
            # Auto-scroll to the bottom once typing is complete
            self.my_label.verticalScrollBar().setValue(self.my_label.verticalScrollBar().maximum())

app = qtw.QApplication([])
mw = MainWindow()

try:
    sys.exit(app.exec_())
except Exception as e:
    print(f"Application exited with an error: {e}")