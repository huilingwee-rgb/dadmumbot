# DadMumBot - Streamlit Community Cloud package

## Stack
- Python
- Streamlit
- OpenAI `gpt-4o-mini`
- Singapore-only RAG (to be connected before real medical-information use)

## Security changes in this version
- Password gate before application functions
- Login attempt throttling
- Global application error boundary with generic user-facing messages
- Server-side OpenAI API key and password hash via Streamlit Secrets
- Prompt-injection detection, input limits and request rate limiting

## OpenAI settings
- Model: `gpt-4o-mini`
- Temperature: `0.2`
- Maximum output tokens: `550`

## Temporary credentials
The login credential is supplied separately with the deployment instructions. The plaintext password is intentionally not stored in this repository or ZIP package.

## Streamlit Community Cloud deployment
Streamlit Community Cloud deploys from GitHub and supports secrets through the app's Advanced settings. Official workflow: connect GitHub, create an app, select repository/branch/`app.py`, open Advanced settings, paste the Secrets block, then deploy.

### Secrets to paste into Community Cloud
```toml
APP_USERNAME = "<your username>"
APP_PASSWORD_SALT = "<salt hex>"
APP_PASSWORD_HASH = "<PBKDF2 hash hex>"
APP_PASSWORD_ITERATIONS = 310000
OPENAI_API_KEY = "<YOUR_REAL_OPENAI_API_KEY>"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_OUTPUT_TOKENS = 550
OPENAI_TEMPERATURE = 0.2
```

Do not commit real secrets. Streamlit explicitly recommends keeping secrets outside the Git repository.

## Deployment steps
1. Create or use a GitHub repository.
2. Upload the package files.
3. Go to https://share.streamlit.io/ and sign in with GitHub.
4. Click **Create app**.
5. Choose repository, branch and `app.py`.
6. Open **Advanced settings** and paste the Secrets block above.
7. Select a supported Python version (Community Cloud currently defaults to Python 3.12).
8. Deploy.
9. Open the generated `*.streamlit.app` URL.
10. Verify the login screen appears before any application functions.
11. Verify invalid credentials are rejected.
12. Verify the supplied credentials open the application.
13. Verify no API key or password appears in page source, URL or error messages.

## RAG gate
`data/approved_sources.json` is a placeholder. Populate the knowledge base only with Singapore Government, Singapore public/private hospital and Singapore health-institute sources relevant to pregnancy/fertility before using medical-answer functionality.
