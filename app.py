import streamlit as st
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
import google.generativeai as genai
import re
# Load API Key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Function to get summary from Gemini
def summarize_text(text):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    prompt = f"Summarize this document in under 150 words:\n\n{text[:15000]}"
    response = model.generate_content(prompt)
    return response.text

# Function to answer custom question
def answer_question(text, question):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    prompt = f"""You're a research assistant. Answer the question based only on the document below.

Document:
{text[:15000]}

Question:
{question}

Answer with justification (e.g., 'Based on para 2' or 'page 1'):
"""
    response = model.generate_content(prompt)
    return response.text
def generate_challenge_questions(text):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    prompt = f"""
Generate 3 reasoning or comprehension-based questions from this document with their correct answers.

Format:
Q1: ...
A1: ...
Q2: ...
A2: ...
Q3: ...
A3: ...

Document:
{text[:15000]}
"""
    response = model.generate_content(prompt)
    return response.text
def evaluate_user_answer(text,question,user_answer,correct_answer):
    model=genai.GenerativeModel("gemini-1.5-flash-latest")
    prompt=f"""Document:{text[:15000]}
    Question:{question}
    User's Answer:{user_answer}
    Correct Answer:{correct_answer}
    Tell if the user's answer is correct or not, and justify based on the document. Be specific (e.g.,"Based on paragraph 2..." or "Not mentioned clearly")."""
    response=model.generate_content(prompt)
    return response.text
# Streamlit UI
st.set_page_config(page_title="📄 Smart Research Assistant", layout="centered")
st.title("📄 Smart Research Assistant")

uploaded_file = st.file_uploader("Upload a research document (PDF or TXT)", type=["pdf", "txt"])

if uploaded_file:
    # Extract text
    if uploaded_file.type == "application/pdf":
        doc_text = extract_text_from_pdf(uploaded_file)
    else:
        doc_text = uploaded_file.read().decode("utf-8")

    # Auto Summary
    st.subheader("📌 Auto Summary")
    if st.button("Generate Summary"):
        with st.spinner("Generating summary..."):
            summary = summarize_text(doc_text)
            st.success(summary)

    # Ask Anything
    st.subheader("💬 Ask Anything from Document")
    user_question = st.text_input("Ask a question based on the document:")
    if st.button("Get Answer"):
        if user_question:
            with st.spinner("Generating answer..."):
                answer = answer_question(doc_text, user_question)
                st.info(answer)
        else:
            st.warning("Please enter a question.")
st.subheader("🧠 Challenge Me")

# Button to generate challenge questions
if st.button("Generate Challenge"):
    with st.spinner("Generating challenge questions..."):
        challenge_raw = generate_challenge_questions(doc_text)
        # Extract Qn-An pairs using regex
        qa_pairs = re.findall(r"(Q\d:.*?)\n(A\d:.*?)", challenge_raw, re.DOTALL)
        st.session_state.qa_pairs = qa_pairs

# Show questions 
if "qa_pairs" in st.session_state:
    st.write("### Try answering these:")

    for i, (q, a) in enumerate(st.session_state.qa_pairs):
        st.markdown(f"{q.strip()}")
        user_input = st.text_input(f"Your answer to Q{i+1}", key=f"user_ans_{i}")

        if st.button(f"Check Answer Q{i+1}", key=f"check_btn_{i}"):
            with st.spinner("Evaluating..."):
                feedback = evaluate_user_answer(doc_text, q, user_input, a)
                st.info(feedback)