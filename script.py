from groq import Groq
from duckduckgo_search import DDGS

import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Tools ---
def calculator(expr):
    allowed = set('0123456789+-*/.() ')
    return str(eval(expr)) if all(c in allowed for c in expr) else "Invalid"

def web_search(query):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])

TOOLS = {"calculator": calculator, "web_search": web_search}

# --- Agent loop ---
messages = [
    {"role": "system", "content": """You are an AI agent with tools:
- calculator: Math like '25*4'
- web_search: Search the internet
To use: ACTION: tool_name | input
After results, give final answer."""},
    {"role": "user", "content": "What is 847*293 and latest AI trends?"}
]

for step in range(5):
    resp = client.chat.completions.create(
        model="qwen/qwen3.8-27b", messages=messages,
        max_tokens=500, temperature=0.2
    )
    reply = resp.choices[0].message.content
    print(f"Step {step+1}: {reply[:100]}...")

    if "ACTION:" in reply:
        line = [l for l in reply.split('\n') if 'ACTION:' in l][0]
        parts = line.split("ACTION:")[1].strip().split("|", 1)
        name, inp = parts[0].strip(), parts[1].strip() if len(parts)>1 else ""
        result = TOOLS[name](inp)
        print(f"  Tool result: {result[:100]}")
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Tool result: {result}"})
    else:
        print(f"\nFINAL: {reply}")
        break