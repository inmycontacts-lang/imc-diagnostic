# -*- coding: utf-8 -*-
"""Tracking GA4 léger pour Streamlit (quick win audit).

Injecte gtag.js et émet les événements via st.components.v1.html (iframe), avec une
FILE d'événements en session_state qui SURVIT aux reruns Streamlit.

Config : définir l'ID GA4 dans les Secrets Streamlit →
    ga_measurement_id = "G-XXXXXXXXXX"
Sans secret, le placeholder G-XXXXXXXXXX est utilisé (inoffensif : aucune donnée réelle
n'est collectée, l'app ne plante pas en preview).

Événements câblés : start_diagnostic, unlock_click, lead_submit.

LIMITE CONNUE : components.html s'exécute dans une iframe (contexte séparé), donc les
page_view sont attribuées à cette iframe. Pour un suivi « propre » (page_view corrects
+ événements fiables), voir la PR : patch de l'index.html Streamlit pour gtag + envoi
des événements via le Measurement Protocol côté serveur. Cette version privilégie le
zéro-friction (aucun secret requis pour tester tout de suite).
"""
import json

PLACEHOLDER_ID = "G-XXXXXXXXXX"


def _ga_id():
    try:
        import streamlit as st
        return st.secrets.get("ga_measurement_id", PLACEHOLDER_ID)
    except Exception:
        return PLACEHOLDER_ID


def track(event, **params):
    """Enfile un événement GA4 ; il sera émis au prochain boot() (survit aux reruns)."""
    try:
        import streamlit as st
        st.session_state.setdefault("_ga_queue", []).append({"name": event, "params": params})
    except Exception:
        pass


def boot():
    """À appeler 1× par rendu (en fin d'app). Émet page_view (1×/session) + vide la file."""
    try:
        import streamlit as st
        import streamlit.components.v1 as components
    except Exception:
        return
    ss = st.session_state
    first = not ss.get("_ga_booted")
    queue = ss.get("_ga_queue", [])
    if not first and not queue:
        return
    gid = _ga_id()
    parts = [
        '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>' % gid,
        '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}',
        'gtag("js",new Date());gtag("config","%s");' % gid,
    ]
    for ev in queue:
        parts.append('gtag("event",%s,%s);' % (json.dumps(ev["name"]), json.dumps(ev.get("params", {}))))
    parts.append('</script>')
    try:
        components.html("".join(parts), height=0, width=0)
    except Exception:
        return
    ss["_ga_booted"] = True
    ss["_ga_queue"] = []
