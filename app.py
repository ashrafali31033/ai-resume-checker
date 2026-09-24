import os

import fitz
import streamlit as st
from dotenv import load_dotenv
from google import genai


# ==========================================
# CONFIGURATION
# ==========================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY is missing from your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.1-flash-lite"


# ==========================================
# PAGE
# ==========================================

st.set_page_config(
    page_title="ResumeAI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 ResumeAI")
st.write(
    "AI-powered Resume Analyzer, Job Matcher and Chatbot"
)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.header("📄 Upload Resume")

    resume_file = st.file_uploader(
        "Upload your resume",
        type=["pdf"]
    )

    if resume_file:
        st.success("Resume uploaded!")


# ==========================================
# EXTRACT RESUME
# ==========================================

resume_text = ""

if resume_file:

    try:

        pdf = fitz.open(
            stream=resume_file.read(),
            filetype="pdf"
        )

        for page in pdf:
            resume_text += page.get_text() + "\n"

        pdf.close()

    except Exception as e:

        st.error(
            "Could not read the PDF: " + str(e)
        )
        st.stop()


# ==========================================
# MAIN APPLICATION
# ==========================================

if not resume_text.strip():

    st.info(
        "👈 Upload your PDF resume from the sidebar."
    )

    st.markdown("""
    ### What you can do

    📊 Analyze your resume

    💼 Compare your resume with a job description

    💬 Chat with your resume
    """)

    st.stop()


# ==========================================
# TABS
# ==========================================

tab1, tab2, tab3 = st.tabs([
    "📊 Resume Analysis",
    "💼 Job Match",
    "💬 Chatbot"
])


# ==========================================
# TAB 1 - RESUME ANALYSIS
# ==========================================

def extract_pdf_text(uploaded_pdf) -> str:
    """Extract plain text from an uploaded PDF file (Streamlit UploadedFile)."""
    text = ""
    pdf_bytes = uploaded_pdf.read()
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in pdf:
        page_text = page.get_text()
        if page_text:
            text += page_text + "\n"
    pdf.close()
    return text.strip()
jd_input_mode = st.radio(
    "How do you want to provide the job description?",
    ["📄 Upload JD PDF", "📝 Paste JD Text"],
    horizontal=True,
    key="jd_input_mode",
)

job_description = ""

if jd_input_mode == "📄 Upload JD PDF":

    jd_file = st.file_uploader(
        "Upload the job description PDF",
        type=["pdf"],
        key="jd_file_uploader",
    )

    if jd_file:
        try:
            job_description = extract_pdf_text(jd_file)

            if not job_description.strip():
                st.error(
                    "Could not extract text from this PDF. "
                    "Please upload a text-based PDF, or paste the JD text instead."
                )
            else:
                st.success("✅ Job description PDF uploaded successfully!")
                st.write(f"Characters extracted: {len(job_description)}")

                with st.expander("Preview extracted JD text"):
                    st.text(job_description[:3000])

        except Exception as e:
            st.error(f"Error reading the JD PDF: {str(e)}")

else:
    job_description = st.text_area(
        "📋 Paste Job Description",
        height=300,
        key="job_description_text",
    )

with tab1:

    st.header("📊 Resume Analysis")

    if st.button(
        "🤖 Analyze Resume",
        key="analyze"
    ):

        prompt = f"""
You are an AI resume analyzer.

Analyze the resume below.

IMPORTANT:
Only use information that actually appears
in the resume. Do not invent skills,
experience, achievements, companies,
education, or numbers.

Give your answer using these sections:

## Overall Assessment

## Skills Found

## Strengths

## Areas to Improve

## Missing or Unclear Information

## 5 Practical Suggestions

RESUME:

{resume_text}
"""

        try:

            with st.spinner(
                "🤖 Analyzing resume..."
            ):

                result = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )

            st.session_state["analysis"] = result.text

        except Exception as e:

            st.error(
                "Gemini error: " + str(e)
            )


    if "analysis" in st.session_state:

        st.markdown(
            st.session_state["analysis"]
        )


# ==========================================
# TAB 2 - JOB MATCH
# ==========================================

with tab2:

    st.header("💼 Compare Resume With Job")

    st.write(
        "Paste the job description below."
    )

    job_description = st.text_area(
        "Job Description",
        height=300,
        placeholder=(
            "Paste the complete job description here..."
        )
    )

    if st.button(
        "🔍 Compare Resume With Job",
        key="compare"
    ):

        if not job_description.strip():

            st.warning(
                "Please paste a job description first."
            )

        else:

            prompt = f"""
You are an AI resume and job matching assistant.

Compare the resume with the job description.

IMPORTANT:
Do not invent information.

Only say a skill is present if it is
actually supported by the resume.

RESUME:

{resume_text}

JOB DESCRIPTION:

{job_description}

Give the result using these sections:

## Matching Skills

Skills appearing in both the resume
and job description.

## Required Skills Found

Important job requirements that are
supported by the resume.

## Skills Not Clearly Present

Important job requirements that are
not clearly demonstrated by the resume.

## Relevant Experience

Explain which experience or projects
are relevant.

## Improvement Suggestions

Give practical suggestions for improving
the resume for this job.

Do not invent experience or qualifications.
"""

            try:

                with st.spinner(
                    "🤖 Comparing resume and job..."
                ):

                    result = client.models.generate_content(
                        model=MODEL,
                        contents=prompt
                    )

                st.markdown(result.text)

            except Exception as e:

                st.error(
                    "Gemini error: " + str(e)
                )


# ==========================================
# TAB 3 - CHATBOT
# ==========================================

with tab3:

    st.header("💬 Resume Chatbot")

    st.write(
        "Ask questions about your resume."
    )

    # Create chat history
    if "chat_history" not in st.session_state:

        st.session_state["chat_history"] = []


    # Display old messages
    for message in st.session_state["chat_history"]:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )


    # Chat input
    question = st.chat_input(
        "Ask about your resume..."
    )


    if question:

        # Display user question
        with st.chat_message("user"):

            st.write(question)


        # Save user question
        st.session_state["chat_history"].append(
            {
                "role": "user",
                "content": question
            }
        )


        prompt = f"""
You are ResumeAI, a helpful resume assistant.

Answer the user's question using the
resume below.

IMPORTANT RULES:

- Do not invent information.
- Do not invent skills.
- Do not invent experience.
- Do not invent companies.
- Do not invent achievements.
- Do not invent numbers.

If the answer cannot be found in the
resume, say that the information is
not available in the resume.

RESUME:

{resume_text}

USER QUESTION:

{question}
"""

        try:

            with st.chat_message("assistant"):

                with st.spinner(
                    "🤖 Thinking..."
                ):

                    result = client.models.generate_content(
                        model=MODEL,
                        contents=prompt
                    )

                st.write(result.text)


            # Save answer
            st.session_state["chat_history"].append(
                {
                    "role": "assistant",
                    "content": result.text
                }
            )

        except Exception as e:

            st.error(
                "Gemini error: " + str(e)
            )