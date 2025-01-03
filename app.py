import os
import streamlit as st
from smolagents import tool, CodeAgent, HfApiModel
import pdfplumber
from uuid import uuid4


def parse_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file.

    Args:
        file_path: Path to the PDF file.
        
    Returns:
        Extracted text from the PDF.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

"""
Not really a tool tho
"""
@tool
def get_text() -> str:
    """
    Returns:
        Extracted text from the PDF.
    """
    return st.session_state.get("pdf_text", "")


if "reasoning_in_progress" not in st.session_state:
    st.session_state.reasoning_in_progress = False
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""


st.title("Interactive PDF Query Tool")


input_mode = st.radio(
    "Choose your input mode:", 
    ["Upload a PDF", "Write Text Directly"], 
    disabled=st.session_state.reasoning_in_progress
)

if input_mode == "Upload a PDF":
    uploaded_file = st.file_uploader(
        "Upload a PDF file", 
        type="pdf", 
        disabled=st.session_state.reasoning_in_progress
    )

    if uploaded_file:
        uploads_dir = "./uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        unique_filename = f"{uuid4()}_{uploaded_file.name}"
        file_path = os.path.join(uploads_dir, unique_filename)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        st.session_state.pdf_text = parse_pdf(file_path)

        os.remove(file_path)

        st.subheader("Extracted Text from PDF")
        st.text_area("PDF Content", st.session_state.pdf_text, height=300, disabled=True)
elif input_mode == "Write Text Directly":
    st.session_state.pdf_text = st.text_area(
        "Write or Paste Your Text Here", 
        height=300, 
        disabled=st.session_state.reasoning_in_progress
    )

st.subheader("Ask a Question")
question = st.text_input(
    "Enter your question:", 
    disabled=st.session_state.reasoning_in_progress
)

max_iterations = st.number_input(
    "Select the number of reasoning steps (max_iterations):",
    min_value=1,
    max_value=10,
    value=3,
    disabled=st.session_state.reasoning_in_progress
)

if st.button("Get Answer", disabled=st.session_state.reasoning_in_progress):
    if not question.strip():
        st.error("Please enter a valid question.")
    elif not st.session_state.pdf_text.strip():
        st.error("Please provide text content (via PDF or direct input).")
    else:
        st.session_state.reasoning_in_progress = True  
        with st.spinner("Reasoning in progress..."):
            agent = CodeAgent(
                tools=[get_text],
                model=HfApiModel(),
                max_iterations=max_iterations,
            )
            answer = agent.run(question)

        st.session_state.reasoning_in_progress = False 
        st.success(f"Answer: {answer}")
