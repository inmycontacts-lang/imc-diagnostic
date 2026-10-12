# -*- coding: utf-8 -*-
"""
Capture des leads du Diagnostic 360°.
Priorité : Google Sheets (durable) via st.secrets["gcp_service_account"] + "gsheet_url".
Fallback : CSV local (éphémère sur Streamlit Cloud — averti dans l'UI).

Config attendue dans les Secrets Streamlit :
---------------------------------------------------------------
gsheet_url = "https://docs.google.com/spreadsheets/d/....."
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "xxxxx@xxxx.iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
---------------------------------------------------------------
Partager le Google Sheet en "Éditeur" avec le client_email du compte de service.
"""
import os
import csv
from datetime import datetime

HEADERS = ["Horodatage", "Prénom", "Nom", "Entreprise", "Secteur", "Téléphone", "Email",
           "Score global", "Pilier le plus faible", "Scores détaillés", "Consentement"]

CSV_PATH = os.path.join(os.path.dirname(__file__), "leads_local.csv")


def _row_from_lead(lead):
    return [
        lead.get("ts", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        lead.get("prenom", ""), lead.get("nom", ""), lead.get("entreprise", ""),
        lead.get("secteur", ""), lead.get("telephone", ""), lead.get("email", ""),
        lead.get("score_global", ""), lead.get("pilier_faible", ""),
        lead.get("scores", ""), "Oui" if lead.get("consent") else "Non",
    ]


def _save_gsheets(lead):
    """Tente l'enregistrement dans Google Sheets. Renvoie True si OK, lève sinon."""
    import streamlit as st
    import gspread
    from google.oauth2.service_account import Credentials

    if "gcp_service_account" not in st.secrets or "gsheet_url" not in st.secrets:
        raise RuntimeError("secrets manquants")

    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(st.secrets["gsheet_url"])
    ws = sh.sheet1
    # En-têtes si la 1re ligne est vide — via append_row (compatible gspread 5 ET 6).
    # NB : ws.update("A1", [HEADERS]) plantait en gspread 6.x (ordre des arguments
    # inversé : update(values, range_name)) → c'était la cause de la perte des leads.
    try:
        first_row = ws.row_values(1)
    except Exception:
        first_row = []
    if not first_row:
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")
    ws.append_row(_row_from_lead(lead), value_input_option="USER_ENTERED")
    return True


def _save_csv(lead):
    newfile = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if newfile:
            w.writerow(HEADERS)
        w.writerow(_row_from_lead(lead))
    return True


def save_lead(lead):
    """
    Enregistre un lead. Renvoie (ok: bool, mode: str, message: str).
    mode ∈ {"gsheets", "csv"}.
    """
    try:
        _save_gsheets(lead)
        return True, "gsheets", "Enregistré dans Google Sheets."
    except Exception as e:
        detail = "%s: %s" % (type(e).__name__, str(e)[:160])
        try:
            _save_csv(lead)
            return True, "csv", ("Google Sheets indisponible — enregistré en local "
                                 "(⚠️ éphémère sur Streamlit Cloud). Détail : " + detail)
        except Exception as e2:
            return False, "none", ("Échec total de l'enregistrement — " + detail +
                                   " | CSV : " + str(e2)[:120])


def diagnose_gsheets():
    """Diagnostic Google Sheets SANS fallback CSV : renvoie (ok, info).
    N'expose JAMAIS la clé privée — seulement l'URL, le client_email, le titre du
    classeur réellement atteint et le nb de lignes, ou l'exception exacte."""
    info = {}
    try:
        import streamlit as st
    except Exception as e:
        return False, {"streamlit_error": repr(e)}
    try:
        info["gcp_service_account_present"] = "gcp_service_account" in st.secrets
        info["gsheet_url_present"] = "gsheet_url" in st.secrets
        if info["gsheet_url_present"]:
            info["gsheet_url"] = str(st.secrets["gsheet_url"])
        if info["gcp_service_account_present"]:
            info["client_email"] = dict(st.secrets["gcp_service_account"]).get("client_email", "?")
    except Exception as e:
        return False, {"secrets_error": "%s: %s" % (type(e).__name__, str(e)[:200])}
    if not info.get("gcp_service_account_present") or not info.get("gsheet_url_present"):
        info["error"] = "Secret manquant : gcp_service_account et/ou gsheet_url absent des Secrets."
        return False, info
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(st.secrets["gsheet_url"])
        info["spreadsheet_title"] = sh.title
        ws = sh.sheet1
        info["worksheet_title"] = ws.title
        try:
            info["rows_before"] = len(ws.get_all_values())
        except Exception:
            info["rows_before"] = "?"
        return True, info
    except Exception as e:
        info["error"] = "%s: %s" % (type(e).__name__, str(e)[:300])
        return False, info
