import sys
import json
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, \
    QPushButton, QLabel, QComboBox, QCheckBox, QSpinBox, QPlainTextEdit, QGroupBox, QFormLayout, QDoubleSpinBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor

VERSION = "4.2"
CONFIG_FILE = "config.json"
OLLAMA_API_URL = "http://localhost:11434/api"


class OllamaThread(QThread):
    response_received = pyqtSignal(str)
    response_finished = pyqtSignal()

    def __init__(self, model, prompt, context, personality, role, temperature, top_p, top_k, max_tokens):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self.context = context
        self.personality = personality
        self.role = role
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens

    def run(self):
        try:
            system_prompt = {
                "role": "system",
                "content": f"You are a {self.role}. {self.personality} Respond to all messages in character, without breaking the fourth wall or mentioning that you are an AI. Always stay in character."
            }
            messages = [system_prompt]

            # Add context messages
            for message in self.context:
                if message.startswith("Human: "):
                    messages.append({"role": "user", "content": message[7:]})
                elif message.startswith("AI: "):
                    messages.append({"role": "assistant", "content": message[4:]})

            # Add the current user message
            messages.append({"role": "user", "content": self.prompt})

            print(f"Full Messages: {messages}")  # Debugging output

            response = requests.post(
                f"{OLLAMA_API_URL}/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": self.temperature,
                        "top_p": self.top_p,
                        "top_k": self.top_k,
                        "max_tokens": self.max_tokens  # Set max tokens for response length
                    }
                },
                stream=True
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'message' in data and 'content' in data['message']:
                            self.response_received.emit(data['message']['content'])
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON: {line}")
            self.response_finished.emit()
        except requests.RequestException as e:
            self.response_received.emit(f"Error: {str(e)}")
            self.response_finished.emit()


class ChatbotUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Ollama Chatbot v{VERSION}")
        self.setGeometry(100, 100, 1000, 800)

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

        # Prompt parameters
        prompt_params_group = QGroupBox("Prompt Parameters")
        prompt_params_layout = QFormLayout()

        self.role_input = QLineEdit()
        prompt_params_layout.addRow("Role:", self.role_input)

        self.personality_input = QPlainTextEdit()
        prompt_params_layout.addRow("Personality/Context:", self.personality_input)

        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setSingleStep(0.1)
        self.temperature_input.setValue(0.7)
        prompt_params_layout.addRow("Temperature:", self.temperature_input)

        self.top_p_input = QDoubleSpinBox()
        self.top_p_input.setRange(0.0, 1.0)
        self.top_p_input.setSingleStep(0.1)
        self.top_p_input.setValue(0.9)
        prompt_params_layout.addRow("Top P:", self.top_p_input)

        self.top_k_input = QSpinBox()
        self.top_k_input.setRange(0, 100)
        self.top_k_input.setValue(40)
        prompt_params_layout.addRow("Top K:", self.top_k_input)

        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(50, 2000)
        self.max_tokens_input.setValue(500)
        prompt_params_layout.addRow("Max Tokens:", self.max_tokens_input)

        prompt_params_group.setLayout(prompt_params_layout)
        layout.addWidget(prompt_params_group)

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
        self.current_response = ""
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
        except json.JSONDecodeError:
            self.params_label.setText("Error decoding JSON")

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

        personality = self.personality_input.toPlainText().strip()
        role = self.role_input.text().strip()
        temperature = self.temperature_input.value()
        top_p = self.top_p_input.value()
        top_k = self.top_k_input.value()
        max_tokens = self.max_tokens_input.value()

        self.ollama_thread = OllamaThread(
            self.model_combo.currentText(),
            user_input,
            self.chat_history,
            personality,
            role,
            temperature,
            top_p,
            top_k,
            max_tokens
        )
        self.ollama_thread.response_received.connect(self.handle_response_chunk)
        self.ollama_thread.response_finished.connect(self.handle_response_finished)
        self.current_response = ""
        self.chat_log.append("<b>Bot:</b> ")
        self.ollama_thread.start()

    def handle_response_chunk(self, chunk):
        self.current_response += chunk
        cursor = self.chat_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.chat_log.setTextCursor(cursor)
        self.chat_log.ensureCursorVisible()

    def handle_response_finished(self):
        self.chat_log.append("")  # Add a newline after the complete response

        # Update chat history
        self.chat_history.append(f"Human: {self.input_field.text()}")
        self.chat_history.append(f"AI: {self.current_response}")

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
                self.role_input.setText(config.get("role", ""))
                self.personality_input.setPlainText(config.get("personality", ""))
                self.temperature_input.setValue(config.get("temperature", 0.7))
                self.top_p_input.setValue(config.get("top_p", 0.9))
                self.top_k_input.setValue(config.get("top_k", 40))
                self.max_tokens_input.setValue(config.get("max_tokens", 500))
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
                "role": self.role_input.text(),
                "personality": self.personality_input.toPlainText(),
                "temperature": self.temperature_input.value(),
                "top_p": self.top_p_input.value(),
                "top_k": self.top_k_input.value(),
                "max_tokens": self.max_tokens_input.value()
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
