"""FitTrack - a HealthifyMe-style health & nutrition tracker built with Streamlit."""
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="FitTrack", page_icon="🥗", layout="wide")

DATA_FILE = Path("fittrack_data.json")

# ----------------------------------------------------------------------------
# Style
# ----------------------------------------------------------------------------
CSS = """
<style>
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 2rem; max-width: 1100px;}
.hero {
    background: linear-gradient(120deg, #16a34a 0%, #0ea5a4 100%);
    color: #fff; padding: 22px 26px; border-radius: 18px; margin-bottom: 18px;
    box-shadow: 0 6px 18px rgba(22,163,74,.25);
}
.hero h2 {margin: 0; font-size: 1.6rem; color: #fff;}
.hero p {margin: 4px 0 0 0; opacity: .92;}
.stat {
    background: rgba(22,163,74,.08); border: 1px solid rgba(22,163,74,.25);
    border-radius: 14px; padding: 14px 16px; text-align: center;
}
.stat span {display: block; font-size: .8rem; opacity: .75; text-transform: uppercase; letter-spacing: .04em;}
.stat b {display: block; font-size: 1.6rem; margin-top: 2px;}
.stat small {opacity: .7;}
.ring-wrap {position: relative; width: 190px; height: 190px; margin: 6px auto 14px auto;}
.ring {
    width: 100%; height: 100%; border-radius: 50%;
    background: conic-gradient(var(--c) calc(var(--pct) * 1%), rgba(128,128,128,.22) 0);
    -webkit-mask: radial-gradient(farthest-side, transparent 72%, #000 73%);
            mask: radial-gradient(farthest-side, transparent 72%, #000 73%);
}
.ring-text {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; text-align: center;
}
.ring-text b {font-size: 2rem; line-height: 1.1;}
.ring-text span {font-size: .8rem; opacity: .7;}
.bar-row {margin: 10px 0;}
.bar-label {display: flex; justify-content: space-between; font-size: .9rem; margin-bottom: 4px;}
.bar-track {background: rgba(128,128,128,.22); border-radius: 99px;
