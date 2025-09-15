# AI-Powered Excel Mock Interviewer

[![Streamlit App](https://img.shields.io/badge/Streamlit-Deployed-brightgreen)](https://excelinterviewcandiate.streamlit.app/)

🚀 Test project / Proof of Concept for an **AI-driven Excel Interview Assistant**.  
This project simulates a **mock Excel interview** where candidates answer Excel-related questions and receive real-time or post-interview evaluation powered by LLaMA 3.1 (via Hugging Face).  

---

## 🔹 Live Demo
👉 [Try the App on Streamlit](https://excelinterviewcandiate.streamlit.app/)

---

## 🔹 Problem Statement
As per the assignment brief:

> Manual Excel technical interviews are a bottleneck — they consume senior analysts’ time, are inconsistent, and slow down the hiring process. An **AI-powered interviewer** can solve this by simulating interviews, evaluating answers, and providing feedback automatically.

---

## 🔹 Functionality
✅ Structured Interview Flow  
- Introduces itself, explains the process, and walks through multiple Excel questions.  

✅ Two Interview Modes  
- **Interview Mode** → Candidate answers all questions, feedback given at the end.  
- **Practice Mode** → Immediate feedback after each answer, with option to proceed to next question.  

✅ Intelligent Evaluation  
- Uses **LLaMA 3.1 Instruct models** (via Hugging Face Inference API).  
- Candidate responses are parsed and evaluated on correctness, score, rationale, and suggested improvements.  

✅ Feedback & Report  
- At the end, the system generates a **performance summary** with strengths, weaknesses, and recommendations.  
- Transcript and scores are stored as JSON for analysis.  

---

## 🔹 Problems Solved
- **Removes bottleneck** in manual Excel interviews.  
- **Standardizes evaluation**, making hiring fair and consistent.  
- **Saves time** for senior analysts by automating first-round skill checks.  
- **Improves candidate experience** with clear, constructive feedback.  

---

## 🔹 Future Scope
Based on the assignment requirements and possible enhancements:
- 🔹 **Larger Question Bank** → Expand beyond basic Excel to cover advanced use cases (PivotTables, VBA, Power Query).  
- 🔹 **Adaptive Interviewing** → Questions chosen dynamically based on candidate performance.  
- 🔹 **Analytics Dashboard** → For recruiters to compare candidates across attempts.  
- 🔹 **Fine-tuned Models** → Train on real interview transcripts to improve evaluation accuracy.  
- 🔹 **Integration with ATS** → Seamlessly push results into Applicant Tracking Systems.  
- 🔹 **Multi-skill Assessment** → Extend framework for SQL, Python, and Data Analytics skills.  
- 🔹 **Dynamic Question Sourcing** → Questions can be pulled directly from a **central question bank or JSON file**, making the system extensible without modifying code.  

---

## 🔹 Tech Stack
- **Frontend/UI**: [Streamlit](https://streamlit.io)  
- **LLM**: Meta’s **LLaMA 3.1 Instruct models** via Hugging Face Inference API  
- **Deployment**: Streamlit Community Cloud  
- **Secrets Management**: Streamlit `secrets.toml`  

---

## 🔹 Installation & Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/excel_interview.git
cd excel_interview
