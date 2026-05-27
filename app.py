import io
import json
import re
from typing import Dict, List

import pdfplumber
import streamlit as st

DOC_KEYWORDS = {
    "Resume": [
        "skills",
        "education",
        "experience",
        "certifications",
        "resume",
        "projects",
        "objective",
        "summary",
    ],
    "Invoice": [
        "invoice",
        "bill",
        "total amount",
        "gst",
        "tax",
        "payment",
        "due date",
        "subtotal",
    ],
    "Bank Statement": [
        "account number",
        "transaction",
        "balance",
        "statement",
        "debit",
        "credit",
        "opening balance",
        "closing balance",
    ],
}


def extract_pdf_text(uploaded_file) -> str:
    pdf_bytes = uploaded_file.read()
    text_chunks: List[str] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_chunks.append(page_text)
                else:
                    text_chunks.append(f"[Page {page_number} contains no extractable text]")
    except Exception as exc:
        st.error(f"Unable to read the PDF file: {exc}")
    return "\n\n".join(text_chunks), pdf_bytes


# Advanced detection helpers
UNIQUE_PATTERNS = {
    "Invoice": [
        r"invoice\s*no[:\-]?\s*\S+",
        r"total\s*amount",
        r"gst\b",
        r"invoice\b",
    ],
    "Bank Statement": [
        r"account\s*number",
        r"ifsc\b",
        r"statement\b",
        r"debit\b",
        r"credit\b",
    ],
    "Resume": [
        r"experience\b",
        r"education\b",
        r"skills\b",
        r"certifications?\b",
        r"\bresume\b",
    ],
}


def detect_document_type_advanced(text: str, pdf_bytes: bytes) -> str:
    """Use keyword counts, regex patterns and table heuristics to pick a document type."""
    text_lower = text.lower()
    # 1) basic keyword scoring
    keyword_scores = {name: 0 for name in DOC_KEYWORDS}
    for name, keywords in DOC_KEYWORDS.items():
        for k in keywords:
            if k in text_lower:
                keyword_scores[name] += 1

    # 2) unique regex boosts
    import collections

    regex_scores = collections.Counter()
    for name, patterns in UNIQUE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                regex_scores[name] += 2

    # 3) numeric/table heuristics (invoices and bank statements often contain tables)
    table_score = {"Invoice": 0, "Bank Statement": 0, "Resume": 0}
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            table_count = 0
            numeric_table_count = 0
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for table in tables:
                    table_count += 1
                    # count numeric cells in table
                    numeric = 0
                    cells = sum(1 for row in table for cell in (row or []) if cell)
                    for row in table:
                        for cell in (row or []):
                            if cell and re.search(r"\d", str(cell)):
                                numeric += 1
                    if cells > 0 and numeric / max(1, cells) > 0.25:
                        numeric_table_count += 1
            if numeric_table_count >= 1:
                table_score["Invoice"] += 2
                table_score["Bank Statement"] += 2
    except Exception:
        pass

    # 4) currency presence indicates invoice/bank
    currency_hits = 0
    for cur in [r"\$", "₹", "€", "rs ", "usd", "inr"]:
        if cur in text_lower:
            currency_hits += 1
    if currency_hits:
        table_score["Invoice"] += 1
        table_score["Bank Statement"] += 1

    # 5) email/phone hints make it a resume
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        keyword_scores["Resume"] += 1
    if re.search(r"\+?\d[\d \-.]{7,}\d", text):
        keyword_scores["Resume"] += 1

    # Combine weighted scores
    combined = {}
    for name in DOC_KEYWORDS.keys():
        combined[name] = keyword_scores.get(name, 0) + regex_scores.get(name, 0) + table_score.get(name, 0)

    # choose best
    best = max(combined, key=combined.get)
    if combined[best] == 0:
        return "General PDF"
    return best


def detect_document_type(text: str) -> str:
    lower_text = text.lower()
    scoring = {name: sum(1 for keyword in keywords if keyword in lower_text) for name, keywords in DOC_KEYWORDS.items()}
    best_type = max(scoring, key=scoring.get)
    return best_type if scoring[best_type] > 0 else "General PDF"


def summarize_text(text: str, sentence_limit: int = 4) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= sentence_limit:
        return text.strip()
    return " ".join(sentences[:sentence_limit]).strip() + " ..."


def answer_question(text: str, question: str) -> str:
    if not question.strip():
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    words = [w for w in re.findall(r"\w+", question.lower()) if len(w) > 2]
    if not words:
        return "Ask a more specific question."
    scored = []
    for sentence in sentences:
        score = sum(1 for word in words if word in sentence.lower())
        if score > 0:
            scored.append((score, sentence.strip()))
    if not scored:
        return "No clear answer found in the extracted text. Try a different question."
    scored.sort(reverse=True, key=lambda item: item[0])
    return " ".join(sentence for _, sentence in scored[:3])


def find_first_pattern(text: str, patterns: List[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1):
            return match.group(1).strip()
    return ""


def handle_simple_question(question: str, metadata: Dict[str, int]) -> str:
    q = question.lower().strip()
    # word count
    if "word count" in q or ("words" in q and "count" in q):
        return str(metadata.get("word_count", ""))
    # text length / characters
    if "text length" in q or "characters" in q or "length" in q:
        return str(metadata.get("text_length", ""))
    # document type
    if "document type" in q or "detected type" in q or q == "type":
        return metadata.get("document_type", "") or ""
    return ""


def extract_specific_answer(question: str, text: str, sentence: str) -> str:
    q = question.lower()
    patterns = {
        "invoice date": [r"date[:\-]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})", r"invoice date[:\-]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})"],
        "total amount": [r"total\s*amount[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)", r"amount[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)"],
        "amount": [r"([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)"],
        "account number": [r"account\s*number[:\-]?\s*(\S+)", r"a/c\s*no[:\-]?\s*(\S+)"],
        "ifsc": [r"ifsc\s*code[:\-]?\s*(\S+)", r"ifsc[:\-]?\s*(\S+)"] ,
        "current balance": [r"current\s*balance[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)"],
        "balance": [r"balance[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)"],
        "email": [r"([\w.+-]+@[\w-]+\.[\w.-]+)"],
        "phone": [r"(\+?\d[\d \-.]{7,}\d)"],
    }
    for key, pat_list in patterns.items():
        if key in q:
            for pat in pat_list:
                for source in (sentence, text):
                    match = re.search(pat, source, re.IGNORECASE)
                    if match and match.group(1):
                        return match.group(1).strip()
    return ""


def extract_fields(text: str, doc_type: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    if doc_type == "Invoice":
        fields["Invoice number"] = find_first_pattern(text, [r"invoice\s*no[:\-]?\s*(\S+)", r"inv(?:oice)?\s*#?\s*(\S+)"])
        fields["Invoice date"] = find_first_pattern(text, [r"date[:\-]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})", r"date[:\-]?\s*([A-Za-z0-9 ,]+)"])
        fields["Total amount"] = find_first_pattern(text, [r"total\s*amount[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)", r"amount[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)"])
    elif doc_type == "Bank Statement":
        fields["Account number"] = find_first_pattern(text, [r"account\s*number[:\-]?\s*(\S+)", r"a/c\s*no[:\-]?\s*(\S+)"])
        fields["Opening balance"] = find_first_pattern(text, [r"opening\s*balance[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)"])
        fields["Closing balance"] = find_first_pattern(text, [r"closing\s*balance[:\-]?\s*([\$₹€]?\s?[0-9,]+(?:\.[0-9]{2})?)"])
        fields["Statement period"] = find_first_pattern(text, [r"period[:\-]?\s*([A-Za-z0-9 ,\-]+)"])
    elif doc_type == "Resume":
        fields["Email"] = find_first_pattern(text, [r"([\w.+-]+@[\w-]+\.[\w.-]+)"])
        fields["Phone"] = find_first_pattern(text, [r"(\+?\d[\d \-.]{7,}\d)"])
        fields["Top skills"] = find_first_pattern(text, [r"skills[:\-]?\s*([A-Za-z0-9, ]+)"])
    return {key: value for key, value in fields.items() if value}


def make_analysis_payload(text: str, doc_type: str, summary: str, answer: str, fields: Dict[str, str]) -> Dict[str, str]:
    return {
        "document_type": doc_type,
        "summary": summary,
        "answer": answer,
        "fields": fields,
        "text_length": len(text),
    }


def main() -> None:
    st.set_page_config(page_title="PDF Assistant", page_icon="📄", layout="wide")
    st.sidebar.title("PDF Assistant")
    st.sidebar.write("Upload a PDF and get fast extraction, type detection, and downloads.")
    st.sidebar.markdown("---")
    st.sidebar.write("If you want, choose a parser type or keep auto-detect.")

    parser_options = ["Auto detect", "General PDF", "Resume", "Invoice", "Bank Statement"]

    def lock_parser_mode() -> None:
        st.session_state.parser_mode_locked = True

    def unlock_parser_mode() -> None:
        st.session_state.parser_mode_locked = False

    if "parser_mode" not in st.session_state:
        st.session_state.parser_mode = "Auto detect"

    if "parser_mode_locked" not in st.session_state or not st.session_state.parser_mode_locked:
        parser_mode = st.sidebar.radio(
            "Parser mode",
            parser_options,
            index=parser_options.index(st.session_state.parser_mode),
            key="parser_mode",
            on_change=lock_parser_mode,
        )
    else:
        parser_mode = st.session_state.parser_mode
        st.sidebar.write("Parser mode")
        st.sidebar.success(parser_mode)
        st.sidebar.button("Change parser mode", on_click=unlock_parser_mode)

    st.title("PDF Assistant")
    st.write("Extract text from a PDF, detect the document type, summarize it, and download results.")

    upload_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if not upload_file:
        st.info("Please upload a PDF file to continue.")
        return

    file_text, pdf_bytes = extract_pdf_text(upload_file)
    if not file_text.strip():
        st.error("No text could be extracted from this PDF. Try another file.")
        return

    detected_type = detect_document_type_advanced(file_text, pdf_bytes)
    if parser_mode == "Auto detect":
        document_type = detected_type
        st.info(f"Auto-detected type: {detected_type}")
    else:
        document_type = parser_mode
        if detected_type != parser_mode:
            st.warning(
                f"Selected parser mode is '{parser_mode}', but the uploaded file looks like '{detected_type}'.\n"
                "Please confirm the parser mode or choose Auto detect."
            )

    summary = summarize_text(file_text, sentence_limit=4)
    question = st.text_input("Ask a question about this document", placeholder="Example: What is the total amount?")
    answer_placeholder = st.empty()
    answer = ""
    if question.strip():
        # replicate the local matching steps for answer extraction
        sentences = re.split(r'(?<=[.!?])\s+', file_text)
        words = [w for w in re.findall(r"\w+", question.lower()) if len(w) > 2]
        scored = []
        for sentence in sentences:
            score = sum(1 for word in words if word in sentence.lower())
            if score > 0:
                scored.append((score, sentence.strip()))
        scored.sort(reverse=True, key=lambda item: item[0])

        meta = {"word_count": len(file_text.split()), "text_length": len(file_text), "document_type": document_type}
        simple_answer = handle_simple_question(question, meta)
        if simple_answer:
            answer = simple_answer
        else:
            answer = answer_question(file_text, question)
            specific = extract_specific_answer(question, file_text, scored[0][1] if scored else file_text)
            if specific:
                answer = specific

        answer_placeholder.subheader("Answer")
        answer_placeholder.write(answer)

    fields = extract_fields(file_text, document_type)
    results = make_analysis_payload(file_text, document_type, summary, answer, fields)
    json_results = json.dumps(results, ensure_ascii=False, indent=2)
    

    with st.expander("Show full extracted text", expanded=False):
        st.text_area("Extracted text", file_text, height=360)

    st.download_button(
        "Download extracted text",
        file_text,
        file_name="extracted_text.txt",
        mime="text/plain",
    )
    st.download_button(
        "Download analysis JSON",
        json_results,
        file_name="pdf_analysis.json",
        mime="application/json",
    )

    # Document details moved to bottom as requested
    st.subheader("Document details")
    st.markdown(f"**Detected type:** {document_type}")
    st.markdown(f"**Text length:** {len(file_text)} characters")
    st.markdown(f"**Word count:** {len(file_text.split())}")

    if fields:
        st.subheader("Extracted fields")
        for key, value in fields.items():
            st.markdown(f"- **{key}:** {value}")


if __name__ == "__main__":
    main()
