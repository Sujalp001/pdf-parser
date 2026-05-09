import streamlit as st
import pdfplumber
import re
import json

st.set_page_config(
    page_title="PDF Parser",
    page_icon="📄",
    layout="centered"
)
st.title("Pdf Text Extractor")

upload_file = st.file_uploader("uploaded file :", type=["pdf"])

if upload_file:

    file = ""

    try:
        with pdfplumber.open(upload_file) as pdf:

            for page in pdf.pages:

                text = page.extract_text()

                if text:
                    file += text
    except Exception:
        st.error("Error Reading PDF")
    else:
        # st.subheader("pdf text")
        # st.text(file)

        # ---------------- EMAIL ----------------

        email = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            file
        )

        # ---------------- PHONE ----------------

        phone = re.findall(r"\d{10}", file)

        # ---------------- NAME ----------------

        name = "Not Found"

        if "Name" in file:
            name = file.split("Name")[1].split("\n")[0].strip()

        # ---------------- OUTPUT ----------------

        st.subheader("Extracted Information")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f" name : {name}")

        with col2:
            st.info(f"phone: {phone[0] if phone else 'not found'}")

        st.info(f"email :{email[0] if email else 'not found'}")
        data = {
            "Name": name,
            "Email": email[0] if email else "Not Found",
            "Phone": phone[0] if phone else "Not Found"
        }
        skills ="not found"
        if skills in file:
            skills =file.split("skills")[1].split("Education")[0].strip()
        
        st.info(f"🛠 Skills : {skills}")
        st.json(data)

        json_data = json.dumps(data, indent=4)

        st.download_button(
            label="Download json",
            data=json_data,
            file_name="parsed_data.json",
            mime="application/json"
        )

st.sidebar.title("pdf parser")

st.sidebar.info(
    "upload any resume pdf and extraxt information automatically"
)
