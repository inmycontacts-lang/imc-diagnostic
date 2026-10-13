# -*- coding: utf-8 -*-
"""
IN MY CONTACTS (IMC) — Diagnostic Stratégique 360° + Services + Annuaire + Diagnostic Financier.
Lead magnet : diagnostic gratuit → capture de leads → recommandations de services IMC.
Auteur : Nizar SALAH — IMC   •   Lancer : streamlit run app.py
"""
import streamlit as st
from theme import CSS, LOGO, CONTACT, CONTACT_HTML

st.set_page_config(page_title="Diagnostic 360° IMC", page_icon="🎯", layout="wide",
                   initial_sidebar_state="expanded")
try:
    st.logo(LOGO, size="large")
except Exception:
    pass
st.markdown(CSS, unsafe_allow_html=True)

# Logo + accroche dans la barre latérale
try:
    st.sidebar.image(LOGO, width=230)
except Exception:
    st.sidebar.markdown("### In My Contacts")

from pages_360 import render_360, render_catalogue, render_annuaire
from financial_module import render_financial

PAGES = [
    st.Page(render_360, title="Diagnostic 360°", icon="🎯", default=True),
    st.Page(render_catalogue, title="Catalogue Services IMC", icon="📖"),
    st.Page(render_annuaire, title="Annuaire Pro IMC", icon="📘"),
    st.Page(render_financial, title="Diagnostic Financier (expert)", icon="💶"),
]

nav = st.navigation(PAGES)

# Pied de barre latérale : contact permanent
st.sidebar.divider()
st.sidebar.caption("📞 Un expert IMC vous accompagne :")
st.sidebar.markdown(f"<div style='font-size:.8rem;color:#5A6473;line-height:1.5'>{CONTACT_HTML}</div>",
                    unsafe_allow_html=True)

nav.run()
