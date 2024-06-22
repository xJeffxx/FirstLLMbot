import sys
import json
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, \
    QPushButton, QLabel, QComboBox, QCheckBox, QSpinBox, QPlainTextEdit
from PyQt6.QtCore import Qt, QThread, pyqtSignal

VERSION = "2.2"
CONFIG_FILE = "config.json"
OLLAMA_API_URL = "http://localhost:11434/api"


class OllamaThread(QThread):
    response_received = pyqtSignal(str)

    def __init__(self, model, prompt, context, personality):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self.context = context
        self.personality = personality

    def run(self):
        try:
            full_prompt = f"{self.personality}\n{self.context}\nHuman: {self.prompt}\nAI:"
            print(f"Full Prompt: {full_prompt}")  # Debugging output
            response = requests.post(
                f"{OLLAMA_API_URL}/generate",
                json={"model": self.model, "prompt": full_prompt},
                stream=True
            )
            response.raise_for_status()
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        full_response += data['response']
            if not full_response:
                self.response_received.emit("No response received from the model.")
            else:
                self.response_received.emit(full_response)
        except requests.RequestException as e:
            self.response_received.emit(f"Error: {str(e)}")
        except json.JSONDecodeError as e:
            self.response_received.emit(f"Error decoding JSON: {str(e)}")


class ChatbotUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Ollama Chatbot v{VERSION}")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.get_available_models())
        self.model_combo.currentTextChanged.connect(self.update_model_params)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # Personality definition
        layout.addWidget(QLabel("Personality/Context:"))
        self.personality_input = QPlainTextEdit()
        layout.addWidget(self.personality_input)

        # Chat log
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        layout.addWidget(self.chat_log)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)

        # Model parameters
        self.params_label = QLabel("Model Parameters:")
        layout.addWidget(self.params_label)

        # Persistence and history length
        persistence_layout = QHBoxLayout()
        self.persistence_checkbox = QCheckBox("Enable Persistence")
        persistence_layout.addWidget(self.persistence_checkbox)

        persistence_layout.addWidget(QLabel("History Length:"))
        self.history_length_spinbox = QSpinBox()
        self.history_length_spinbox.setRange(1, 100)
        self.history_length_spinbox.setValue(10)
        self.history_length_spinbox.valueChanged.connect(self.update_history_length)
        persistence_layout.addWidget(self.history_length_spinbox)

        layout.addLayout(persistence_layout)

        # Clear history button
        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(self.clear_history)
        layout.addWidget(clear_button)

        self.chat_history = []
        self.max_history_length = 10
        self.load_config()
        self.update_model_params()

    def get_available_models(self):
        try:
            response = requests.get(f"{OLLAMA_API_URL}/tags")
            response.raise_for_status()
            return [model["name"] for model in response.json()["models"]]
        except requests.RequestException:
            return ["Error fetching models"]

    def update_model_params(self):
        model = self.model_combo.currentText()
        try:
            response = requests.post(f"{OLLAMA_API_URL}/show", json={"name": model})
            response.raise_for_status()
            params = response.json()["parameters"]
            if isinstance(params, str):
                params = json.loads(params)
            readable_params = self.make_params_readable(params)
            self.params_label.setText(f"Model Parameters:\n{readable_params}")
        except requests.RequestException:
            self.params_label.setText("Error fetching model parameters")
        except json.JSONDecodeError as e:
            self.params_label.setText(f"Error decoding JSON: {str(e)}")

    def make_params_readable(self, params):
        readable = ""
        for key, value in params.items():
            readable += f"{key.replace('_', ' ').title()}: {value}\n"
        return readable

    def send_message(self):
        user_input = self.input_field.text().strip()
        if not user_input:
            return

        self.chat_log.append(f"<b>You:</b> {user_input}")
        self.input_field.clear()

        context = "\n".join(self.chat_history)
        personality = self.personality_input.toPlainText().strip()
        self.ollama_thread = OllamaThread(self.model_combo.currentText(), user_input, context, personality)
        self.ollama_thread.response_received.connect(self.handle_response)
        self.ollama_thread.start()

    def handle_response(self, response):
        self.chat_log.append(f"\n<b>Bot:</b> {response}")
        self.chat_log.verticalScrollBar().setValue(self.chat_log.verticalScrollBar().maximum())

        # Update chat history
        self.chat_history.append(f"Human: {self.input_field.text()}")
        self.chat_history.append(f"AI: {response}")

        # Limit chat history length
        if len(self.chat_history) > self.max_history_length * 2:  # *2 because each exchange is 2 messages
            self.chat_history = self.chat_history[-(self.max_history_length * 2):]

    def update_history_length(self, value):
        self.max_history_length = value
        # Trim existing history if necessary
        if len(self.chat_history) > self.max_history_length * 2:
            self.chat_history = self.chat_history[-(self.max_history_length * 2):]

    def clear_history(self):
        self.chat_history = []
        self.chat_log.clear()
        self.personality_input.clear()
        self.save_config()

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as file:
                config = json.load(file)
                self.model_combo.setCurrentText(config.get("model", ""))
                self.chat_log.setHtml(config.get("chat_log", ""))
                self.persistence_checkbox.setChecked(config.get("persistence", False))
                self.chat_history = config.get("chat_history", [])
                self.max_history_length = config.get("max_history_length", 10)
                self.history_length_spinbox.setValue(self.max_history_length)
                self.personality_input.setPlainText(config.get("personality", ""))
                # Ensure chat history doesn't exceed the maximum length
                self.chat_history = self.chat_history[-(self.max_history_length * 2):]
        except FileNotFoundError:
            pass
        except json.JSONDecodeError as e:
            print(f"Error loading config: {str(e)}")

    def save_config(self):
        if self.persistence_checkbox.isChecked():
            config = {
                "model": self.model_combo.currentText(),
                "chat_log": self.chat_log.toHtml(),
                "persistence": self.persistence_checkbox.isChecked(),
                "chat_history": self.chat_history,
                "max_history_length": self.max_history_length,
                "personality": self.personality_input.toPlainText().strip()
            }
            with open(CONFIG_FILE, "w") as file:
                json.dump(config, file, indent=4)

    def closeEvent(self, event):
        self.save_config()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatbotUI()
    window.show()
    sys.exit(app.exec())