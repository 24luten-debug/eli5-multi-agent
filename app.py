import os
import re
import json
import streamlit as st
from groq import Groq
from tavily import TavilyClient

# -------------------------------
# API KEYS
# -------------------------------
import os

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


MODEL = "llama-3.1-8b-instant"

st.set_page_config(page_title="ELI5 Explainer", page_icon="🤖", layout="centered")
st.title("🤖 ELI5 – Learn Anything Simply")
st.write("Clear explanations in the simplest possible way")

SECTIONS = ["HOOK", "EXPLANATION", "ANALOGY", "WHY", "CONCLUSION", "FUN_FACT"]

# -------------------------------
# Helpers
# -------------------------------
def call_llm(messages, temperature=0.4, max_tokens=650):
    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()

def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()

def parse_json_or_sections(text):
    raw = (text or "").strip()

    try:
        candidate = raw
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
            candidate = re.sub(r"\s*```$", "", candidate)
        data = json.loads(candidate)
        if isinstance(data, dict):
            return {k: clean_text(str(data.get(k, ""))) for k in SECTIONS}
    except Exception:
        pass

    result = {k: "" for k in SECTIONS}
    current = None

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        matched = False
        for key in SECTIONS:
            if line.startswith(key + ":"):
                current = key
                result[key] = clean_text(line[len(key) + 1 :])
                matched = True
                break

        if not matched and current:
            result[current] = (result[current] + " " + line).strip()

    return result

def word_count(text):
    return len(clean_text(text).split())

def all_sections_good(data):
    mins = {
        "HOOK": 8,
        "EXPLANATION": 16,
        "ANALOGY": 10,
        "WHY": 10,
        "CONCLUSION": 5,
        "FUN_FACT": 5,
    }
    for k, m in mins.items():
        if word_count(data.get(k, "")) < m:
            return False
    return True

def safe_text(text, fallback):
    text = clean_text(text)
    return text if text else fallback

def topic_profile(query):
    q = (query or "").lower()
    if "ai" in q or "artificial intelligence" in q:
        return {
            "hook": "Think about how a phone can recognize faces or suggest the next song.",
            "explanation": "AI means a computer learns patterns from examples and uses them to make guesses or decisions.",
            "analogy": "It is like a student who gets better by practicing on many example questions.",
            "why": "It matters because computers can help with tasks like finding patterns, sorting data, and making quick choices.",
            "conclusion": "So, AI is a way for computers to learn from examples.",
            "fun_fact": "Fun fact: AI can be trained for very different jobs, from games to photos.",
        }
    if "ram" in q:
        return {
            "hook": "Think about a desk where you keep the books you are using right now.",
            "explanation": "RAM is the computer's short-term working memory.",
            "analogy": "It is like the space on your desk where you keep open books and notes.",
            "why": "It matters because it helps the computer work quickly on the things you are using now.",
            "conclusion": "So, RAM is the computer's quick workspace.",
            "fun_fact": "Fun fact: RAM forgets everything when the power goes off.",
        }
    if "internet" in q:
        return {
            "hook": "Think about roads that connect many houses in a city.",
            "explanation": "The internet connects computers so they can share information.",
            "analogy": "It is like a huge road network for messages and files.",
            "why": "It matters because it helps people send things and find information fast.",
            "conclusion": "So, the internet is a big connection system for computers.",
            "fun_fact": "Fun fact: tiny data pieces travel across many different paths.",
        }
    if "cpu" in q:
        return {
            "hook": "Think about a chef in a kitchen following many small steps.",
            "explanation": "The CPU is the part of the computer that follows instructions and does the main work.",
            "analogy": "It is like the chef who keeps the kitchen moving.",
            "why": "It matters because the computer needs it to run programs and finish tasks.",
            "conclusion": "So, the CPU is the computer's main worker.",
            "fun_fact": "Fun fact: a faster CPU can finish many tasks more quickly.",
        }
    return {
        "hook": f"Think about {query} as something you can break into small parts.",
        "explanation": f"{query} becomes easier when you look at the main idea and the simple parts behind it.",
        "analogy": "It is like sorting mixed objects into neat groups.",
        "why": "It matters because small steps make hard ideas easier to understand.",
        "conclusion": f"So, {query} is easier once it is explained step by step.",
        "fun_fact": "Fun fact: simple examples often make hard ideas much easier.",
    }

# -------------------------------
# Agent 1: Concept Analyzer
# -------------------------------
def concept_analyzer(query):
    messages = [
        {
            "role": "system",
            "content": """
Extract the topic into short notes.

Return JSON only:
{
  "core": "...",
  "key_points": ["...", "...", "..."],
  "everyday_angle": "..."
}

Rules:
- very short
- simple words
- no extra explanation
- no commentary
""",
        },
        {"role": "user", "content": query},
    ]
    return call_llm(messages, temperature=0.2, max_tokens=220)

# -------------------------------
# Agent 2: Research Agent
# -------------------------------
def research_agent(query):
    try:
        result = tavily_client.search(query=query, max_results=3)
        items = result.get("results", [])
        snippets = []

        for item in items:
            title = clean_text(item.get("title", ""))
            content = clean_text(item.get("content", ""))
            if content:
                snippets.append(f"{title}: {content}" if title else content)

        return "\n".join(snippets[:3])[:700] if snippets else "No external research available."
    except Exception:
        return "No external research available."

# -------------------------------
# Agent 3: Simplifier
# -------------------------------
def simplifier(concepts, research, query):
    profile = topic_profile(query)
    messages = [
        {
            "role": "system",
            "content": """
You are an expert at explaining things simply.

You are NOT childish.
You are NOT formal.
You are NOT a textbook.

Your job is to make the idea feel obvious and easy.

Return JSON only:
{
  "HOOK": "...",
  "EXPLANATION": "...",
  "ANALOGY": "...",
  "WHY": "...",
  "CONCLUSION": "...",
  "FUN_FACT": "..."
}

Rules:
- use plain English
- use short sentences
- no jargon unless very briefly explained
- no phrases like "computer system", "machine learning", "automate tasks", "improve performance"
- no baby talk
- no fantasy talk
- keep it natural and direct
""",
        },
        {
            "role": "user",
            "content": f"""
Topic: {query}

Concept notes:
{concepts}

Research notes:
{research}

Use this style direction:
HOOK: {profile["hook"]}
EXPLANATION: {profile["explanation"]}
ANALOGY: {profile["analogy"]}
WHY: {profile["why"]}
CONCLUSION: {profile["conclusion"]}
FUN_FACT: {profile["fun_fact"]}

Write the JSON now.
""",
        },
    ]
    return call_llm(messages, temperature=0.7, max_tokens=550)

# -------------------------------
# Agent 4: Formatter
# -------------------------------
def formatter(text):
    messages = [
        {
            "role": "system",
            "content": """
You clean the answer without making it harder.

Return JSON only with the same keys:
HOOK, EXPLANATION, ANALOGY, WHY, CONCLUSION, FUN_FACT

Rules:
- keep meaning
- keep simple language
- keep natural tone
- do not add new sections
- do not make it formal
""",
        },
        {"role": "user", "content": text},
    ]
    return call_llm(messages, temperature=0.15, max_tokens=450)

# -------------------------------
# Agent 5: Judge
# -------------------------------
def judge(text, query):
    profile = topic_profile(query)
    messages = [
        {
            "role": "system",
            "content": f"""
You are a strict clarity judge.

Your job:
- make sure the answer is simple
- make sure it sounds natural
- remove textbook words
- keep it beginner-friendly
- do not make it childish

Return JSON only:
{{
  "HOOK": "...",
  "EXPLANATION": "...",
  "ANALOGY": "...",
  "WHY": "...",
  "CONCLUSION": "...",
  "FUN_FACT": "..."
}}

Use this style if needed:
HOOK: {profile["hook"]}
EXPLANATION: {profile["explanation"]}
ANALOGY: {profile["analogy"]}
WHY: {profile["why"]}
CONCLUSION: {profile["conclusion"]}
FUN_FACT: {profile["fun_fact"]}
""",
        },
        {"role": "user", "content": text},
    ]
    return call_llm(messages, temperature=0.25, max_tokens=550)

# -------------------------------
# Repair pass
# -------------------------------
def repair_if_needed(final_text, query, concepts, research):
    parsed = parse_json_or_sections(final_text)
    if all_sections_good(parsed):
        return final_text

    profile = topic_profile(query)
    repair_prompt = f"""
Rewrite this into a clean, simple ELI5 answer in JSON only.

Topic: {query}

Concept notes:
{concepts}

Research notes:
{research}

Current draft:
{final_text}

Rules:
- keep it simple and natural
- do not sound childish
- do not sound like a textbook
- do not use "computer system", "machine learning", "automate tasks", "improve performance"
- fill every key
- return only JSON with keys:
HOOK, EXPLANATION, ANALOGY, WHY, CONCLUSION, FUN_FACT

Style:
HOOK: {profile["hook"]}
EXPLANATION: {profile["explanation"]}
ANALOGY: {profile["analogy"]}
WHY: {profile["why"]}
CONCLUSION: {profile["conclusion"]}
FUN_FACT: {profile["fun_fact"]}
"""
    return call_llm(
        [
            {"role": "system", "content": "You are an expert ELI5 rewritter."},
            {"role": "user", "content": repair_prompt},
        ],
        temperature=0.35,
        max_tokens=600,
    )

# -------------------------------
# Generate
# -------------------------------
def generate_answer(query):
    concepts = concept_analyzer(query)
    research = research_agent(query)

    for _ in range(3):
        draft = simplifier(concepts, research, query)
        cleaned = formatter(draft)
        judged = judge(cleaned, query)
        final_text = repair_if_needed(judged, query, concepts, research)git --version
        parsed = parse_json_or_sections(final_text)
        if all_sections_good(parsed):
            return parsed, concepts, research, draft, cleaned, final_text

    fallback = topic_profile(query)
    parsed = {
        "HOOK": fallback["hook"],
        "EXPLANATION": fallback["explanation"],
        "ANALOGY": fallback["analogy"],
        "WHY": fallback["why"],
        "CONCLUSION": fallback["conclusion"],
        "FUN_FACT": fallback["fun_fact"],
    }
    return parsed, concepts, research, "", "", json.dumps(parsed)

# -------------------------------
# UI
# -------------------------------
query = st.text_input("Enter a topic")

if st.button("Explain"):
    if query.strip():
        with st.spinner("Thinking..."):
            result, concepts, research, draft, formatted, final_text = generate_answer(query.strip())

        st.subheader("✨ Explanation")

        st.markdown("### 🧠 Idea")
        st.write(result["HOOK"])

        st.markdown("### 📖 Explanation")
        st.write(result["EXPLANATION"])

        st.markdown("### 🔁 Example")
        st.write(result["ANALOGY"])

        st.markdown("### 💡 Why it matters")
        st.write(result["WHY"])

        st.markdown("### ✅ Summary")
        st.write(result["CONCLUSION"])

        st.markdown("### 🤯 Fun fact")
        st.write(result["FUN_FACT"])

        with st.expander("🔍 Debug"):
            st.write("Concept:", concepts)
            st.write("Research:", research)
            st.write("Draft:", draft)
            st.write("Formatted:", formatted)
            st.write("Final:", final_text)