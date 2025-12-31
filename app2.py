import base64
import streamlit as st
import os
import re
import pdfplumber

# ------------------ CONFIG ------------------

st.set_page_config(page_title="Lesson Plan Library", layout="centered")
st.title("AquaAssist Beta")

PDF_DIR = "pdfs"

STROKES = [
    "front crawl",
    "back crawl",
    "breaststroke",
    "butterfly"
]

# ------------------ HELPERS ------------------

def get_level_to_pdf():
    if not os.path.exists(PDF_DIR):
        return {}

    return {
        os.path.splitext(f)[0].replace("_", " ").lower(): os.path.join(PDF_DIR, f)
        for f in os.listdir(PDF_DIR)
        if f.lower().endswith(".pdf")
    }


def detect_stroke(user_input):
    for stroke in STROKES:
        if stroke in user_input:
            return stroke
    return None


def extract_sections_from_pdf(pdf_path):
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += "\n" + text

    text_lower = full_text.lower()

    matches = []
    for stroke in STROKES:
        for m in re.finditer(rf"\b{stroke}\b", text_lower):
            matches.append((m.start(), stroke))

    if not matches:
        return {}

    matches.sort(key=lambda x: x[0])

    sections = {}
    for i, (start_idx, stroke) in enumerate(matches):
        end_idx = matches[i + 1][0] if i + 1 < len(matches) else len(full_text)
        sections[stroke] = full_text[start_idx:end_idx].strip()

    return sections


def display_pdf(path):
    with open(path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="600"
            style="border:none;">
        </iframe>
        """,
        unsafe_allow_html=True
    )

# ------------------ UI ------------------

st.caption("Ask for a lesson plan. Example: **'Swimmer 6 front crawl'**")

user_input = st.chat_input("Ask for a lesson plan")

if user_input:
    normalized = user_input.lower()
    LEVEL_TO_PDF = get_level_to_pdf()

    matched_pdf = None
    matched_level = None

    for level, path in LEVEL_TO_PDF.items():
        if level in normalized:
            matched_pdf = path
            matched_level = level
            break

    stroke = detect_stroke(normalized)

    with st.chat_message("assistant"):
        if not matched_pdf or not os.path.exists(matched_pdf):
            st.write("Sorry — I couldn’t find a lesson plan for that level.")
            st.write("Available lesson plans:")
            st.write(list(LEVEL_TO_PDF.keys()))
        else:
            # Stroke-specific request
            if stroke:
                sections = extract_sections_from_pdf(matched_pdf)

                if stroke in sections:
                    st.write(f"### {matched_level.title()} — {stroke.title()}")
                    st.text(sections[stroke])
                else:
                    st.write("That stroke section was not found in this lesson plan.")
            else:
                # Full PDF
                st.write(f"### {matched_level.title()} — Full Lesson Plan")
                display_pdf(matched_pdf)

                with open(matched_pdf, "rb") as f:
                    st.download_button(
                        "Download PDF",
                        f,
                        file_name=os.path.basename(matched_pdf),
                        mime="application/pdf"
                    )
