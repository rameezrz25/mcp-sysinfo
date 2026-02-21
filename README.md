<div align="center">
  <h1> 🌌 mcp-sysinfo 🌌 </h1>
  <p><i>A beautiful, AI-powered hardware & system benchmarking tool for your local machine</i></p>

  ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
  ![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
  ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
  ![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
</div>

<br>

Welcome to **`mcp-sysinfo`**! 🌟 This project is a shiny hardware & system benchmarking tool that allows an Artificial Intelligence to run tests and analyze your computer's performance in real time!

If you are a new Python programmer, this is a **fantastic** example of how to connect a large language model (like Gemini) to actual Python code that runs locally on your machine using the magic of the **Model Context Protocol (MCP)**.

---

## 🧐 What is this project doing?

Normally, an AI like ChatGPT or Gemini is stuck in the cloud ☁️. It doesn't know how much RAM your computer has, and it can't run a speed test on your CPU. 

This project bridges that gap by giving the AI **"tools"** 🛠️ it can use!

**Here is how it works step-by-step:**
1. 🗣️ **You ask a question**: You type something like, *"Is my CPU fast?"*
2. 🧠 **The AI receives the question**: The AI realizes it needs to run a CPU benchmark tool to answer your question.
3. 📡 **The AI asks for data**: The AI sends a message saying, *"Hey, please run the tool called `run_cpu_benchmark` for me."*
4. 💻 **The Python Server obeys**: Our local Python script actually runs the heavy math calculations on your computer to test the CPU, and gets a score.
5. 📤 **The Python Server replies**: The script sends the score back to the AI.
6. ✨ **The AI gives you the answer**: The AI reads the score and writes a human-friendly response like, *"Your CPU scored 300,000, which is very fast!"*

## 🏗️ Why use MCP? (The Architecture)

We use the **Model Context Protocol (MCP)** to keep things perfectly organized and totally secure 🔒. We split the code into two main parts:

1. ⚙️ **The Server (`mcp_server.py`)**: This script contains the actual Python benchmarking functions (like measuring IO speeds). It acts as a menu, saying *"Here are the 4 tools I know how to run."*
2. 🤖 **The Client (`mcp_client.py`)**: This script talks to the Gemini API. It shows the AI the "menu" of tools from the server. When the AI wants to use a tool, the client passes the message to the server, waits for the result, and gives it back to the AI.

> 💡 **Security Note:** This separation means the AI is safely restricted. It can't run arbitrary commands on your computer; it can *only* run the specific benchmarking tools you provided in the server script!

---

## 📂 Deliverables inside this folder

- 📜 **`mcp_server.py`**: The MCP Server. Exposes system tools like `run_cpu_benchmark()`.
- 🕹️ **`mcp_client.py`**: The MCP Client. Instantiates Gemini, fetches the tools, asks the model to benchmark the system, fields its tool usages, and prints the AI's final system analysis.
- 📦 **`sample_benchmark.json`**: An example payload of what the underlying MCP raw tool outputs look like when aggregated.

---

## 🛠️ Prerequisites

1. **Install required dependencies:**
   ```bash
   pip install google-generativeai flask python-dotenv
   ```
2. **Create a `.env` file** in the root directory and add your key:
   ```bash
   GEMINI_API_KEY="your-gemini-api-key"
   ```

---

## 🎮 Example Run

### 🌐 Web UI (Tailwind CSS)

You can run a beautiful web interface to interact with the benchmarking assistant!

```bash
# Ensure you are using the virtual environment if applicable
python3 app.py
```
Then, open `http://127.0.0.1:5001/` in your browser. 🌍

**Features:**
- 💬 Type a custom prompt in the chatbox, e.g., *"Just check my memory and IO speeds."*
- 🚀 Click **Ask** to let Gemini run the corresponding tools and stream the insights back!

### 💻 CLI Mode

You can also run the client directly from the command line, and optionally provide a custom prompt:

```bash
python3 mcp_client.py --prompt "Only run the CPU benchmark and tell me if it's fast enough."
```

---

## 📸 Example Prompts

Here are a few different demo command prompts you can try to see how the GenAI controller uses its available tools in real time!

### 🎯 Prompt triggering a single API/tool:
* *"Only run a CPU benchmark and tell me if its score is good."* -> Triggers `run_cpu_benchmark()`
* *"What is my system info?"* -> Triggers `get_system_info()`

![Single API Prompt Demo](single_api_demo.png)

### 🤹‍♀️ Prompt triggering multiple APIs/tools sequentially:
* *"Check my memory and IO speeds, then summarize the results."* -> Triggers `run_memory_benchmark()` and `run_io_benchmark()`
* *"Run all performance diagnostics to give me a hardware analysis."* -> Triggers `get_system_info()`, `run_cpu_benchmark()`, `run_memory_benchmark()`, and `run_io_benchmark()`

![Multiple API Prompt Demo](multi_api_demo.png)

---

## 🔄 Flow Outcome Recap

1. 🤝 Handshake establishes JSON-RPC connection.
2. 🔍 Tools are discovered and fed to Gemini's schema parameters.
3. 🤔 Gemini decides to use `get_system_info`, `run_cpu_benchmark`, `run_memory_benchmark`, and `run_io_benchmark`.
4. 🏃‍♂️ The isolated MCP server executes these, returning metrics like CPU scores, memory operations/sec, and disk read/write bandwidth in JSON.
5. 📊 Gemini digests the JSON structured data and summarizes bottlenecks and insights into a friendly AI Analyst Report!
