# multi-ai-agent-debate
A Streamlit-based web application featuring a multi-agent debate and vision pipeline powered by the Gemini and Groq APIs.
Studying automation and control with limited Python experience, I grew tired of basic terminal scripts and wanted to build a functional web application capable of handling complex tasks.

The Project Goal
I wanted a multi-agent AI setup. Since premium platforms were too expensive, I built my own version using free developer APIs.

The Learning Process
It took a few days of debugging Streamlit session states, file hashes and API chaining to get it built. I used AI for the boilerplate code, but debugging the errors, improving the UI, and connecting the APIs taught me real-world data flow and integration skills that static textbooks cannot teach.


Features
-Multi-agent architecture powered by free APIs
-Interactive web UI built with Streamlit
-Real-time session state management and file handling

Prerequisites & Installation
Make sure you have Python 3.8 or higher installed on your system. Open your terminal in the project directory and run:

pip install streamlit pillow google-genai groq requests

Environment Configuration
This app requires API keys from both Groq and Google Gemini to power the multi-agent workflow. You need to declare them in your environment variables before launching.

On Windows (PowerShell):

$env:GROQ_API_KEY="your_groq_api_key_here"
$env:GEMINI_API_KEY="your_gemini_api_key_here"

On macOS / Linux (Terminal):

export GROQ_API_KEY="your_groq_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"


How to Run
Start the Streamlit application from your terminal:
streamlit run "the agent.py"

Open the local URL provided in your terminal (usually http://localhost:8501) in your browser.

Use the sidebar to upload files or documents, enter your prompt, and trigger the multi-agent debate and consensus pipeline.
