import streamlit as st
import pdfplumber
import re
import json

st.set_page_config(
    page_title="PDF Parser",
    page_icon="📄",
    layout="centered"
)

parser_type = st.selectbox(
    "Select parser type",
    [
        "Select Option",
        "Normal PDF",
        "Resume Parser",
        "Bank Statement Parser",
        "Invoice Parser"
    ]
)

if parser_type == "Select Option":
    st.warning("Please choose a parser type.")
    st.stop()

st.title("PDF Text Extractor")

upload_file = st.file_uploader("Upload file:", type=["pdf"])
if not upload_file:
    st.stop()

file_text = ""
try:
    with pdfplumber.open(upload_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                file_text += page_text
except Exception as exc:
    st.error(f"Error reading PDF: {exc}")
    st.stop()

st.write("TEXT LENGTH:", len(file_text))
if file_text:
    st.text(file_text)
else:
    st.warning("No text could be extracted from this PDF.")

file_lower = file_text.lower()
resume_keywords = ["skills", "education", "experience", "project", "resume"]
bank_keywords = ["account number", "transaction", "balance", "debit", "credit"]
invoice_keywords = ["invoice", "bill", "amount", "gst", "total"]

if parser_type == "Resume Parser":
    email = re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        file_text
    )
    phone = re.findall(r"\d{10}", file_text)

    name = "Not Found"
    if "name" in file_lower:
        name_part = re.split(r"(?i)name[:\s]*", file_text, maxsplit=1)
        if len(name_part) > 1:
            name = name_part[1].split("\n")[0].strip()

    skills = "Not Found"
    if "skills" in file_lower:
        skills_part = file_text.lower().split("skills", 1)[1]
        if "education" in skills_part:
            skills = skills_part.split("education", 1)[0].strip()
        else:
            skills = skills_part.strip()

    # st.subheader("Resume Information")
    # st.info(f"👤 Name: {name}")
    # st.info(f"📧 Email: {email[0] if email else 'Not Found'}")
    # st.info(f"📱 Phone: {phone[0] if phone else 'Not Found'}")
    # st.info(f"🛠 Skills: {skills}")

    if not any(word in file_lower for word in resume_keywords):
        st.error("This does not appear to be a resume. Please upload a valid resume PDF.")
        st.stop()

elif parser_type == "Bank Statement Parser":
    if not any(word in file_lower for word in bank_keywords):
        st.error("This does not appear to be a bank statement. Please upload a valid bank statement PDF.")
        st.stop()
    st.success("✅ Bank Statement Parser selected.")

elif parser_type == "Invoice Parser":
    if not any(word in file_lower for word in invoice_keywords):
        st.error("This does not appear to be an invoice. Please upload a valid invoice PDF.")
        st.stop()
    st.success("✅ Invoice Parser selected.")

elif parser_type == "Normal PDF":
    st.success("✅ Normal PDF selected.")

    email = re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        file_text
    )
    phone = re.findall(r"\d{10}", file_text)

    name = "Not Found"
    if "name" in file_lower:
        name_part = re.split(r"(?i)name[:\s]*", file_text, maxsplit=1)
        if len(name_part) > 1:
            name = name_part[1].split("\n")[0].strip()

    st.subheader("Extracted Information")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Name: {name}")
    with col2:
        st.info(f"Phone: {phone[0] if phone else 'Not Found'}")

    st.info(f"Email: {email[0] if email else 'Not Found'}")

    skills = "Not Found"
    if "skills" in file_lower:
        skills_part = file_lower.split("skills", 1)[1]
        if "education" in skills_part:
            skills = skills_part.split("education", 1)[0].strip()
        else:
            skills = skills_part.strip()
    st.info(f"🛠 Skills: {skills}")

    data = {
        "Name": name,
        "Email": email[0] if email else "Not Found",
        "Phone": phone[0] if phone else "Not Found"
    }
    json_data = json.dumps(data, indent=4)
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name="parsed_data.json",
        mime="application/json"
    )

st.sidebar.title("PDF Parser")
st.sidebar.info(
    "Upload any PDF and extract useful text or parser-specific data automatically."
)
