# streamlit_app.py / main.py
import streamlit as st
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# -------------------------------
# Load environment variables
# -------------------------------
# First try Streamlit secrets.toml
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    # Fallback to local env files
    if os.path.exists("key.env"):
        load_dotenv("key.env")
    elif os.path.exists(".env"):
        load_dotenv(".env")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("❌ No API key found. Please set it in `.streamlit/secrets.toml` or `key.env`/`.env` locally.")
    st.stop()

# -------------------------------
# Import OpenAI
# -------------------------------
import openai
openai.api_key = OPENAI_API_KEY

# -------------------------------
# Prompts and helpers
# -------------------------------
from prompts import QUESTION_CONTEXT, make_eval_prompt

def call_llm_eval(prompt: str, model: str):
    """Call the LLM to evaluate candidate's answer, expecting JSON."""
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a strict JSON-returning Excel interviewer evaluator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=350,
            temperature=0.0
        )
        text = resp["choices"][0]["message"]["content"].strip()
        idx = text.find('{')
        json_text = text if idx == 0 else text[idx:]
        parsed = json.loads(json_text)
        return parsed, text
    except Exception as e:
        return {
            "correctness":"error",
            "score":0,
            "rationale":str(e),
            "improvements":[],
            "canonical_answer":""
        }, f"ERROR: {e}"

# -------------------------------
# Streamlit page setup
# -------------------------------
st.set_page_config(page_title="AI Excel Mock Interviewer", layout="centered")
st.title("AI-Powered Excel Mock Interviewer — PoC")

# Sidebar
st.sidebar.header("⚙️ Settings")
model_choice = st.sidebar.selectbox(
    "Choose LLM model:",
    ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    index=0
)
practice_mode = st.sidebar.radio(
    "Feedback style:",
    ["Interview Mode (feedback only at end)", "Practice Mode (feedback after each question)"]
)

# -------------------------------
# Session State
# -------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.started_at = datetime.utcnow().isoformat()
    st.session_state.q_order = list(QUESTION_CONTEXT.keys())
    st.session_state.current_q_idx = 0
    st.session_state.transcript = []
    st.session_state.scores = {}
    st.session_state.completed = False

st.sidebar.markdown(f"**Session ID:** {st.session_state.session_id}")
st.sidebar.markdown(f"Started at (UTC): {st.session_state.started_at}")

# -------------------------------
# Interview Loop
# -------------------------------
if not st.session_state.completed:
    idx = st.session_state.current_q_idx
    q_key = st.session_state.q_order[idx]
    q_obj = QUESTION_CONTEXT[q_key]

    st.subheader(f"Question {idx+1} of {len(st.session_state.q_order)}")
    st.markdown(f"**{q_obj['question']}**")

    answer = st.text_area("Your answer", key=f"answer_{q_key}", height=160)

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Submit answer"):
            if not answer.strip():
                st.warning("Please enter an answer.")
            else:
                prompt = make_eval_prompt(q_obj["question"], answer, q_obj["tags"])
                with st.spinner("Evaluating..."):
                    parsed, raw_text = call_llm_eval(prompt, model_choice)

                entry = {
                    "question_key": q_key,
                    "question": q_obj["question"],
                    "answer": answer,
                    "evaluation_raw": raw_text,
                    "evaluation": parsed,
                    "timestamp": datetime.utcnow().isoformat()
                }
                st.session_state.transcript.append(entry)
                st.session_state.scores[q_key] = parsed.get("score", 0)

                if "Practice" in practice_mode:
                    st.markdown("### Immediate Feedback")
                    st.json(parsed)

                if idx + 1 >= len(st.session_state.q_order):
                    st.session_state.completed = True
                else:
                    st.session_state.current_q_idx = idx + 1
                st.experimental_rerun()

    with col2:
        if st.button("Skip question"):
            entry = {
                "question_key": q_key,
                "question": q_obj["question"],
                "answer": "",
                "evaluation_raw": "skipped",
                "evaluation": {"correctness":"skipped","score":0,"rationale":"skipped"},
                "timestamp": datetime.utcnow().isoformat()
            }
            st.session_state.transcript.append(entry)
            st.session_state.scores[q_key] = 0
            if idx + 1 >= len(st.session_state.q_order):
                st.session_state.completed = True
            else:
                st.session_state.current_q_idx = idx + 1
            st.experimental_rerun()

# -------------------------------
# Final Summary
# -------------------------------
if st.session_state.completed:
    st.header("📊 Final Report")
    total_score = sum(st.session_state.scores.values())
    max_score = len(st.session_state.q_order) * 10
    pct = (total_score / max_score) * 100 if max_score else 0

    st.metric("Total Score", f"{total_score}/{max_score}", delta=f"{pct:.1f}%")

    for i, e in enumerate(st.session_state.transcript):
        st.subheader(f"Q{i+1}: {e['question']}")
        st.markdown(f"**Answer:**\n```\n{e['answer']}\n```")
        if isinstance(e["evaluation"], dict):
            ev = e["evaluation"]
            st.markdown(f"- **Score:** {ev.get('score')}  \n- **Correctness:** {ev.get('correctness')}")
            st.markdown(f"- **Rationale:** {ev.get('rationale')}")
            if ev.get("improvements"):
                st.markdown("- **Improvements:**")
                for it in ev["improvements"]:
                    st.markdown(f"  - {it}")
            if ev.get("canonical_answer"):
                st.markdown(f"- **Canonical answer:** {ev.get('canonical_answer')}")

    st.subheader("📝 Constructive Feedback")
    summary_prompt = "You are an expert interviewer. Given these Q&A evaluations, produce 3 short paragraphs: strengths, weaknesses, and recommended next steps.\n\n"
    summary_prompt += json.dumps(st.session_state.transcript, indent=2)

    try:
        resp = openai.ChatCompletion.create(
            model=model_choice,
            messages=[
                {"role":"system","content":"You are a friendly career coach and Excel expert."},
                {"role":"user","content":summary_prompt}
            ],
            max_tokens=400,
            temperature=0.2
        )
        st.write(resp["choices"][0]["message"]["content"].strip())
    except Exception as e:
        st.error(f"Feedback generation failed: {e}")

    fname = f"transcript_{st.session_state.session_id}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump({
            "session_id": st.session_state.session_id,
            "started_at": st.session_state.started_at,
            "completed_at": datetime.utcnow().isoformat(),
            "transcript": st.session_state.transcript,
            "total_score": total_score,
            "max_score": max_score
        }, f, indent=2)
    st.success(f"Transcript saved: {fname}")

    if st.button("Start new interview"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()
