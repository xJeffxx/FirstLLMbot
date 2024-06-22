Ollama Chatbot
Overview
Ollama Chatbot is a simple yet powerful chatbot application built using Python, PyQt6, and requests. The chatbot interacts with a local Ollama server to generate responses based on user input. The application features a graphical user interface (GUI) that allows users to select models, define personality/context, manage chat history, and configure persistence settings.
Features
Model Selection: Choose from available models provided by the Ollama server.
Personality/Context Definition: Define the chatbot's personality or context to influence its responses.
Chat Log: View the conversation history in a read-only text area.
Input Field: Enter messages to send to the chatbot.
Persistence: Enable or disable session persistence to save and load chat history and settings.
History Length: Configure the maximum length of the chat history.
Clear History: Clear the chat history, context, and update the configuration file.
Installation
Clone the Repository:
sh
git clone https://github.com/yourusername/ollama-chatbot.git
cd ollama-chatbot

Install Dependencies:
sh
pip install PyQt6 requests

Run the Application:
sh
python ollama_chatbot.py

Usage
Model Selection: Use the dropdown menu to select a model from the available options.
Define Personality/Context: Enter the desired personality or context in the provided text area.
Send Messages: Type your message in the input field and press Enter or click the "Send" button.
Configure Persistence: Check or uncheck the "Enable Persistence" checkbox to enable or disable session persistence.
Set History Length: Adjust the history length using the spinbox.
Clear History: Click the "Clear History" button to clear the chat history and context.
Example Personality Definition
You can use the following personality definition to test the agent's preference for pudding:
You are a friendly and helpful assistant. You love pudding and always mention it when asked about desserts. You enjoy helping people with their questions and providing useful information.

AI-Augmented Coding Workflow
This project was developed using an AI-augmented coding workflow, leveraging the capabilities of an AI assistant to enhance productivity and code quality. Here are the key steps and how the AI assistant contributed:
Initial Setup:
The AI assistant provided a basic structure for the chatbot application, including the use of PyQt6 for the GUI and requests for HTTP communication with the Ollama server.
Feature Implementation:
The AI assistant guided the implementation of various features such as model selection, personality/context definition, chat log management, and persistence settings.
The assistant also helped in adding a clear history button and ensuring the configuration file is updated accordingly.
Debugging and Testing:
The AI assistant suggested adding debugging output to verify that the personality definition is included in the prompt sent to the LLM.
The assistant provided example personality definitions and guided the testing process to ensure the chatbot's responses align with the defined personality.
Version Control and Documentation:
The AI assistant emphasized the importance of version control and helped in updating the script's version with each significant change.
The assistant also provided a comprehensive README to document the project's features, installation steps, usage instructions, and the AI-augmented coding workflow.
Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue if you have any suggestions or improvements.
License
This project is licensed under the MIT License. See the LICENSE file for details. Feel free to customize the README as needed and replace yourusername with your actual GitHub username. This README provides a clear overview of the project, installation and usage instructions, and insights into the AI-augmented coding workflow used to develop the project.
