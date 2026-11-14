# -*- coding: utf-8 -*-
"""
Page Streamlit — Due Diligence TBI (protection d'un investissement international).
À déposer dans le dossier `pages/` de l'app IMC Diagnostic 360°.

INTÉGRATION LEAD : voir la fonction `enregistrer_lead()` plus bas (un seul endroit
à brancher sur votre pipeline Google Sheet existant — aucun secret dupliqué ici).
"""
import io

import pandas as pd
import streamlit as st

from dd_tbi_content import (
    BLOCS, GLOSSAIRE, STATUTS, TODO, NAVY, TURQ, GOLD,
    score_bloc, score_global, pourcentage, verdict,
)

# --------------------------------------------------------------------------
# Thème IMC (inline, pour rester autonome même sans config.toml)
# --------------------------------------------------------------------------
st.markdown(f"""
<style>
.imc-band {{background:{NAVY};padding:18px 22px;border-radius:8px;margin-bottom:6px;}}
.imc-band h1 {{color:#fff;margin:0;font-size:1.6rem;}}
.imc-band p  {{color:{TURQ};margin:2px 0 0;font-size:.95rem;}}
.imc-rule {{height:4px;background:{GOLD};border-radius:2px;margin:6px 0 18px;}}
.verdict {{padding:14px 18px;border-radius:8px;color:#fff;font-size:1.15rem;font-weight:700;text-align:center;}}
.imc-foot {{color:#7A8290;font-size:.8rem;margin-top:8px;}}
div[data-testid="stMetricValue"] {{color:{NAVY};}}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="imc-band"><h1>🛡️ Due Diligence TBI</h1>'
    '<p>Protection d\'un investissement par traité (TBI / chapitre investissement d\'ALE)</p></div>'
    '<div class="imc-rule"></div>', unsafe_allow_html=True)

st.caption("Choisissez un statut par point de contrôle — le score et le verdict se calculent automatiquement.")
st.info("ℹ️ Outil d'aide à la décision — **ne constitue pas un avis juridique**.", icon="ℹ️")


# --------------------------------------------------------------------------
# INTÉGRATION LEAD — à brancher sur votre pipeline existant
# --------------------------------------------------------------------------
def enregistrer_lead(nom, email, societe, score_pct, verdict_txt, consent):
    """
    Enregistre le lead via le pipeline existant : leads.save_lead() écrit dans le
    Google Sheet « IMC Leads 360 » (fallback CSV). Aucun secret n'est dupliqué ici,
    save_lead lit lui-même st.secrets. Un échec reste non bloquant.
    """
    try:
        from leads import save_lead
        ok, mode, msg = save_lead({
            "nom": nom,
            "entreprise": societe,
            "email": email,
            "score_global": score_pct,
            "pilier_faible": f"DD TBI — {verdict_txt}",
            "consent": consent,
        })
        if not ok:
            st.warning(f"Lead non enregistré : {msg}")
        return ok
    except Exception as e:  # noqa: BLE001
        st.warning(f"Lead non enregistré : {e}")
        return False


# --------------------------------------------------------------------------
# Saisie — un onglet par bloc
# --------------------------------------------------------------------------
statuts = {}
tabs = st.tabs([f"Bloc {code}" for code, _t, _c in BLOCS])
for (code, titre, criteres), tab in zip(BLOCS, tabs):
    with tab:
        st.subheader(f"Bloc {code} — {titre}")
        for ref, lib, chk, poids in criteres:
            flag = " ⭐" if poids == 2 else ""
            st.markdown(f"**{ref}. {lib}**{flag}")
            st.caption(chk)
            statuts[ref] = st.radio(
                label=f"statut_{ref}", options=STATUTS, index=0,
                horizontal=True, label_visibility="collapsed", key=f"st_{ref}",
            )
            st.divider()

# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------
rows = []
for code, titre, criteres in BLOCS:
    bs, bm = score_bloc(criteres, statuts)
    p = pourcentage(bs, bm)
    rows.append({"Bloc": f"{code} — {titre}", "Score": bs, "Max": bm,
                 "% protection": (round(p * 100, 1) if p is not None else None)})
df = pd.DataFrame(rows)

s_tot, m_tot = score_global(statuts)
p_tot = pourcentage(s_tot, m_tot)
v_txt, v_col = verdict(p_tot)

st.markdown("## 📊 Résultat")
c1, c2, c3 = st.columns([1, 1, 2])
c1.metric("Score global", f"{p_tot*100:.0f} %" if p_tot is not None else "—")
c2.metric("Points", f"{s_tot} / {m_tot}" if m_tot else "0 / 0")
with c3:
    st.markdown(f'<div class="verdict" style="background:{v_col}">{v_txt}</div>',
                unsafe_allow_html=True)

st.progress(p_tot if p_tot is not None else 0.0)

chart_df = df.dropna(subset=["% protection"]).set_index("Bloc")[["% protection"]]
if not chart_df.empty:
    st.bar_chart(chart_df, color=TURQ)
st.dataframe(df, use_container_width=True, hide_index=True)

st.caption("Lecture : ≥ 80 % Bien protégé  •  60–79 % Protection partielle  •  < 60 % Risque élevé"
           "   |   ⭐ = point critique (poids 2)")

# --------------------------------------------------------------------------
# Référentiel
# --------------------------------------------------------------------------
with st.expander("📚 Référentiel — notions clés"):
    for terme, dfn in GLOSSAIRE:
        st.markdown(f"**{terme}** — {dfn}")

# --------------------------------------------------------------------------
# Rapport (capture de lead puis export)
# --------------------------------------------------------------------------
st.markdown("## 📥 Recevoir le rapport")
with st.form("lead_dd_tbi"):
    cc1, cc2, cc3 = st.columns(3)
    nom = cc1.text_input("Nom *")
    email = cc2.text_input("Email *")
    societe = cc3.text_input("Société")
    consent = st.checkbox("J'accepte d'être recontacté par IMC et que mes données soient "
                          "traitées à cette fin (conformément à la réglementation).")
    ok = st.form_submit_button("Générer le rapport")

if ok:
    if not nom or not email:
        st.error("Merci d'indiquer au moins votre nom et votre email.")
    elif not consent:
        st.error("Merci de cocher la case de consentement pour continuer.")
    else:
        enregistrer_lead(nom, email, societe,
                         f"{p_tot*100:.0f}%" if p_tot is not None else "—", v_txt, consent)
        st.success("Rapport prêt — téléchargez-le ci-dessous.")
        detail = pd.DataFrame(
            [{"Réf": ref, "Point de contrôle": lib, "Poids": poids, "Statut": statuts[ref]}
             for _code, _t, crit in BLOCS for (ref, lib, _chk, poids) in crit]
        )
        buf = io.BytesIO()
        try:
            with pd.ExcelWriter(buf, engine="openpyxl") as xl:
                df.to_excel(xl, sheet_name="Synthèse", index=False)
                detail.to_excel(xl, sheet_name="Détail", index=False)
            st.download_button("⬇️ Télécharger le rapport (Excel)", buf.getvalue(),
                               file_name="IMC_DD_TBI_rapport.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception:  # openpyxl absent -> repli CSV
            st.download_button("⬇️ Télécharger le rapport (CSV)",
                               detail.to_csv(index=False).encode("utf-8"),
                               file_name="IMC_DD_TBI_rapport.csv", mime="text/csv")

st.markdown(
    f'<p class="imc-foot"><b>Nizar SALAH — IMC</b> · 95 avenue de Londres, Tunis 1002 · '
    f'+216 24 423 506 · inmycontacts@gmail.com<br>'
    f'Cadre d\'analyse : «الوجيز في القانون الدولي للاستثمار» — Pr F. Al Harchani, '
    f'Latrach Édition, 2026.</p>', unsafe_allow_html=True)
