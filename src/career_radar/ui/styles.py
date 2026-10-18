"""Shared, accessible styling for the research studio."""
import streamlit as st


def apply_styles() -> None:
    st.markdown("""
    <style>
    .block-container {max-width:1220px;padding-top:4.2rem;padding-bottom:4rem;}
    h1,h2,h3 {letter-spacing:-.035em;color:#142e30;}
    h1 {font-size:clamp(2.5rem,5vw,4.2rem)!important;line-height:1.08!important;}
    p {line-height:1.65;}
    .radar-brand {font-size:.85rem;letter-spacing:.16em;font-weight:750;color:#17675e;}
    .radar-eyebrow {font-size:.75rem;font-weight:750;letter-spacing:.13em;color:#17675e;margin-top:1rem;}
    .radar-lede {font-size:1.2rem;color:#405853;max-width:700px;margin-bottom:1.5rem;}
    .radar-chip {display:inline-block;padding:.25rem .65rem;border-radius:2rem;background:#e5eeea;
      color:#23534d;font-size:.75rem;font-weight:650;margin:0 .3rem .7rem 0;}
    .radar-number {font-size:.8rem;letter-spacing:.1em;color:#a64a28;font-weight:750;}
    div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
    div[data-testid="stMetric"] {padding:.6rem 0;}
    button {min-height:2.75rem;}
    .st-key-radar_nav div[role="radiogroup"] {gap:.4rem;flex-wrap:wrap;}
    .st-key-radar_nav label[data-testid="stRadioOption"] {border:1px solid #d9dfd9;border-radius:2rem;
      padding:.4rem .75rem;margin:0;background:#f1f2ec;transition:background .15s;}
    .st-key-radar_nav label[data-testid="stRadioOption"]:has(input:checked) {background:#e0ece6;border-color:#17675e;}
    .st-key-radar_nav label[data-testid="stRadioOption"]:focus-within {outline:2px solid #17675e;outline-offset:2px;}
    .radar-orbit {height:62px;margin:.5rem 0 .25rem;}
    .radar-orbit svg {width:190px;height:62px;max-width:100%;}
    .radar-footer {font-size:.8rem;color:#536660;margin-top:2rem;border-top:1px solid #d9dfd9;padding-top:1rem;}
    @media(max-width:640px){.block-container{padding:4.2rem 1rem 3rem;}h1{font-size:2.5rem!important;}}
    </style>
    """, unsafe_allow_html=True)
