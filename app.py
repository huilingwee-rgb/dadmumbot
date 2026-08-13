from __future__ import annotations
import logging
from datetime import date
import streamlit as st
from openai_client import generate_response
from prenatal_schedule import generate_prenatal_schedule, validate_pregnancy_dates
from retrieval import load_source_chunks, retrieve
from security import check_rate_limit, logout, prompt_injection_signal, render_login_gate, security_notice, validate_user_input

st.set_page_config(page_title="DadMumBot", page_icon="👶", layout="wide")
logger = logging.getLogger("dadmumbot")

def show_application_error():
    st.error("DadMumBot encountered an unexpected problem. No sensitive technical details are shown here. Please try again later.")

def main():
    if not render_login_gate(): return
    st.markdown("""<style>.main{padding-top:1.5rem}.app-title{font-size:2.4rem;font-weight:700}.app-subtitle{font-size:1.05rem;color:#666}.section-title{font-size:1.25rem;font-weight:650;margin:1rem 0 .6rem}.info-box{padding:.9rem 1rem;border-radius:.6rem;background:#f6f8fb;margin-bottom:1rem}</style>""", unsafe_allow_html=True)
    header_left, header_right=st.columns([5,1])
    with header_left:
        st.markdown('<div class="app-title">👶 DadMumBot</div>',unsafe_allow_html=True)
        st.markdown('<div class="app-subtitle">Your personalised maternity journey planner</div>',unsafe_allow_html=True)
    with header_right: st.button("Sign out",on_click=logout,use_container_width=True)
    st.markdown('<div class="info-box"><b>Getting started:</b> Tell us about your pregnancy journey. DadMumBot will use these details to personalise your information.</div>',unsafe_allow_html=True)
    with st.expander("IMPORTANT NOTICE - Please read before using DadMumBot",expanded=False):
        st.warning("IMPORTANT NOTICE: This web application is a prototype developed for educational purposes only. The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.\n\nFurthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.\n\nAlways consult with qualified professionals for accurate and personalised advice.")

    st.markdown('<div class="section-title">1. Pregnancy details</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: mother_age=st.number_input("Mother's age",18,60,30,1)
    with c2: conception_method=st.selectbox("Conception method",["Natural conception","IUI","IVF"])
    c3,c4=st.columns(2)
    with c3: current_week=st.selectbox("Current pregnancy week",list(range(1,43)),index=11,format_func=lambda x:f"Week {x}")
    with c4: edd_date=st.date_input("Estimated due date (EDD)",value=date.today())
    fet_date=None; embryo_age=None
    if conception_method=="IVF":
        st.markdown('<div class="section-title">2. IVF details</div>',unsafe_allow_html=True)
        a,b=st.columns(2)
        with a: fet_date=st.date_input("Embryo transfer (FET) date",value=date.today())
        with b: embryo_age=st.radio("Embryo age at transfer",["Day 3","Day 5"],horizontal=True)

    st.markdown('<div class="section-title">3. Review your details</div>',unsafe_allow_html=True)
    summary=[("Mother's age",f"{mother_age} years"),("Conception method",conception_method),("Current pregnancy week",f"Week {current_week}"),("EDD",edd_date.strftime("%d %b %Y"))]
    if conception_method=="IVF": summary += [("Embryo transfer date",fet_date.strftime("%d %b %Y")),("Embryo age",embryo_age)]
    for label,value in summary:
        x,y=st.columns([1,2]); x.write(f"**{label}**"); y.write(value)

    with st.expander("Retrieval status",expanded=False):
        try:
            chunks=load_source_chunks()
            st.write(f"Approved source pages loaded: {len({x['source_name'] for x in chunks})}")
            st.write(f"Retrievable text chunks: {len(chunks)}")
            warnings=st.session_state.get("retrieval_warnings",[])
            if warnings: st.warning("; ".join(warnings[:3]))
        except Exception: st.warning("The approved-source retrieval layer could not be initialised.")

    st.markdown('<div class="section-title">4. Ask DadMumBot</div>',unsafe_allow_html=True)
    # -----------------------------
    # Prenatal schedule and date validation
    # -----------------------------
    st.markdown("### Prenatal check schedule")

    validation_errors = validate_pregnancy_dates(
        conception_method=conception_method,
        edd_date=edd_date,
        fet_date=fet_date if conception_method == "IVF" else None,
    )

    if validation_errors:
        for validation_error in validation_errors:
            st.error(validation_error)

    if st.button(
        "Generate prenatal check schedule",
        type="secondary",
        use_container_width=True,
        disabled=bool(validation_errors),
    ):
        try:
            st.session_state["prenatal_schedule"] = generate_prenatal_schedule(
                current_week=current_week,
                conception_method=conception_method,
            )
        except Exception:
            logger.exception("Failed to generate prenatal schedule")
            st.error(
                "The prenatal schedule could not be generated. "
                "Please try again later."
            )

    if st.session_state.get("prenatal_schedule"):
        st.info(
            "Educational planning guide only. Your healthcare professional "
            "may recommend a different schedule for your individual pregnancy."
        )
        for item in st.session_state["prenatal_schedule"]:
            status = (
                "Current / upcoming"
                if item["week_end"] >= current_week
                else "Earlier milestone"
            )
            with st.expander(
                f'{item["week_label"]}: {item["title"]} - {status}',
                expanded=item["week_start"] <= current_week <= item["week_end"],
            ):
                st.write(item["details"])
                if item.get("optional"):
                    st.caption(
                        "This item may be optional or depend on individual circumstances."
                    )
                st.markdown(
                    f'**Source:** [{item["source_name"]}]({item["source_url"]})'
                )

    question=st.chat_input("Ask a pregnancy planning question...")
    if question:
        ok,cleaned=validate_user_input(question)
        if not ok: st.error(cleaned); return
        allowed,retry_after=check_rate_limit()
        if not allowed: st.warning(f"Too many requests. Please try again in about {retry_after} seconds."); return
        if prompt_injection_signal(cleaned): st.warning("That request contains instructions that cannot override DadMumBot's security rules. Please rephrase your pregnancy question."); return
        with st.chat_message("user"): st.write(cleaned)
        try:
            context, results=retrieve(cleaned,mother_age,conception_method,current_week,top_k=5)
            if not results:
                with st.chat_message("assistant"): st.info("The approved Singapore sources could not be retrieved at this time. Please try again later or consult your healthcare professional for personal advice.")
            else:
                with st.chat_message("assistant"):
                    st.write(generate_response(cleaned,context))
                    st.caption("Sources: " + "; ".join(dict.fromkeys(r["source_name"] for r in results)))
        except Exception:
            logger.exception("Retrieval or OpenAI request failed")
            show_application_error()
    st.divider(); security_notice()
    st.caption("DadMumBot provides general pregnancy information and planning. It does not diagnose medical conditions or interpret individual medical results.")

if __name__=="__main__":
    try: main()
    except Exception:
        logger.exception("Unhandled application error")
        show_application_error()
