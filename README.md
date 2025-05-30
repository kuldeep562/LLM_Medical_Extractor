# LLM Medical Context Extractor

This tool uses a local LLM (via Ollama) to extract structured medical information from patient conversations.

## 🔍 Features

- Extracts 10 specific medical slots using LLM prompts
- Runs asynchronously using `aiohttp`
- Terminal colored outputs using `colorama`
- Logs output to `llm_log.txt`

## 🧠 Example Input

See `llm_context.txt` for example patient conversations.

## 🚀 How to Run

1. Install dependencies:

```bash
pip install aiohttp colorama
