# PyQt5:
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
#ollama
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
#speec
import pyttsx3
#speech to text imports
from vosk import Model, KaldiRecognizer
import pyaudio

#text to speech stuff
engine = pyttsx3.init()
engine.setProperty('rate', 175)
engine.setProperty('volume', 1.0)



#speech to text stuff - ENTER THE PATH TO YOUR VOSK MODEL HERE
model = Model(r"/Users/andrew/PycharmProjects/llama-bot/vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)
mic = pyaudio.PyAudio()

#Change your name and put any knowledge you would like Nova to know before running the program
template = """
My name is Andrew and your name is Nova.
You are my virtual assistant.
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""
model=OllamaLLM(model="llama3.2")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

class MainWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()
        # Add a title
        self.setWindowTitle("Nova")

        # Set layout V is for vertical box layout (H is for horizontal)
        self.setLayout(qtw.QVBoxLayout())

        # Initialize conversation
        self.conversation = ""

        # Create a label
        self.my_label = qtw.QTextEdit()
        self.my_label.setFont(qtg.QFont('Helvetica', 18))
        self.my_label.setReadOnly(True)  # Make it read-only so it behaves like a label
        self.my_label.setFixedWidth(1000)  # Set a fixed width
        self.layout().addWidget(self.my_label)

        # Create entry box
        self.my_entry = qtw.QLineEdit()
        self.my_entry.setObjectName("input_field")
        self.my_entry.setText("")
        self.layout().addWidget(self.my_entry)

        # Connect the returnPressed signal to the press_it method
        self.my_entry.returnPressed.connect(self.press_it)

        # Create a button
        my_button = qtw.QPushButton("Submit", clicked=self.press_it)
        self.layout().addWidget(my_button)

        #toggle the speech
        self.speech_checkbox = qtw.QCheckBox("Enable Speech")
        self.speech_checkbox.setChecked(True)  # Default to enabled
        self.layout().addWidget(self.speech_checkbox)

        # toggle the mic
        mic_button = qtw.QPushButton("mic", clicked=self.mic_toggle)
        self.layout().addWidget(mic_button)
        # self.mic_checkbox = qtw.QCheckBox("Enable Microphone")
        # self.mic_checkbox.setChecked(False)  # Default to enabled
        # self.layout().addWidget(self.mic_checkbox)

        # Show the app
        self.show()

    def mic_toggle(self):
        clean_text=""
        stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        stream.start_stream()
        while "ghost" not in clean_text:
            data = stream.read(4096)

            if recognizer.AcceptWaveform(data):
                text = recognizer.Result()
                clean_text += f"{text[14:-3]} "
                print(f"' {text[14:-3]} '")
        clean_text = clean_text[:-6]
        result = chain.invoke({"context": self.conversation, "question": clean_text})
        print("clean_text: " + clean_text)
        print("results "+ result)
        self.conversation += f'\n\nYou: {clean_text}\n\nNova: {result}'
        self.my_label.setText(self.conversation)
        if self.speech_checkbox.isChecked():
            engine.say(result)
            engine.runAndWait()
        # Clear entry box
        self.my_entry.setText("")

    def press_it(self):
        # Update conversation with new input
        result = chain.invoke({"context": self.conversation, "question": self.my_entry.text()})
        print(result)
        self.conversation += f'\nYou: {self.my_entry.text()}\nNova: {result}'
        # Update label with full conversation
        self.my_label.setText(self.conversation)

        #check if speech is toggled:
        if self.speech_checkbox.isChecked():
            engine.say(result)
            engine.runAndWait()
        # Clear entry box
        self.my_entry.setText("")

app = qtw.QApplication([])
mw = MainWindow()

# Run the app
app.exec_()
engine.stop()



