import base64
import streamlit as st
import os

st.set_page_config(page_title="Lesson Plan Library", layout="centered")
st.title("AquaAssist Beta")

PDF_DIR = "pdfs"

def get_level_to_pdf():
    if not os.path.exists(PDF_DIR):
        return {}

    return {
        os.path.splitext(f)[0].replace("_", " ").lower(): os.path.join(PDF_DIR, f)
        for f in os.listdir(PDF_DIR)
        if f.lower().endswith(".pdf")
    }


def display_pdf(path):
    with open(path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
        f'width="100%" height="600" style="border:none;"></iframe>',
        unsafe_allow_html=True
    )

user_input = st.chat_input("Ask for a lesson plan")

if user_input:
    normalized = user_input.lower()
    LEVEL_TO_PDF = get_level_to_pdf()

    matched_pdf = None
    for level, path in LEVEL_TO_PDF.items():
        if level in normalized:
            matched_pdf = path
            break

    with st.chat_message("assistant"):
        if matched_pdf and os.path.exists(matched_pdf):
            st.write("Here is the lesson plan you requested:")
            display_pdf(matched_pdf)

            with open(matched_pdf, "rb") as f:
                st.download_button(
                    "Download PDF",
                    f,
                    file_name=os.path.basename(matched_pdf),
                    mime="application/pdf"
                )
        else:
            st.write("Sorry — I couldn’t find a lesson plan for that level.")
