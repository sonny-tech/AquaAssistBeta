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

DAY_TYPES = [
    "pdf"
    "evaluation",
    "swim"
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

# ------------------ KEYWORD DETECTION ------------------

def detect_keywords(user_input):
    keywords = []
    for stroke in STROKES:
        if stroke in user_input:
            keywords.append(stroke)
    for day in DAY_TYPES:
        if day in user_input:
            keywords.append(day)
    return keywords



# ------------------ HEADER HEURISTIC ------------------

def is_section_header(line):
    line_lower = line.lower()

    has_keyword = (
        any(stroke in line_lower for stroke in STROKES) or
        any(day in line_lower for day in DAY_TYPES)
    )

    has_day_word = "day" in line_lower
    ends_with_colon = line.strip().endswith(":")

    return has_keyword and (has_day_word or ends_with_colon)



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

def find_best_section(sections, requested_keywords):
    if not requested_keywords:
        return None, None

    # 1 Prefer headers that contain ALL requested keywords
    for header, content in sections.items():
        header_lower = header.lower()
        if all(keyword in header_lower for keyword in requested_keywords):
            return header, content

    # 2 Fallback: header containing ANY requested keyword
    for header, content in sections.items():
        header_lower = header.lower()
        if any(keyword in header_lower for keyword in requested_keywords):
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

#-----------------HELPER FUNCTION TO FILTER LINES (removed) -----------------
#def filter_section_content(content, requested_strokes):
   # if not requested_strokes:
   #     return content

    #filtered_lines = []
    #for line in content.split("\n"):
    #    if any(stroke in line.lower() for stroke in requested_strokes):
    #        filtered_lines.append(line)

   # return "\n".join(filtered_lines)
#----------------------------------------------------------------------------
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

    requested_keywords = detect_keywords(normalized)

    with st.chat_message("assistant"):
        if not matched_pdf or not os.path.exists(matched_pdf):
            st.write("Sorry — I couldn’t find a lesson plan for that level.")
            st.write("Available lesson plans:")
            st.write(list(LEVEL_TO_PDF.keys()))
        else:
            if requested_keywords:
                sections = extract_sections_from_pdf(matched_pdf)
                header, content = find_best_section(sections, requested_keywords)


                if content:
                    st.write(f"### {header}")
                    st.text(content)
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