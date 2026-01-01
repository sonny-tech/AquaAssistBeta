import base64
import streamlit as st
import os
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

# ------------------ FILE DISCOVERY ------------------

def get_level_to_pdf():
    if not os.path.exists(PDF_DIR):
        return {}

    return {
        os.path.splitext(f)[0].replace("_", " ").lower(): os.path.join(PDF_DIR, f)
        for f in os.listdir(PDF_DIR)
        if f.lower().endswith(".pdf")
    }

# ------------------ STROKE DETECTION ------------------

def detect_strokes(user_input):
    return [stroke for stroke in STROKES if stroke in user_input]


# ------------------ HEADER HEURISTIC ------------------

def is_section_header(line):
    line_lower = line.lower()

    has_stroke = any(stroke in line_lower for stroke in STROKES)
    looks_like_drill = any(
        token in line_lower for token in [" x ", " m", "sec", "meters"]
    )

    return (
        has_stroke
        and not looks_like_drill
        and len(line.strip()) < 80
    )

# ------------------ PDF PARSING ------------------

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

        if not line_clean:
            continue

        if is_section_header(line_clean):
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

def find_best_section(sections, requested_strokes):
    if not requested_strokes:
        return None, None

    # 1 Prefer headers that contain ALL requested strokes
    for header, content in sections.items():
        header_lower = header.lower()
        if all(stroke in header_lower for stroke in requested_strokes):
            return header, content

    # 2 Fallback: header containing ANY requested stroke
    for header, content in sections.items():
        header_lower = header.lower()
        if any(stroke in header_lower for stroke in requested_strokes):
            return header, content

    return None, None

# ------------------ PDF DISPLAY ------------------

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

#-----------------HELPER FUNCTION TO FILTER LINES-----------------
def filter_section_content(content, requested_strokes):
    if not requested_strokes:
        return content

    filtered_lines = []
    for line in content.split("\n"):
        if any(stroke in line.lower() for stroke in requested_strokes):
            filtered_lines.append(line)

    return "\n".join(filtered_lines)

# ------------------ UI ------------------

st.caption("Example: **'Swimmer 6 front crawl'** or **'Junior Masters 1 butterfly'**")

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

    requested_strokes = detect_strokes(normalized)

    with st.chat_message("assistant"):
        if not matched_pdf or not os.path.exists(matched_pdf):
            st.write("Sorry — I couldn’t find a lesson plan for that level.")
            st.write("Available lesson plans:")
            st.write(list(LEVEL_TO_PDF.keys()))
        else:
            if requested_strokes:
                sections = extract_sections_from_pdf(matched_pdf)
                header, content = find_best_section(sections, requested_strokes)

                if content:
                    st.write(f"### {header}")
                    filtered = filter_section_content(content, requested_strokes)

                    if filtered.strip():
                        st.text(filtered)
                    else:
                        st.text(content)  # fallback if filtering removes everything

                else:
                     st.write("That section was not found in this lesson plan.")

            else:
                st.write(f"### {matched_level.title()} — Full Lesson Plan")
                display_pdf(matched_pdf)

                with open(matched_pdf, "rb") as f:
                    st.download_button(
                        "Download PDF",
                        f,
                        file_name=os.path.basename(matched_pdf),
                        mime="application/pdf"
                    )