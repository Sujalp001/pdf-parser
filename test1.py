import os
import sys
from google import genai
import pdfplumber


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from all pages of a PDF file."""
    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
            else:
                text_chunks.append(f"[Page {i} contains no extractable text]")
    return "\n\n".join(text_chunks)


def make_gemini_client() -> genai.Client:
    api_key = os.environ.get("GENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Please set the GENAI_API_KEY environment variable before running this script."
        )
    return genai.Client(api_key=api_key)


def summarize_pdf(pdf_path: str, prompt: str) -> str:
    client = make_gemini_client()
    pdf_text = extract_pdf_text(pdf_path)
    if not pdf_text.strip():
        return "No text was extracted from the PDF."

    request_text = (
        "I have extracted text from a PDF document. "
        "Please answer the question below based on that text.\n\n"
        f"Question: {prompt}\n\n"
        "PDF text:\n"
        f"{pdf_text}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=request_text,
    )
    return response.text


def print_usage() -> None:
    print("Usage: python test1.py <path-to-pdf> [question]")
    print("Example: python test1.py sample.pdf \"Summarize the key points of this PDF.\"")


def main() -> None:
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    prompt = (
        sys.argv[2] if len(sys.argv) > 2 else "Summarize the key points of this PDF document."
    )

    print(f"Extracting text from: {pdf_path}")
    summary = summarize_pdf(pdf_path, prompt)
    print("\n=== Gemini Response ===\n")
    print(summary)


if __name__ == "__main__":
    main()
