# 🏗️ BIM pilot v 0.2 — AI Assistant for BIM Engineers

An AI-powered assistant built with LangChain, ChromaDB, Groq AI, and Streamlit. Ask technical questions about BIM standards, Revit, Navisworks, LOD Specification, and ISO 19650 — and get accurate, document-grounded answers instantly.


---

## 🚀 Live Demo

Coming soon — Streamlit Cloud deployment in progress.

---

## 📌 What This Project Does

Most BIM engineers waste hours searching through hundreds of pages of 
technical documentation to find answers to simple questions.

This AI assistant solves that problem. It reads your BIM documents, stores 
them in a vector database, and answers your technical questions instantly — 
grounded only in your actual documents, not generic internet data.

---

## ✨ Features

- 💬 Chat interface for asking BIM technical questions
- 📄 Upload your own PDF documents and ask questions about them instantly
- 🧠 Powered by Groq AI with Llama 3.3 70B model
- 🔍 Vector search using ChromaDB for accurate document retrieval
- 📚 Pre-loaded with 5 major BIM documents and 9935 knowledge chunks
- 🔒 Runs locally — your documents never leave your system
- ⚡ Fast responses using Groq inference engine

---

## 📚 Pre-loaded Knowledge Base

| Document | Pages |
|---|---|
| ISO 19650 Edition 4 | BIM information management standard |
| LOD Specification 2025 | Level of Development specification |
| Revit Architecture User Guide | Autodesk Revit complete guide |
| Navisworks Getting Started Guide | Clash detection and coordination |
| BIM Execution Plan Template | Project BIM planning template |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| LangChain | RAG pipeline orchestration |
| ChromaDB | Local vector database |
| HuggingFace Embeddings | Document embedding model |
| Groq AI + Llama 3.3 | Language model for answers |
| Streamlit | Web interface |
| PyPDF | PDF document loading |

---

## 📁 Project Structure