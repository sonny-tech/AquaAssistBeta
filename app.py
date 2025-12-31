import base64
import streamlit as st
import os
import re
import pdfplumber

# ------------------ CONFIG ------------------

st.set_page_config(page_title="Lesson Plan Library", layout="centered")
st.title("AquaAssist Alpha")

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
    with pdfplumber.open(pdf_path) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))

    sections = {}
    current_header = None
    current_content = []

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        # Heuristic: section headers
        is_header = (
            any(stroke in line_lower for stroke in STROKES)
            and (line_lower.endswith(":") or "day" in line_lower)
            and len(line_clean) < 60
        )

        if is_header:
            if current_header:
                sections[current_header] = "\n".join(current_content).strip()
            current_header = line_clean
            current_content = []
        else:
            if current_header:
                current_content.append(line_clean)

    if current_header:
        sections[current_header] = "\n".join(current_content).strip()

    return sections

def find_section_for_stroke(sections, stroke):
    for header, content in sections.items():
        if stroke in header.lower():
            return header, content
    return None, None

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
                header, content = find_section_for_stroke(sections, stroke)

                if content:
                    st.write(f"### {header}")
                    st.text(content)
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
