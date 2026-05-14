import streamlit as st
import pdfplumber
import re
import json
import pandas as pd

def card(title,value,icon):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1e293b, #0f172a);
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 15px;
            border: 1px solid #334155;
            box-shadow: 0 6px 18px rgba(0,0,0,0.25);
            ">
            <h3 style="
            color: white;
            margin: 0 0 10px 0;
            font-size: 20px;
            ">
            {icon} {title}
            </h3>
             <p style="
                color: #e2e8f0;
                font-size: 18px;
                margin: 0;
                line-height: 1.5;
            ">
                {value}
            </p>
            </div>
            """,
            unsafe_allow_html=True
    )
st.set_page_config(
    page_title="PDF Parser",
    page_icon="📄",
    layout="centered"
)
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}

h1, h2, h3, h4, h5, h6, p, label {
    color: white !important;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

div[data-baseweb="select"] {
    background-color: #1e293b;
    border-radius: 10px;
}

.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
}

.stDownloadButton>button {
    background-color: #16a34a;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
}

</style>
""", unsafe_allow_html=True)

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

# st.write("TEXT LENGTH:", len(file_text))
# if file_text:
#     st.text(file_text)
# else:
#     st.warning("No text could be extracted from this PDF.")

file_lower = file_text.lower()
resume_keywords = ["skills", "education", "experience", "project", "resume","certifications"]
bank_keywords = ["account number", "transaction", "account holder", "transaction history", "ifsc", "balance", "debit", "current balance", "credit"]
invoice_keywords = ["invoice", "bill", "gst number", "total amount", "amount", "gst", "total", "payment status"]

if parser_type == "Resume Parser":
    matched_words = [word for word in resume_keywords if word in file_lower]
    if len(matched_words) <= 1:
        st.error("This does not appear to be a resume. Please upload a valid resume PDF.")
        st.stop()
    st.success("✅ Resume Parser selected.")
    
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

    st.subheader("Resume Information")
    card("Name", name, "👤")
    card("Email", email[0] if email else "Not Found", "📧")
    card("Phone", phone[0] if phone else "Not Found", "📱")
    card("Skills", skills, "🛠")
    
    data = {
        "Name": name,
        "Email": email[0] if email else "Not Found",
        "Phone": phone[0] if phone else "Not Found",
        "Skills": skills
    }
    json_data = json.dumps(data, indent=4)
    
    st.download_button(
        label="Download Extracted Data as JSON",
        data=json_data,
        file_name="parsed_data.json",
        mime="application/json"
    )

elif parser_type == "Bank Statement Parser":
    matched_words = [word for word in bank_keywords if word in file_lower]
    if len(matched_words) < 2:
        st.error("This does not appear to be a bank statement. Please upload a valid bank statement PDF.")
        st.stop()
    st.success("✅ Bank Statement Parser selected.")
    st.text(file_text)
    

elif parser_type == "Invoice Parser":
    matched_words = [word for word in invoice_keywords if word in file_lower]
    if len(matched_words) < 2:
        st.error("This does not appear to be an invoice. Please upload a valid invoice PDF.")
        st.stop()
    st.success("✅ Invoice Parser selected.")
    st.text(file_text)
    
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
        card("Name", name, "👤")
        card("Email", email[0] if email else "Not Found", "📧")
    with col2:
        card("Phone", phone[0] if phone else "Not Found", "📱")

    skills = "Not Found"
    if "skills" in file_lower:
        skills_part = file_lower.split("skills", 1)[1]
        if "education" in skills_part:
            skills = skills_part.split("education", 1)[0].strip()
        else:
            skills = skills_part.strip()
    card("Skills", skills, "🛠")

st.sidebar.title("PDF Parser")
st.sidebar.info(
    "Upload any PDF and extract useful text or parser-specific data automatically."
)
