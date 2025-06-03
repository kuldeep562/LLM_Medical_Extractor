import asyncio
import aiohttp
import json
import time
import sys
from colorama import Fore, Style, init

# ---------------- Configuration ----------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"

# ---------------- Slot Definitions ----------------
SLOTS = {
    "brief_medical_history": "Summarize the patient's overall medical history briefly.",
    "chief_complaints": "Describe the patient's main complaints, how long they have lasted, and the nature of the symptoms.",
    "current_symptoms_and_medical_background": "Provide details of the current symptoms and any relevant medical background.",
    "past_medical_history": "State any past diseases along with the type of diagnosis (e.g., Clinical, Provisional).",
    "hospitalization_and_surgical_history": "Include any previous hospitalizations or surgeries with diagnosis, treatment, and time of admission.",
    "gynecological_history": "Mention any relevant gynecological or obstetric history, including pregnancies or menstrual history.",
    "lifestyle_and_social_activity": "Describe the patient's physical activity habits, time spent, and current activity status.",
    "family_history": "List any family members with known diseases and their age at diagnosis or current age.",
    "allergies_and_hypersensitivities": "Mention any known allergies with the allergen, reaction type, severity, and whether it's active or passive."
}

# ---------------- Slot-Specific Schemas ----------------
SCHEMA_HINTS = {
    "brief_medical_history": '''
{
  "brief_medical_history": "string"
}
''',

    "chief_complaints": '''
{
  "chief_complaints": {
    "Complaint": "string",
    "Duration": "string",
    "Description": "string"
  }
}
''',

    "current_symptoms_and_medical_background": '''
{
  "current_symptoms_and_medical_background": {
    "symptoms": "string",
    "medical_history": "string",
    "allergies": "string",
    "previous_investigations": "string",
    "family_medical_history": "string"
  }
}
''',

    "past_medical_history": '''
{
  "past_medical_history": {
    "Diagnosis_Type": "Clinical | Differential | Final | Provisional | Suspected",
    "Disease": "string"
  }
}
''',

    "hospitalization_and_surgical_history": '''
{
  "hospitalization_and_surgical_history": {
    "Diagnosis": "string",
    "Treatment": "string",
    "Admission_Time": "string"
  }
}
''',

    "gynecological_history": '''
{
  "gynecological_history": "string"
}
''',

    "lifestyle_and_social_activity": '''
{
  "lifestyle_and_social_activity": {
    "Physical_Activity": "string",
    "Time": "string",
    "Status": "string"
  }
}
''',

    "family_history": '''
{
  "family_history": {
    "Relation": "string",
    "Disease_Name": "string",
    "Age": "string"
  }
}
''',

    "allergies_and_hypersensitivities": '''
{
  "allergies_and_hypersensitivities": {
    "Allergy": "string",
    "Allergen": "string",
    "Type_of_Reaction": "string",
    "Severity": "string",
    "Status": "active | passive"
  }
}
'''
}

# ---------------- Color Setup ----------------
COLOR_MAP = list(Fore.__dict__.values())[10:10 + len(SLOTS)]
init(autoreset=True)

# ---------------- LLM Call Function ----------------
async def ask_slot(session, slot_name, instruction, context, color):
    schema_hint = SCHEMA_HINTS.get(slot_name, "")
    prompt = f"""
    Context:
    {context}

    Instruction:
    {instruction}

    Respond ONLY in JSON format for field: {slot_name}

    {schema_hint}

    Make sure field names and nesting are exactly as shown.
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "num_predict": 200
    }

    start_time = time.time()
    try:
        async with session.post(OLLAMA_URL, json=payload) as response:
            res_text = await response.text()
            elapsed = round(time.time() - start_time, 2)

            if response.status == 200:
                try:
                    res_json = json.loads(res_text)
                    raw = res_json.get("response", "").strip()

                    # Parse the nested JSON if possible
                    try:
                        parsed = json.loads(raw)
                    except json.JSONDecodeError:
                        # Try to auto-correct missing closing brackets (very basic fix)
                        raw_fixed = raw.strip()
                        if raw_fixed.endswith(","):
                            raw_fixed = raw_fixed[:-1]
                        if raw_fixed.count("{") > raw_fixed.count("}"):
                            raw_fixed += "}" * (raw_fixed.count("{") - raw_fixed.count("}"))
                        if raw_fixed.count("[") > raw_fixed.count("]"):
                            raw_fixed += "]" * (raw_fixed.count("[") - raw_fixed.count("]"))

                        try:
                            parsed = json.loads(raw_fixed)
                        except Exception as e2:
                            raise Exception(f"Secondary parsing failed: {str(e2)}\nRaw (fixed): {raw_fixed}")

                    # ✅ Print in both cases
                    print(color + f"\n✅ {slot_name.upper()} ({elapsed}s)\n" +
                        json.dumps(parsed, indent=4) + Style.RESET_ALL)

                except Exception as e:
                    print(Fore.RED + f"\n❌ ERROR parsing {slot_name}: {str(e)}\nRaw: {raw}" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"\n❌ ERROR {slot_name}: {res_text[:200]}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"\n❌ EXCEPTION {slot_name}: {str(e)}" + Style.RESET_ALL)

# ---------------- Async Runner ----------------
async def run_all_slots(context):
    timeout = aiohttp.ClientTimeout(total=300)
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = []
        for i, (slot, instruction) in enumerate(SLOTS.items()):
            color = COLOR_MAP[i % len(COLOR_MAP)]
            tasks.append(asyncio.create_task(ask_slot(session, slot, instruction, context, color)))
        await asyncio.gather(*tasks)

# ---------------- CLI Entry Point ----------------
def main():
    print(Fore.CYAN + "📝 Paste the medical context. Press Enter on an empty line to submit:\n" + Style.RESET_ALL)
    lines = []
    while True:
        line = input()
        if not line.strip():  # Empty line = end of input
            break
        lines.append(line)
    context = "\n".join(lines).strip()

    if not context:
        print(Fore.RED + "❌ No context provided." + Style.RESET_ALL)
        return

    # 👇 This is the key line you wanted
    print(Fore.YELLOW + "\n⏳ Sending request to LLM...\n" + Style.RESET_ALL)

    total_start = time.time()
    asyncio.run(run_all_slots(context))
    total_end = time.time()
    print(Fore.GREEN + f"\n🎉 All done in {round(total_end - total_start, 2)}s" + Style.RESET_ALL)


# ---------------- Start ----------------
if __name__ == "__main__":
    main()
