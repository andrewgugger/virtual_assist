# Virtual Assist
Virtual assistant using local LLM's with a GUI

### Requirements:
Please download the [Vosk speech recognition model](https://alphacephei.com/vosk/models) and check out their [GitHub](https://github.com/alphacep/vosk-api). We used the vosk-model-small-en-us-0.15 model. </br>
We used [Ollama3.2](https://ollama.com/) </br>
pip install pyqt5 langchain langchain_ollama vosk kaldilab pyttsx3 pyaudio


### How to use:
To message Nova, type in the chat box and click the Submit button or hit the enter key. </br>
You can toggle the speech so Nova's reponses will either be read out or not. </br>
By clicking on the mic toggle you can enable the microphone and begin speaking. The wake word is 'okay nova' you can then speak your query. To end your query, say the word 'ghost' and the Nova will respond to your query.
