# -*- coding: utf-8 -*-
"""拾光账本 - 直接嵌入设计稿 HTML，视觉 100% 一致"""
import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="拾光账本", page_icon="🌿", layout="wide")
st.markdown("""
<style>
.stApp, .stApp > div, .stApp > div > div, .stApp > div > div > div { padding: 0 !important; margin: 0 !important; }
[data-testid="stHeader"] { display: none; }
[data-testid="stAppViewContainer"] { padding: 0 !important; margin: 0 !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

html_path = os.path.join(os.path.dirname(__file__), "assets", "shiguang.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=1200, scrolling=False)
