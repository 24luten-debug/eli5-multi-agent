# 🤖 ELI5 – Learn Anything Simply

Clear explanations in the simplest possible way using a multi-agent AI system.

---

## 🚀 Live App

👉 https://eli5-multi-agent-6yco7cu8dmitahfmzdqg4y.streamlit.app/

---

## 📌 Problem

Most explanations online are complex and hard to understand.

---

## 💡 Solution

This app explains any topic in a simple, structured “Explain Like I’m 5” format.

---

## 🧠 Architecture

Multi-Agent System:

* Concept Analyzer → understands the query
* Research Agent → fetches data using Tavily API
* Simplifier Agent → simplifies explanation
* Formatter Agent → structures output
* Judge Agent → ensures quality

👉 All agents use Groq LLM for reasoning and generation.

---

## ⚙️ Tech Stack

* Streamlit
* Groq API
* Tavily API
* Python

---

## 🧪 Example

Input:

```
explain ai
```

Output:

* Idea
* Explanation
* Example
* Why it matters

---

## 🔑 Setup

Create `.env` file:

```
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
```

Install dependencies:

```
pip install -r requirements.txt
```

Run:

```
streamlit run app.py
```

---

## 📦 Features

* Multi-agent reasoning
* Real-time web research
* Structured explanations
* Beginner-friendly UI

---

## 👤 Author

Nishad Lute
Om pande
