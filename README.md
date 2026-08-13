# DadMumBot - Streamlit Community Cloud

This version fixes the retrieval issue in the earlier prototype package. The app now:

- fetches an allowlisted set of Singapore Government, public hospital and private healthcare pregnancy sources;
- chunks and retrieves source material using OpenAI embeddings with a lexical fallback;
- passes only the most relevant approved excerpts to `gpt-4o-mini`;
- keeps `temperature=0.2` and a 550-token output cap;
- keeps the OpenAI key and authentication secrets in Streamlit Secrets;
- shows retrieval status in the UI for easier diagnosis.

## Streamlit Community Cloud
1. Upload these files to GitHub.
2. Deploy `app.py` from Streamlit Community Cloud.
3. Add your existing authentication secrets and OpenAI key under App settings -> Secrets.
4. Do not commit the real API key or password.

## Required secrets
```toml
APP_USERNAME = "dadmumbot"
APP_PASSWORD_SALT = "<your-salt>"
APP_PASSWORD_HASH = "<your-pbkdf2-hash>"
APP_PASSWORD_ITERATIONS = 310000
OPENAI_API_KEY = "<your-real-key>"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_OUTPUT_TOKENS = 550
OPENAI_TEMPERATURE = 0.2
```

## Important
The medical-information knowledge base is restricted to the URLs in `data/approved_sources.json`. If a source page cannot be fetched, the app records a warning and does not invent content.


## Prenatal schedule

The app includes a user-triggered prenatal check schedule based only on curated approved Singapore healthcare sources. For IVF, the EDD must be later than the FET date.
