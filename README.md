
# Personal AI Assistant with Proactive Notifications 🚀

This project is a personal AI assistant designed to act as my digital twin on my portfolio. It's capable of answering questions about my background, skills, and experience, while also serving as an active monitoring tool for professional opportunities.

My philosophy was simple: **total control over the logic** for maximum performance and customization. That's why I deliberately chose to build the agent's core "from scratch" in **pure Python**, without relying on frameworks like LangChain or LlamaIndex.

The user interface is handled by **Chainlit** for a modern, fast, and elegant experience.



## ✨ Key Features

* **"From Scratch" Logic**: The agent's core (context management, tool calls) is built in pure Python for maximum optimization and transparency.
* **Reactive UI**: Uses Chainlit for a smooth and asynchronous chat interface.
* **RAG (Retrieval-Augmented Generation)**: The agent draws its knowledge from local documents (CV, PDF profile, summary) to provide accurate and contextual answers.
* **Intelligent Tool Usage**: The AI can decide to use tools (Python functions) to perform specific tasks.
* **Proactive Real-Time Notifications**: Thanks to **Pushover**, the agent instantly notifies me on my phone when high-value interactions occur.

---

## 🧠 How It Works: The Architecture

This project transforms a simple chatbot into a truly proactive agent. Here is the operational flow:

1.  **User Interface (Chainlit)**: Manages the chat display, receives user messages, and displays the AI's responses.
2.  **Agent Orchestrator (app.py)**:
    * On startup, the agent loads context from local files (`.pdf`, `.txt`) to build its knowledge base.
    * Each user message is enriched with this context and a detailed system prompt before being sent to the LLM API.
3.  **The Brain (Groq & Gemma2-9b-it)**: The Groq language model processes the request. Thanks to the system prompt's instructions and the description of available "tools," it can either generate a text response or decide to call a Python function.
4.  **Tools**: If the LLM requests to use a tool (e.g., `record_user_details`), the corresponding Python logic is executed.
5.  **The Bridge to Reality (Pushover)**: The `push()` tool sends an instant notification, turning a digital conversation into a concrete, actionable alert.



---

## 🔔 The Magic: The Notification System

The true power of this assistant lies in its ability to filter out the noise and alert me only when it's relevant. It turns a passive portfolio into an active monitoring tool.

I am notified instantly in the following cases:

* **❓ Unanswered Question**: If a visitor asks a relevant question about my career that the AI cannot answer, I receive the question. This is a perfect opportunity to improve the agent's knowledge base.
* **🤝 Interest in Collaboration or a Project**: When a user mentions a project opportunity or a desire to collaborate.
* **💼 Hiring Proposal**: If the conversation indicates a clear interest in recruitment and the user leaves their contact details.

---

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **UI Framework**: Chainlit
* **Language Model (LLM)**: Gemma2-9b-it via the Groq API
* **Notifications**: Pushover
* **Dependency Management**: Pip
* **Document Reading**: PyPDF

---

## ⚙️ Setup and Installation

Follow these steps to run the assistant on your local machine.

### 1. Prerequisites

* Python 3.10 or higher
* A [GroqCloud](https://console.groq.com/keys) account to get an API key.
* A [Pushover](https://pushover.net/) account to get a user key and an application token key.

### 2. Clone the Repository

```bash
git clone [https://github.com/Cheikhfall03/AssistantResume.git](https://github.com/Cheikhfall03/AssistantResume.git)
cd AssistantResume
### 3. Install Dependencies

> It's recommended to work in a virtual environment.

#### Bash

```bash
# Create a virtual environment
python -m venv venv

# Activate the environment (macOS/Linux)
source venv/bin/activate

# Activate the environment (Windows)
# venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt

