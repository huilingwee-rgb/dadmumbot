# DadMumBot Security Baseline

## Authentication
A username/password gate is required before the pregnancy-planning functions are rendered. Password verification uses PBKDF2-HMAC-SHA256 with a unique salt and 310,000 iterations. Only the salted hash is stored in Streamlit Secrets.

Temporary credential is supplied separately; plaintext credentials are intentionally not stored in the repository.

## Error handling
- OpenAI call is wrapped and provider errors are not shown directly to users.
- A top-level exception boundary prevents unexpected errors from exposing stack traces to the browser.
- Server-side logging is used for debugging.
- User-facing errors are generic and avoid sensitive details.

## Secrets
Keep `OPENAI_API_KEY`, `APP_PASSWORD_HASH`, `APP_PASSWORD_SALT`, `APP_PASSWORD_ITERATIONS` and `APP_USERNAME` in Streamlit Community Cloud Secrets. Never commit them to GitHub.

## AI/security controls
- Treat user input and retrieved content as untrusted.
- Detect common prompt-injection attempts.
- Do not reveal system prompts, credentials or secrets.
- No arbitrary tools, shell commands or write access are granted to the model.
- Limit input, RAG context, output and request frequency.
- Ground medical answers only in approved Singapore sources once RAG is connected.

## Deployment
Streamlit Community Cloud provides secrets management and GitHub-based deployment. This baseline is OWASP-aligned but is not an OWASP certification or guarantee.
