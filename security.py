"""Security, authentication and cost-control helpers for DadMumBot."""
from __future__ import annotations
import hashlib, hmac, os, re, time
from typing import Optional
import streamlit as st

MAX_INPUT_CHARS = 1200
MAX_OUTPUT_CHARS = 5000
MAX_RAG_CONTEXT_CHARS = 9000
REQUESTS_PER_WINDOW = 10
WINDOW_SECONDS = 60
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300
INJECTION_PATTERNS = [
    r"ignore\s+(all|any|the)\s+(previous|prior|above)\s+instructions",
    r"reveal\s+(your|the)\s+(system|developer)\s+prompt",
    r"show\s+me\s+(your|the)\s+(api\s*key|secret|token)",
    r"developer\s+message", r"system\s+message", r"jailbreak",
]

def _get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        value = st.secrets.get(name)
        if value is not None:
            return str(value)
    except Exception:
        pass
    value = os.getenv(name)
    return str(value) if value is not None else default

def _password_hash(password: str, salt_hex: str, iterations: int) -> str:
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()

def authenticate_user(username: str, password: str) -> bool:
    configured_user = _get_secret("APP_USERNAME")
    configured_hash = _get_secret("APP_PASSWORD_HASH")
    salt_hex = _get_secret("APP_PASSWORD_SALT")
    iterations_raw = _get_secret("APP_PASSWORD_ITERATIONS", "310000")
    if not configured_user or not configured_hash or not salt_hex:
        raise RuntimeError("Application authentication is not configured on the server.")
    try:
        iterations = int(iterations_raw or "310000")
    except ValueError:
        iterations = 310000
    if not hmac.compare_digest(username, configured_user):
        return False
    try:
        candidate = _password_hash(password, salt_hex, iterations)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, configured_hash)

def _login_attempt_allowed() -> tuple[bool, int]:
    now = time.time()
    attempts = [t for t in st.session_state.get("login_attempt_timestamps", []) if now - t < LOGIN_WINDOW_SECONDS]
    if len(attempts) >= LOGIN_MAX_ATTEMPTS:
        retry_after = max(1, int(LOGIN_WINDOW_SECONDS - (now - attempts[0])))
        st.session_state["login_attempt_timestamps"] = attempts
        return False, retry_after
    st.session_state["login_attempt_timestamps"] = attempts
    return True, 0

def record_login_attempt() -> None:
    attempts = st.session_state.get("login_attempt_timestamps", [])
    attempts.append(time.time())
    st.session_state["login_attempt_timestamps"] = attempts

def render_login_gate() -> bool:
    if st.session_state.get("authenticated", False):
        return True
    st.title("🔐 DadMumBot")
    st.subheader("Secure prototype access")
    st.caption("Enter the credentials provided by the project owner to access the application.")
    with st.form("login_form"):
        username = st.text_input("Username", max_chars=80, autocomplete="username")
        password = st.text_input("Password", type="password", max_chars=200, autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        allowed, retry_after = _login_attempt_allowed()
        if not allowed:
            st.error(f"Too many login attempts. Please try again in about {retry_after} seconds.")
            return False
        record_login_attempt()
        try:
            ok = authenticate_user(username.strip(), password)
        except Exception:
            st.error("The login service is not configured correctly. Please contact the application owner.")
            return False
        if ok:
            st.session_state["authenticated"] = True
            st.session_state["login_attempt_timestamps"] = []
            st.rerun()
        else:
            st.error("Invalid username or password.")
    return False

def logout() -> None:
    st.session_state["authenticated"] = False
    st.session_state.pop("login_attempt_timestamps", None)
    st.rerun()

def validate_user_input(text: str) -> tuple[bool, str]:
    if not isinstance(text, str): return False, "Invalid input."
    clean = " ".join(text.split())
    if not clean: return False, "Please enter a question."
    if len(clean) > MAX_INPUT_CHARS: return False, f"Please keep your question under {MAX_INPUT_CHARS} characters."
    return True, clean

def prompt_injection_signal(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)

def trim_rag_context(text: str, limit: int = MAX_RAG_CONTEXT_CHARS) -> str:
    if not text: return "No approved source material was retrieved."
    seen, unique_parts = set(), []
    for part in text.split("\n\n"):
        normalized = " ".join(part.split()).strip()
        if not normalized: continue
        key = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if key in seen: continue
        seen.add(key); unique_parts.append(part.strip())
    result = "\n\n".join(unique_parts)
    if len(result) <= limit: return result
    return result[:limit].rsplit(" ", 1)[0] + "\n[Source context truncated for safety and cost control.]"

def redact_sensitive(text: str) -> str:
    text = re.sub(r"sk-[A-Za-z0-9_-]{10,}", "[REDACTED_KEY]", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED_TOKEN]", text, flags=re.I)
    text = re.sub(r"(?i)(api[_ -]?key|token|secret)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
    return text

def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def check_rate_limit() -> tuple[bool, int]:
    now = time.time()
    timestamps = [t for t in st.session_state.get("request_timestamps", []) if now - t < WINDOW_SECONDS]
    if len(timestamps) >= REQUESTS_PER_WINDOW:
        retry_after = max(1, int(WINDOW_SECONDS - (now - timestamps[0])))
        st.session_state["request_timestamps"] = timestamps
        return False, retry_after
    timestamps.append(now); st.session_state["request_timestamps"] = timestamps
    return True, 0

def safe_error_message(exc: Exception) -> str:
    _ = redact_sensitive(str(exc))
    return "The request could not be completed. Please try again later."

def security_notice() -> None:
    st.caption("Security and cost controls are enabled. Do not enter API keys, authentication tokens, or unnecessary medical record identifiers into the chat.")
