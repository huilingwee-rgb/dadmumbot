from __future__ import annotations
import logging
from datetime import date
import streamlit as st
from openai_client import generate_response
from security import check_rate_limit, logout, prompt_injection_signal, render_login_gate, security_notice, validate_user_input

st.set_page_config(page_title="DadMumBot", page_icon="👶", layout="wide")
logger = logging.getLogger("dadmumbot")

def show_application_error() -> None:
    st.error("DadMumBot encountered an unexpected problem. No sensitive technical details are shown here. Please try again later.")

def main() -> None:
    if not render_login_gate():
        return
    st.markdown("""
    <style>
        .main { padding-top: 1.5rem; }
        .app-title { font-size: 2.4rem; font-weight: 700; margin-bottom: .2rem; }
        .app-subtitle { font-size: 1.05rem; color: #666; margin-bottom: 1.5rem; }
        .section-title { font-size: 1.25rem; font-weight: 650; margin: 1rem 0 .6rem; }
        .info-box { padding: .9rem 1rem; border-radius: .6rem; background: #f6f8fb; margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)
    header_left, header_right = st.columns([5, 1])
    with header_left:
        st.markdown('<div class="app-title">👶 DadMumBot</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-subtitle">Your personalised maternity journey planner</div>', unsafe_allow_html=True)
    with header_right:
        st.button("Sign out", on_click=logout, use_container_width=True)
    st.markdown('<div class="info-box"><b>Getting started:</b> Tell us about your pregnancy journey. DadMumBot will use these details to personalise your information.</div>', unsafe_allow_html=True)
    st.markdown("### Prototype notice")
    with st.expander("IMPORTANT NOTICE - Please read before using DadMumBot", expanded=False):
        st.warning("IMPORTANT NOTICE: This web application is a prototype developed for educational purposes only. The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.\n\nFurthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.\n\nAlways consult with qualified professionals for accurate and personalised advice.")

    st.markdown('<div class="section-title">1. Pregnancy details</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        mother_age = st.number_input("Mother's age", min_value=18, max_value=60, value=30, step=1)
    with col2:
        conception_method = st.selectbox("Conception method", ["Natural conception", "IUI", "IVF"])
    col3, col4 = st.columns(2)
    with col3:
        current_week = st.selectbox("Current pregnancy week", list(range(1, 43)), index=11, format_func=lambda x: f"Week {x}")
    with col4:
        edd_date = st.date_input("Estimated due date (EDD)", value=date.today(), help="Use the EDD provided by your healthcare professional.")
    fet_date = None; embryo_age = None
    if conception_method == "IVF":
        st.markdown('<div class="section-title">2. IVF details</div>', unsafe_allow_html=True)
        st.info("For IVF pregnancies, provide the embryo transfer date and embryo age.")
        ivf_col1, ivf_col2 = st.columns(2)
        with ivf_col1: fet_date = st.date_input("Embryo transfer (FET) date", value=date.today())
        with ivf_col2: embryo_age = st.radio("Embryo age at transfer", ["Day 3", "Day 5"], horizontal=True)

    st.markdown('<div class="section-title">3. Review your details</div>', unsafe_allow_html=True)
    summary = [("Mother's age", f"{mother_age} years"), ("Conception method", conception_method), ("Current pregnancy week", f"Week {current_week}"), ("EDD", edd_date.strftime("%d %b %Y"))]
    if conception_method == "IVF": summary += [("Embryo transfer date", fet_date.strftime("%d %b %Y")), ("Embryo age", embryo_age)]
    for label, value in summary:
        c1, c2 = st.columns([1, 2]); c1.write(f"**{label}**"); c2.write(value)

    st.markdown('<div class="section-title">4. Ask DadMumBot</div>', unsafe_allow_html=True)
    question = st.chat_input("Ask a pregnancy planning question...")
    if question:
        ok, cleaned = validate_user_input(question)
        if not ok: st.error(cleaned)
        else:
            allowed, retry_after = check_rate_limit()
            if not allowed: st.warning(f"Too many requests. Please try again in about {retry_after} seconds.")
            elif prompt_injection_signal(cleaned): st.warning("That request contains instructions that cannot override DadMumBot's security rules. Please rephrase your pregnancy question.")
            else:
                with st.chat_message("user"): st.write(cleaned)
                retrieved_context = "No approved Singapore source material has been retrieved yet. State that the information is unavailable rather than inventing medical claims."
                with st.chat_message("assistant"):
                    try:
                        st.write(generate_response(cleaned, retrieved_context))
                    except Exception:
                        logger.exception("OpenAI request failed")
                        show_application_error()
    st.divider(); security_notice()
    st.caption("DadMumBot provides general pregnancy information and planning. It does not diagnose medical conditions or interpret individual medical results.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Unhandled application error")
        show_application_error()
