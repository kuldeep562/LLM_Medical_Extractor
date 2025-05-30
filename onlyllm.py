# import asyncio
# import aiohttp
# import json
# import time

# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL = "llama3.2:3b"

# SLOTS = [
#     "brief_medical_history",
#     "chief_complaints",
#     "past_medical_history",
#     "personal_history",
#     "family_history",
#     "treatment_history",
#     "allergy_history",
#     "diagnostic_reports",
#     "clinical_findings",
#     "provisional_diagnosis"
# ]

# async def ask_question(session, context, slot, delay=0):
#     await asyncio.sleep(delay)
#     start = time.time()
#     # Prompt optimized slightly
#     prompt = f"From the text below, extract only the '{slot}':\n\n{context}"
#     payload = {"model": MODEL, "prompt": prompt, "stream": False}

#     for attempt in range(2):  # Retry max 2 times
#         try:
#             async with session.post(OLLAMA_URL, json=payload) as response:
#                 res_text = await response.text()
#                 if response.status == 200:
#                     res_json = json.loads(res_text)
#                     return slot, res_json.get("response", "").strip(), round(time.time() - start, 2)
#                 else:
#                     error_text = f"ERROR: {res_text.strip()[:200]}"
#         except Exception as e:
#             error_text = f"ERROR: {str(e)}"
#         await asyncio.sleep(1)
#     return slot, error_text, round(time.time() - start, 2)

# async def process_all_slots(context):
#     print("⏳ Sending all questions to LLM...\n")
#     timeout = aiohttp.ClientTimeout(total=500)
#     connector = aiohttp.TCPConnector(limit=20)  # Increased concurrency
#     async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
#         tasks = [ask_question(session, context, slot, delay=i * 0.1) for i, slot in enumerate(SLOTS)]
#         for future in asyncio.as_completed(tasks):
#             slot, answer, taken = await future
#             print(f"\n📌 {slot.upper()} ({taken}s):\n{answer}\n{'-'*50}")

# def main():
#     print("📝 Enter your medical context (paste and press Enter twice):\n")
#     lines = []
#     while True:
#         try:
#             line = input()
#         except EOFError:
#             break
#         if line.strip() == "":
#             break
#         lines.append(line)
#     context = "\n".join(lines).strip()
#     if not context:
#         print("❌ No context provided.")
#         return

#     total_start = time.time()
#     asyncio.run(process_all_slots(context))
#     total_end = time.time()
#     print(f"\n✅ Done in {round(total_end - total_start, 2)}s")

# if __name__ == "__main__":
#     main()


import asyncio
import aiohttp
import json
import time
import datetime
from colorama import Fore, Style, init

# ---------------- Configuration ----------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"
LOG_FILE = "llm_log.txt"

SLOTS = {
    "brief_medical_history": "Summarize the patient's overall medical history briefly.",
    "chief_complaints": "What are the patient's main complaints or symptoms that led her to seek care?",
    "past_medical_history": "Mention any significant past medical events, surgeries, or chronic conditions.",
    "personal_history": "Describe relevant personal health or lifestyle factors such as habits, occupation, or routines.",
    "family_history": "Note any family health conditions or hereditary illnesses.",
    "treatment_history": "Mention any medications, therapies, or treatments the patient has tried.",
    "allergy_history": "State any known or suspected allergies and reactions.",
    "diagnostic_reports": "Summarize any diagnostic tests mentioned and their results.",
    "clinical_findings": "Mention any clinical observations or findings from examination.",
    "provisional_diagnosis": "Based on the symptoms and context, what could be a possible diagnosis?"
}

TOKEN_LIMITS = {
    "brief_medical_history": 50,
    "chief_complaints": 40,
    "past_medical_history": 60,
    "personal_history": 50,
    "family_history": 40,
    "treatment_history": 40,
    "allergy_history": 40,
    "diagnostic_reports": 30,
    "clinical_findings": 50,
    "provisional_diagnosis": 60
}

COLOR_MAP = [
    Fore.CYAN, Fore.MAGENTA, Fore.YELLOW, Fore.BLUE,
    Fore.GREEN, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX,
    Fore.LIGHTCYAN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTGREEN_EX
]

# Initialize colorama for cross-platform terminal color support
init(autoreset=True)

# ---------------- Logging ----------------
def log_to_file(text: str):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {text}\n")

# ---------------- Core Function ----------------
async def ask_question(session, context, slot, delay=0):
    await asyncio.sleep(delay)
    start = time.time()
    prompt = f"{SLOTS[slot]}\n\n{context}"
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "num_predict": TOKEN_LIMITS.get(slot, 50)
    }

    for attempt in range(2):
        try:
            async with session.post(OLLAMA_URL, json=payload) as response:
                res_text = await response.text()
                if response.status == 200:
                    res_json = json.loads(res_text)
                    result = res_json.get("response", "").strip()
                    duration = round(time.time() - start, 2)
                    return slot, result, duration
                else:
                    error = f"ERROR: {res_text.strip()[:200]}"
        except Exception as e:
            error = f"ERROR: {str(e)}"
        await asyncio.sleep(1)

    return slot, error, round(time.time() - start, 2)

# ---------------- Async Runner ----------------
async def process_all_slots(context):
    print(Fore.YELLOW + "⏳ Sending all questions to LLM...\n" + Style.RESET_ALL)
    log_to_file("=== NEW SESSION START ===")
    log_to_file(f"INPUT:\n{context}\n")

    timeout = aiohttp.ClientTimeout(total=500)
    connector = aiohttp.TCPConnector(limit=20)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [ask_question(session, context, slot, delay=i * 0.1) for i, slot in enumerate(SLOTS.keys())]
        for i, future in enumerate(asyncio.as_completed(tasks)):
            slot, answer, taken = await future
            color = COLOR_MAP[i % len(COLOR_MAP)]
            formatted = f"{color}\n📌 {slot.upper()} ({taken}s):\n{answer}\n{'-' * 50}"
            print(formatted)
            log_to_file(f"\n📌 {slot.upper()} ({taken}s):\n{answer}\n{'-' * 50}")

# ---------------- CLI Entry Point ----------------
def main():
    print(Fore.CYAN + "📝 Enter your medical context (paste and press Enter twice):\n" + Style.RESET_ALL)
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "":
            break
        lines.append(line)
    context = "\n".join(lines).strip()

    if not context:
        print(Fore.RED + "❌ No context provided." + Style.RESET_ALL)
        return

    total_start = time.time()
    asyncio.run(process_all_slots(context))
    total_end = time.time()
    print(Fore.GREEN + f"\n✅ Done in {round(total_end - total_start, 2)}s" + Style.RESET_ALL)
    log_to_file(f"\n✅ Total Time: {round(total_end - total_start, 2)}s\n")

if __name__ == "__main__":
    main()
