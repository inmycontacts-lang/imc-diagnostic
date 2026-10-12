# -*- coding: utf-8 -*-
"""Pages du Diagnostic Stratégique 360° : questionnaire + capture lead, catalogue, annuaire."""
import datetime
import streamlit as st
import plotly.graph_objects as go

import content_360 as C
import leads as LEADS
import report360 as RP
from theme import NAVY, TURQ, GOLD, GREEN, AMBER, RED, maturity_label, CONTACT

PDF_MIME = "application/pdf"


def _band(title, sub):
    st.markdown(f'<div class="imc-band">{title}<small>{sub}</small></div>', unsafe_allow_html=True)
    st.write("")


def _radar(res360):
    cats = [p["nom"].split(" & ")[0].split(" (")[0] for p in res360["pillars"]]
    vals = [p["score"] for p in res360["pillars"]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=cats + [cats[0]], fill="toself",
                                  name="Votre entreprise", line_color=TURQ))
    fig.add_trace(go.Scatterpolar(r=[60] * (len(cats) + 1), theta=cats + [cats[0]],
                                  name="Seuil recommandé (60%)", line=dict(color=GOLD, dash="dot")))
    fig.update_layout(height=420, polar=dict(radialaxis=dict(range=[0, 100])),
                      legend=dict(orientation="h", y=-0.12), margin=dict(t=20, l=40, r=40))
    return fig


def render_360():
    ss = st.session_state
    _band("🎯 Diagnostic Stratégique 360°",
          "Évaluez la maturité de votre entreprise sur 6 piliers — gratuit, en 5 minutes.")

    st.markdown("Répondez aux questions ci-dessous. Votre **score de maturité** et vos "
                "**axes de progrès** s'affichent immédiatement.")

    # ---------------- QUESTIONNAIRE ----------------
    answers = {}
    for p in C.PILLARS:
        with st.expander(f"{p['icon']}  {p['nom']}", expanded=False):
            st.caption(p["intro"])
            for qkey, qlabel, opts in p["questions"]:
                labels = [o[0] for o in opts]
                choice = st.radio(qlabel, labels, index=1, key=f"q_{qkey}")
                answers[qkey] = dict(opts)[choice]

    res360 = C.compute_360(answers)
    ss["res360"] = res360

    st.divider()

    # ---------------- APERÇU GRATUIT ----------------
    g = res360["global"]
    lab, col, state = maturity_label(g)
    c1, c2 = st.columns([1, 1.1])
    with c1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=g, number={"suffix": " / 100", "font": {"size": 40, "color": NAVY}},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": col},
                   "steps": [{"range": [0, 40], "color": "#F8D7DA"}, {"range": [40, 60], "color": "#FFF3CD"},
                             {"range": [60, 100], "color": "#D4EDDA"}]}))
        fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=0),
                          title={"text": f"Score global — <b>{lab}</b>", "font": {"color": NAVY}})
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.plotly_chart(_radar(res360), width="stretch")

    # ---------------- GATE / DÉBLOCAGE ----------------
    if not ss.get("unlocked_360"):
        st.markdown('<div class="lockbox">', unsafe_allow_html=True)
        st.markdown("### 🔒 Débloquez votre analyse détaillée")
        st.markdown("Recevez l'**analyse complète par pilier**, votre **plan d'action personnalisé** et le "
                    "**rapport PDF**. Renseignez vos coordonnées — un expert IMC peut vous rappeler.")
        with st.form("lead_form", clear_on_submit=False):
            a, b = st.columns(2)
            prenom = a.text_input("Prénom *")
            nom = b.text_input("Nom *")
            entreprise = a.text_input("Entreprise *")
            secteur = b.selectbox("Secteur d'activité *", C.SECTEURS)
            telephone = a.text_input("Téléphone *")
            email = b.text_input("E-mail *")
            consent = st.checkbox("J'accepte d'être recontacté par IMC et que mes données soient "
                                  "traitées à cette fin (conformément à la réglementation).")
            submitted = st.form_submit_button("🔓 Débloquer mon analyse complète", type="primary")
        if submitted:
            missing = not all([prenom.strip(), nom.strip(), entreprise.strip(), telephone.strip(), email.strip()])
            if missing:
                st.error("Merci de renseigner tous les champs obligatoires (*).")
            elif "@" not in email or "." not in email:
                st.error("Merci de saisir une adresse e-mail valide.")
            elif not consent:
                st.error("Merci de cocher la case de consentement pour continuer.")
            else:
                pires = sorted(res360["pillars"], key=lambda x: x["score"])
                lead = dict(
                    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    prenom=prenom.strip(), nom=nom.strip(), entreprise=entreprise.strip(),
                    secteur=secteur, telephone=telephone.strip(), email=email.strip(),
                    score_global=g, pilier_faible=pires[0]["nom"],
                    scores="; ".join(f"{p['nom'].split(' &')[0]}:{p['score']}%" for p in res360["pillars"]),
                    consent=consent)
                ok, mode, msg = LEADS.save_lead(lead)
                ss["unlocked_360"] = True
                ss["lead_360"] = lead
                if mode == "csv":
                    st.warning("Analyse débloquée. (Note admin : " + msg + ")")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.info("🔎 Aperçu gratuit affiché ci-dessus. L'analyse détaillée et le rapport PDF se débloquent "
                "après le formulaire.")
        return

    # ---------------- ANALYSE DÉTAILLÉE (débloquée) ----------------
    lead = ss.get("lead_360", {})
    st.success(f"✅ Analyse débloquée pour **{lead.get('entreprise','votre entreprise')}**. "
               "Votre plan d'action est ci-dessous.")

    st.markdown("### 📊 Détail par pilier")
    for p in res360["pillars"]:
        plab, pcol, pstate = maturity_label(p["score"])
        st.markdown(
            f'<div class="pcard"><h4>{p["icon"]} {p["nom"]} — '
            f'<span style="color:{pcol}">{p["score"]}% · {plab}</span></h4>'
            f'<div style="background:#eef1f6;border-radius:6px;height:10px;overflow:hidden">'
            f'<div style="width:{p["score"]}%;height:10px;background:{pcol}"></div></div></div>',
            unsafe_allow_html=True)

    recos = C.recommend_services(res360)
    st.markdown("### 💡 Votre plan d'action — comment IMC peut vous aider")
    if not recos:
        st.markdown('<div class="alert a-safe">🟢 Tous vos piliers dépassent le seuil critique. '
                    'IMC peut vous accompagner pour viser l\'excellence et structurer votre croissance.</div>',
                    unsafe_allow_html=True)
    else:
        for nom, icon, score, services in recos:
            plab, pcol, _ = maturity_label(score)
            st.markdown(f"**{icon} {nom} — {score}% ({plab})**")
            for s in services:
                st.markdown(f"- 👉 {s}")

    # PDF
    try:
        pdf_bytes = RP.build_pdf(lead, res360, recos)
        st.download_button("📄 Télécharger mon rapport PDF", data=pdf_bytes,
                           file_name="Diagnostic_360_IMC.pdf", mime=PDF_MIME, type="primary", width="stretch")
    except Exception as e:
        st.info("Le rapport PDF sera disponible sous peu. (" + type(e).__name__ + ")")

    st.markdown('<div class="cta">📞 Besoin d\'aide pour appliquer ce plan ? Prenez RDV avec un expert '
                'In My Contacts.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="coord">{CONTACT}</div>', unsafe_allow_html=True)
    if st.button("↩️ Recommencer le diagnostic"):
        ss["unlocked_360"] = False
        st.rerun()


def render_catalogue():
    _band("📖 Catalogue Services & Offres IMC",
          "Du diagnostic à l'action — des prestations concrètes pour chaque besoin.")
    for fam in C.CATALOGUE:
        st.markdown(f"### {fam['icon']} {fam['famille']}")
        for titre, prix in fam["offres"]:
            st.markdown(f'<div class="svc"><h4>{titre}</h4>'
                        f'<span class="price">{prix}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="cta">➡️ Un besoin précis ? Parlons-en — devis gratuit sous 48h.</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="coord">{CONTACT}</div>', unsafe_allow_html=True)


def render_annuaire():
    ss = st.session_state
    _band("📘 Annuaire Pro IMC & Réseau d'Affaires",
          "Gagnez en visibilité B2B et en crédibilité dans un réseau vérifié.")
    st.markdown("### ✨ Les bénéfices")
    for b in C.ANNUAIRE["benefices"]:
        st.markdown(f"- ✅ {b}")
    st.markdown("### 💼 Formules")
    cols = st.columns(len(C.ANNUAIRE["formules"]))
    for col, (nom, prix, feats) in zip(cols, C.ANNUAIRE["formules"]):
        badge = ' <span class="badge-vip">RECOMMANDÉ</span>' if "VIP" in nom else ""
        with col:
            st.markdown(f'<div class="svc"><h4>{nom}{badge}</h4>'
                        f'<span class="price">{prix}</span></div>', unsafe_allow_html=True)
            for f in feats:
                st.markdown(f"- {f}")

    st.markdown("### 📝 Demande de référencement")
    if ss.get("annuaire_sent"):
        st.success("✅ Votre demande est enregistrée. L'équipe IMC vous recontacte pour finaliser votre fiche.")
    else:
        with st.form("annuaire_form"):
            a, b = st.columns(2)
            ent = a.text_input("Entreprise *")
            sect = b.selectbox("Secteur *", C.SECTEURS)
            contact = a.text_input("Nom du contact *")
            email = b.text_input("E-mail *")
            tel = a.text_input("Téléphone")
            formule = b.selectbox("Formule souhaitée", [f[0] for f in C.ANNUAIRE["formules"]])
            consent = st.checkbox("J'accepte d'être recontacté par IMC à propos de l'annuaire.")
            sent = st.form_submit_button("Envoyer ma demande", type="primary")
        if sent:
            if not all([ent.strip(), contact.strip(), email.strip()]) or "@" not in email:
                st.error("Merci de renseigner l'entreprise, le contact et un e-mail valide.")
            elif not consent:
                st.error("Merci de cocher la case de consentement.")
            else:
                lead = dict(prenom=contact.strip(), nom="", entreprise=ent.strip(), secteur=sect,
                            telephone=tel.strip(), email=email.strip(), score_global="",
                            pilier_faible=f"ANNUAIRE — {formule}", scores="", consent=consent)
                LEADS.save_lead(lead)
                ss["annuaire_sent"] = True
                st.rerun()
    st.markdown(f'<div class="coord">{CONTACT}</div>', unsafe_allow_html=True)
