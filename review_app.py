"""Private human-review workbench; never part of the public Vercel app."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st
from career_radar.ui.review import render

st.set_page_config(page_title="Career Radar · Private evidence review", layout="wide")
render()
