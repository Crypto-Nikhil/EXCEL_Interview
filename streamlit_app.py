import streamlit as st
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from prompts import QUESTION_CONTEXT, make_eval_prompt

# -------------------------------
# Load Hugging Face token
# -------------------------------
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except Exception:
    if os.path.exists("key.env"):
        load_dotenv("key.env")
    elif os.path.exists(".env"):
        load_dotenv(".env")
    HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    st.error("❌ No Hugging Face token found. Please set HF_TOKEN in .streamlit/secrets.toml or .env.")
    st.stop()

# -------------------------------
# Hugging Face Client
# -------------------------------
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)


def call_llm_eval(prompt: str, model: str):
    """Call the Hugging Face LLaMA model to evaluate candidate's answer, expecting JSON."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a strict JSON-returning Excel interviewer evaluator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=350,
            temperature=0.0
        )
        text = resp.choices[0].message["content"].strip()
        idx = text.find('{')
        json_text = text if idx == 0 else text[idx:]
        parsed = json.loads(json_text)
        return parsed, text
    except Exception as e:
        return {
            "correctness": "error",
            "score": 0,
            "rationale": str(e),
            "improvements": [],
            "canonical_answer": ""
        }, f"ERROR: {e}"


def render_feedback(parsed: dict, title="Feedback"):
    """Nicely format the evaluation JSON for display."""
    st.markdown(f"### {title}")
    if not isinstance(parsed, dict):
        st.write(parsed)
        return

    st.markdown(f"**Correctness:** {parsed.get('correctness','N/A')}")
    st.markdown(f"**Score:** {parsed.get('score','N/A')}")
    st.markdown(f"**Rationale:** {parsed.get('rationale','')}")

    improvements = parsed.get("improvements", [])
    if improvements:
        st.markdown("**Improvements:**")
        for imp in improvements:
            st.markdown(f"- {imp}")

    if parsed.get("canonical_answer"):
        st.markdown("**Canonical Answer:**")
        st.code(parsed["canonical_answer"], language="excel")


# -------------------------------
# Streamlit page setup
# -------------------------------
st.set_page_config(page_title="AI Excel Mock Interviewer", layout="centered")
st.title("AI-Powered Excel Mock Interviewer — LLaMA 3.1")

# Sidebar
st.sidebar.header("⚙️ Settings")
model_choice = st.sidebar.selectbox(
    "Choose model:",
    ["meta-llama/Llama-3.1-8B-Instruct", "meta-llama/Llama-3.1-70B-Instruct"],
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
                # Show immediate feedback, pause until user clicks Next
                render_feedback(parsed, "✅ Immediate Feedback")

                if st.button("Next question ➡️"):
                    if idx + 1 >= len(st.session_state.q_order):
                        st.session_state.completed = True
                    else:
                        st.session_state.current_q_idx = idx + 1
                    st.rerun()
            else:
                # Interview Mode -> auto advance
                if idx + 1 >= len(st.session_state.q_order):
                    st.session_state.completed = True
                else:
                    st.session_state.current_q_idx = idx + 1
                st.rerun()

    if st.button("Skip question"):
        entry = {
            "question_key": q_key,
            "question": q_obj["question"],
            "answer": "",
            "evaluation_raw": "skipped",
            "evaluation": {"correctness": "skipped", "score": 0, "rationale": "skipped"},
            "timestamp": datetime.utcnow().isoformat()
        }
        st.session_state.transcript.append(entry)
        st.session_state.scores[q_key] = 0
        if idx + 1 >= len(st.session_state.q_order):
            st.session_state.completed = True
        else:
            st.session_state.current_q_idx = idx + 1
        st.rerun()

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
            render_feedback(e["evaluation"], title="Evaluation")

    st.subheader("📝 Constructive Feedback")
    summary_prompt = "You are an expert interviewer. Given these Q&A evaluations, produce 3 short paragraphs: strengths, weaknesses, and recommended next steps.\n\n"
    summary_prompt += json.dumps(st.session_state.transcript, indent=2)

    try:
        resp = client.chat.completions.create(
            model=model_choice,
            messages=[
                {"role": "system", "content": "You are a friendly career coach and Excel expert."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=400,
            temperature=0.2
        )
        st.write(resp.choices[0].message["content"].strip())
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
        st.rerun()
