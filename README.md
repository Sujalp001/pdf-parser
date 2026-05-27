PDF Assistant — quick setup

1) Purpose of `.env`
- A `.env` file stores environment variables (like API keys) locally so your code can access them without hardcoding secrets.
- The app looks for `GOOGLE_API_KEY` or `GENAI_API_KEY` to enable AI features.

2) How to use
- Copy `.env.example` to `.env` and replace the placeholder with your key:

  GOOGLE_API_KEY=YOUR_REAL_KEY_HERE

- Restart your terminal or the Streamlit app after editing `.env`.

3) Security note — IMPORTANT
- You pasted an API key into the chat. Treat that key as potentially compromised.
- Revoke or rotate the key from your cloud console immediately and create a new one. Do NOT paste the new key into public chat.

4) Run the app
- Install dependencies and start the app:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

5) Troubleshooting
- If AI stays disabled, confirm `.env` exists, contains `GOOGLE_API_KEY`, and `python-dotenv` is installed.
- You can also paste a session key in the app UI if the app provides it (look for an "AI Key (optional)" box in the sidebar).