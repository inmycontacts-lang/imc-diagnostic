# -*- coding: utf-8 -*-
"""
OUTIL DE DIAGNOSTIC FINANCIER IMC — Application web (Streamlit)
Démo interactive : le dirigeant ajuste ses hypothèses et voit le diagnostic se recalculer en direct.
Auteur : Nizar SALAH — IMC   •   Lancer : streamlit run app.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import engine as E

# ============================ CONFIG & CHARTE IMC ============================
NAVY, TURQ, GOLD = "#1C2A4A", "#3DB9BC", "#C9A961"
GREEN, AMBER, RED = "#1E7E34", "#9C6500", "#B02A37"
GREEN_BG, AMBER_BG, RED_BG = "#D4EDDA", "#FFF3CD", "#F8D7DA"

st.set_page_config(page_title="Diagnostic Financier IMC", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(f"""
<style>
  .block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; }}
  h1, h2, h3 {{ color: {NAVY}; }}
  .imc-band {{ background:{NAVY}; color:white; padding:14px 18px; border-radius:10px;
               font-size:1.5rem; font-weight:700; }}
  .imc-sub {{ background:{GOLD}; color:{NAVY}; padding:5px 18px; border-radius:0 0 10px 10px;
              font-weight:600; font-size:.85rem; margin-top:-6px; }}
  .alert {{ padding:10px 14px; border-radius:8px; margin-bottom:7px; font-size:.92rem; }}
  .a-safe {{ background:{GREEN_BG}; color:{GREEN}; }}
  .a-warn {{ background:{AMBER_BG}; color:{AMBER}; }}
  .a-danger {{ background:{RED_BG}; color:{RED}; }}
  [data-testid="stMetricValue"] {{ color:{NAVY}; font-weight:700; }}
  .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
  .stTabs [data-baseweb="tab"] {{ background:#F4F6F9; border-radius:8px 8px 0 0; padding:8px 14px; }}
  .stTabs [aria-selected="true"] {{ background:{NAVY}; color:white; }}
  .cta {{ background:{NAVY}; color:white; padding:14px 18px; border-radius:10px; text-align:center;
          font-weight:700; font-size:1.05rem; }}
  .coord {{ background:{GOLD}; color:{NAVY}; padding:9px 18px; border-radius:0 0 10px 10px;
            text-align:center; font-weight:600; font-size:.85rem; }}
</style>
""", unsafe_allow_html=True)

# ============================ HELPERS ============================
def dt(x):
    return f"{x:,.0f}".replace(",", " ") + " DT"
def pct(x):
    return f"{x*100:,.1f}".replace(",", " ") + " %"
def num(x, s=""):
    return f"{x:,.2f}".replace(",", " ") + s
def badge(state):
    return {"safe": "🟢", "warn": "🟡", "danger": "🔴"}.get(state, "")
def alert_html(state, txt):
    cls = {"safe": "a-safe", "warn": "a-warn", "danger": "a-danger"}[state]
    return f'<div class="alert {cls}">{badge(state)}&nbsp; {txt}</div>'

# ============================ SIDEBAR : INPUTS ============================
ss = st.session_state
st.sidebar.markdown(f"### 📊 Diagnostic Financier **IMC**")
st.sidebar.caption("Ajuste les paramètres — tout se recalcule en direct.")

scen = st.sidebar.selectbox("🎛️ Scénario", list(E.SCENARIOS.keys()),
                            index=list(E.SCENARIOS).index(ss.get("scen", "Cas de Base")))
# (ré)initialiser les hypothèses sur le preset quand le scénario change
if ss.get("scen") != scen or "hyp_croiss" not in ss:
    for k, v in E.SCENARIOS[scen].items():
        ss[f"hyp_{k}"] = v
    ss["scen"] = scen

sector = st.sidebar.selectbox("🏭 Secteur (benchmark)", E.SECTORS, index=0)

with st.sidebar.expander("⚙️ Hypothèses (ajustables)", expanded=True):
    st.slider("Croissance du CA", -0.30, 0.50, step=0.01, key="hyp_croiss", format="%.0f%%")
    st.slider("Taux de marge brute", 0.20, 0.80, step=0.01, key="hyp_marge", format="%.0f%%")
    st.slider("DSO — délai clients (j)", 0, 120, step=1, key="hyp_dso")
    st.slider("DPO — délai fournisseurs (j)", 0, 120, step=1, key="hyp_dpo")
    st.slider("DIO — rotation stocks (j)", 0, 120, step=1, key="hyp_dio")
    st.slider("Évolution charges externes", -0.10, 0.30, step=0.01, key="hyp_evolCF", format="%.0f%%")
    st.slider("Évolution masse salariale", -0.10, 0.30, step=0.01, key="hyp_evolMS", format="%.0f%%")
    st.number_input("CapEx annuel (DT)", 0, 1_000_000, step=10000, key="hyp_capex")
    st.slider("Taux d'intérêt dette", 0.0, 0.25, step=0.005, key="hyp_tint", format="%.1f%%")
    st.slider("Distribution de dividendes", 0.0, 1.0, step=0.05, key="hyp_tdiv", format="%.0f%%")

with st.sidebar.expander("💰 Paramètres de valorisation"):
    wacc = st.slider("WACC", 0.05, 0.25, value=E.DEFAULT_VAL["wacc"], step=0.005, format="%.1f%%", key="val_wacc")
    gg   = st.slider("Croissance perpétuelle (g)", 0.0, 0.05, value=E.DEFAULT_VAL["g"], step=0.005, format="%.1f%%", key="val_g")
    mult = st.slider("Multiple d'EBE", 2.0, 10.0, value=E.DEFAULT_VAL["mult"], step=0.5, key="val_mult")

LINE_LABELS = [("ca","Chiffre d'affaires"),("ach","Achats consommés"),("cext","Charges externes"),
               ("ms","Masse salariale"),("dot","Dotations amort."),("chfin","Charges financières"),
               ("is_","Impôt (IS)"),("ai","Actif immobilisé"),("stk","Stocks"),("cre","Créances clients"),
               ("four","Dettes fournisseurs"),("cp","Capitaux propres"),("df","Dettes financières"),
               ("capex","CapEx"),("emp","Nouvel emprunt"),("remb","Remboursement"),("div","Dividendes")]
with st.sidebar.expander("📥 Données de l'entreprise (2023 → 2025)"):
    base_df = pd.DataFrame({lbl: E.DEFAULT_HIST[k] for k, lbl in LINE_LABELS},
                           index=["2023", "2024", "2025"]).T
    edited = st.data_editor(base_df, width="stretch", key="data_editor")
    hist = {k: [float(edited.loc[lbl, y]) for y in ["2023", "2024", "2025"]] for k, lbl in LINE_LABELS}

# ============================ CALCUL ============================
hyp = {k: ss[f"hyp_{k}"] for k in E.SCENARIOS[scen].keys()}
val = dict(wacc=wacc, g=gg, mult=mult)
res = E.compute_model(hist=hist, hyp=hyp, val=val)
L, R, SC = res["lines"], res["ratios"], res["score"]
YRS = res["years"]

# ============================ EN-TÊTE ============================
st.markdown('<div class="imc-band">📊 Diagnostic Financier & Pilotage Stratégique</div>', unsafe_allow_html=True)
st.markdown(f'<div class="imc-sub">Scénario : <b>{scen}</b> &nbsp;•&nbsp; Secteur : {sector} &nbsp;•&nbsp; Outil IMC — Nizar SALAH</div>', unsafe_allow_html=True)
st.write("")

tabs = st.tabs(["📊 Dashboard", "📈 Ratios", "🗓️ Prévision mensuelle", "🎯 Simulation",
                "💰 Valorisation", "🤝 Conseil IMC"])

# ---------------------------- DASHBOARD ----------------------------
with tabs[0]:
    c1, c2 = st.columns([1, 1.3])
    with c1:
        col = GREEN if SC["global_"] >= 65 else (AMBER if SC["global_"] >= 50 else RED)
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=SC["global_"],
            number={"suffix": " / 100", "font": {"size": 34, "color": NAVY}},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": col},
                   "steps": [{"range": [0, 50], "color": RED_BG},
                             {"range": [50, 65], "color": AMBER_BG},
                             {"range": [65, 100], "color": GREEN_BG}]}))
        fig.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=0),
                          title={"text": f"Score de santé — <b>{SC['note']}</b>", "font": {"color": NAVY}})
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.markdown("##### Détail du score")
        s1, s2, s3 = st.columns(3)
        s1.metric("Rentabilité", f"{SC['rent']}/100")
        s2.metric("Liquidité", f"{SC['liq']}/100")
        s3.metric("Structure", f"{SC['struct']}/100")
        z = res["zscore"]
        st.markdown("##### Risque de défaillance (Altman Z'')")
        zc1, zc2 = st.columns([1, 2])
        zc1.metric("Z''-score N+1", num(z["n1"]))
        zc2.markdown(f"### {z['zone_n1'][0]}")

    st.markdown("##### Indicateurs clés — projection 2026 (N+1)")
    k = st.columns(6)
    k[0].metric("Chiffre d'affaires", dt(L["ca"][3]))
    k[1].metric("EBE / EBITDA", dt(L["ebe"][3]))
    k[2].metric("Résultat net", dt(L["rn"][3]))
    k[3].metric("Trésorerie nette", dt(L["treso"][3]))
    k[4].metric("Marge d'EBE", pct(R["ebe"][3]))
    k[5].metric("Capacité remb.", num(R["cap"][3], " ans"))

    st.markdown("##### 🚨 Top 5 alertes & recommandations")
    for state, txt in res["alerts"]:
        st.markdown(alert_html(state, txt), unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        for key, nm in [("ca", "CA"), ("ebe", "EBE"), ("treso", "Trésorerie nette")]:
            fig.add_trace(go.Scatter(x=YRS, y=L[key], mode="lines+markers", name=nm))
        fig.update_layout(height=300, title="CA · EBE · Trésorerie (DT)", margin=dict(t=40, b=0),
                          legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch")
    with g2:
        fig = go.Figure()
        for key, nm in [("mb", "Marge brute"), ("ebe", "Marge EBE"), ("net", "Marge nette")]:
            fig.add_trace(go.Scatter(x=YRS, y=[v*100 for v in R[key]], mode="lines+markers", name=nm))
        fig.update_layout(height=300, title="Marges (%)", margin=dict(t=40, b=0),
                          yaxis_ticksuffix="%", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch")

# ---------------------------- RATIOS ----------------------------
with tabs[1]:
    groups = [
        ("Rentabilité & performance", [("mb","Marge brute",pct),("ebe","Marge EBE",pct),("net","Marge nette",pct),
            ("roe","ROE",pct),("roce","ROCE",pct),("pm","Point mort (j)",lambda v:num(v,' j'))]),
        ("Liquidité & BFR", [("lg","Liquidité générale",lambda v:num(v)),("lr","Liquidité réduite",lambda v:num(v)),
            ("treso","Trésorerie nette",dt),("dso","DSO",lambda v:num(v,' j')),("dpo","DPO",lambda v:num(v,' j')),
            ("dio","DIO",lambda v:num(v,' j')),("ccc","CCC",lambda v:num(v,' j'))]),
        ("Structure & solvabilité", [("auto","Autonomie financière",pct),("cap","Capacité remb. (ans)",lambda v:num(v,' ans')),
            ("gear","Gearing",lambda v:num(v)),("cov","Couverture frais fin.",lambda v:num(v,'x'))]),
        ("Ratios complémentaires", [("va_ca","Taux de VA",pct),("ms_va","Masse sal. / VA",pct),
            ("rot","Rotation de l'actif",lambda v:num(v,'x')),("bfrj","BFR en jours de CA",lambda v:num(v,' j')),
            ("cafca","CAF / CA",pct),("endet","Endettement global",pct)]),
    ]
    for title, rows in groups:
        st.markdown(f"##### {title}")
        data = {}
        statut_col = []
        idx = []
        for key, lbl, f in rows:
            idx.append(lbl)
            for t, y in enumerate(YRS):
                data.setdefault(y, []).append(f(R[key][t]))
            statut_col.append(E.statut(key, R[key][3]) if key in E.TH else "")
        df = pd.DataFrame(data, index=idx)
        df["Statut N+1"] = statut_col
        st.dataframe(df, width="stretch")

    st.markdown("##### Profil vs secteur (N+1) — base 100 = niveau sectoriel")
    radar = [("Marge EBE","ebe","up"),("ROCE","roce","up"),("Autonomie fin.","auto","up"),
             ("Couverture","cov","up"),("Délai client (DSO)","dso","down"),("Rotation stock (DIO)","dio","down")]
    cats, vals = [], []
    for lbl, key, d in radar:
        b = E.bench_of(key, sector)
        v = R[key][3]
        perf = min(150, (v/b*100) if d == "up" else (b/v*100)) if (b and v) else 0
        cats.append(lbl); vals.append(perf)
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=cats+[cats[0]], fill="toself",
                                  name="Ton entreprise", line_color=TURQ))
    fig.add_trace(go.Scatterpolar(r=[100]*(len(cats)+1), theta=cats+[cats[0]], name="Niveau secteur",
                                  line=dict(color=GOLD, dash="dot")))
    fig.update_layout(height=380, polar=dict(radialaxis=dict(range=[0, 150])),
                      legend=dict(orientation="h", y=-0.1), margin=dict(t=20))
    st.plotly_chart(fig, width="stretch")

# ---------------------------- PRÉVISION MENSUELLE ----------------------------
with tabs[2]:
    m = E.compute_monthly(res)
    k = st.columns(3)
    k[0].metric("Trésorerie minimale", dt(m["tmin"]), help="Point bas de l'année")
    k[1].metric("Mois du point bas", m["tmin_month"])
    k[2].metric("Mois en tension (< 0)", f"{m['n_neg']} mois")
    colors = [RED if x < 0 else TURQ for x in m["tfin"]]
    fig = go.Figure(go.Bar(x=m["months"], y=m["tfin"], marker_color=colors))
    fig.update_layout(height=320, title="Trésorerie fin de mois (DT)", margin=dict(t=40, b=0))
    st.plotly_chart(fig, width="stretch")
    dfm = pd.DataFrame({
        "Encaissements": [dt(x) for x in m["enc"]],
        "Décaissements": [dt(x) for x in m["dec"]],
        "Solde": [dt(x) for x in m["solde"]],
        "Trésorerie fin": [dt(x) for x in m["tfin"]],
    }, index=m["months"]).T
    st.dataframe(dfm, width="stretch")
    c1, c2 = st.columns(2)
    c1.metric("Trésorerie fin décembre (mensuel)", dt(m["fin_dec"]))
    c2.metric("Trésorerie nette N+1 (bilan annuel)", dt(m["treso_annual"]))
    st.caption("Écart normal : créances/dettes de clôture non encore encaissées/payées au 31/12. "
               "Hypothèses : HT, charges fixes/IS/CapEx lissés sur 12 mois, décalages = DSO/DPO arrondis au mois.")

# ---------------------------- SIMULATION ----------------------------
with tabs[3]:
    st.markdown("##### Analyse « Et si… » — impact sur la trésorerie N+1")
    c = st.columns(3)
    d_dso = c[0].slider("Δ DSO (jours)", -30, 60, 15, 1)
    d_marge = c[1].slider("Δ marge brute (pts)", -0.10, 0.10, -0.03, 0.01, format="%.0f%%")
    d_croiss = c[2].slider("Δ croissance CA (pts)", -0.20, 0.20, -0.05, 0.01, format="%.0f%%")
    wi = E.whatif(res, d_dso=d_dso, d_marge=d_marge, d_croiss=d_croiss)
    k = st.columns(3)
    k[0].metric("Trésorerie N+1 — référence", dt(wi["base"]))
    k[1].metric("Trésorerie N+1 — stressée", dt(wi["stressed"]))
    k[2].metric("Impact", dt(wi["impact"]), delta=dt(wi["impact"]))

    st.markdown("##### Matrice de sensibilité — Trésorerie N+1 (croissance × marge)")
    mx = E.sensitivity_matrix(res)
    Z = mx["Z"]
    fig = px.imshow([[round(v) for v in row] for row in Z],
                    x=[pct(m) for m in mx["margins"]], y=[pct(g) for g in mx["growths"]],
                    color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
                    aspect="auto", text_auto=True,
                    labels=dict(x="Marge brute", y="Croissance CA", color="Trésorerie (DT)"))
    fig.update_layout(height=380, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Vert = trésorerie confortable · Rouge = tension. La frontière orange ≈ point d'équilibre (trésorerie nulle).")

# ---------------------------- VALORISATION ----------------------------
with tabs[4]:
    v = res["valo"]
    st.markdown("##### Estimation de la valeur des capitaux propres")
    k = st.columns(3)
    k[0].metric("Estimation basse", dt(v["low"]))
    k[1].metric("⭐ Valorisation moyenne", dt(v["avg"]))
    k[2].metric("Estimation haute", dt(v["high"]))
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Méthode 1 — DCF (flux actualisés)**")
        st.dataframe(pd.DataFrame({
            "Valeur": [dt(v["fcf1"]), dt(v["fcf2"]), dt(v["vt"]), dt(v["ev_dcf"]),
                       dt(v["net_debt"]), dt(v["eq_dcf"])]},
            index=["FCF 2026", "FCF 2027", "Valeur terminale", "Valeur d'entreprise (EV)",
                   "(–) Dette nette", "= Capitaux propres"]), width="stretch")
    with c2:
        st.markdown("**Méthode 2 — Multiple d'EBE**")
        st.dataframe(pd.DataFrame({
            "Valeur": [dt(v["ebe_n"]), num(mult, "x"), dt(v["ev_mult"]), dt(v["net_debt"]), dt(v["eq_mult"])]},
            index=["EBE 2025", "Multiple", "Valeur d'entreprise (EV)", "(–) Dette nette", "= Capitaux propres"]),
            width="stretch")
    fig = go.Figure(go.Bar(x=["DCF", "Multiple d'EBE", "Moyenne retenue"],
                           y=[v["eq_dcf"], v["eq_mult"], v["avg"]],
                           marker_color=[TURQ, TURQ, NAVY]))
    fig.update_layout(height=300, title="Valeur des capitaux propres (DT)", margin=dict(t=40))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Hypothèses : WACC {pct(wacc)}, g {pct(gg)}, multiple {num(mult,'x')}. Condition : WACC > g.")

# ---------------------------- CONSEIL IMC ----------------------------
with tabs[5]:
    st.markdown("##### 🤝 Consultation selon votre cas — recommandations en temps réel")
    st.caption("Ce diagnostic, vous l'avez fait seul. L'étape suivante — le plan d'action et sa mise en œuvre — "
               "est le métier d'IMC, sans la lourdeur ni les honoraires d'un grand cabinet.")
    reco = pd.DataFrame(res["reco"], columns=["Domaine", "État", "Constat", "Mission de conseil IMC", "Format", "Indicatif"])
    st.dataframe(reco, width="stretch", hide_index=True)

    st.markdown("##### 💼 Grille tarifaire (indicative, HT, en DT)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**A. Missions one-shot**")
        st.table(pd.DataFrame({
            "DT": ["1 200 – 1 800", "1 500 – 3 000", "1 800 – 3 000", "2 000 – 3 500", "2 500 – 4 500", "3 500 – 6 000"]},
            index=["Diagnostic 360°", "Business plan", "BFR & trésorerie", "Structure & financement",
                   "Valorisation", "Redressement"]))
    with c2:
        st.markdown("**B. Accompagnement / mois**")
        st.table(pd.DataFrame({
            "DT/mois": ["300 – 500", "500 – 900", "1 000 – 1 800"]},
            index=["Pilotage", "Conseil Standard", "DAF externalisé"]))
    with c3:
        st.markdown("**C. À la carte**")
        st.table(pd.DataFrame({
            "Tarif": ["500 – 800 DT/j", "300 – 450 DT"]},
            index=["TJM sur mesure", "Audit / avis (½ j)"]))

    st.markdown('<div class="cta">➡️ Consultation selon votre cas — parlons de votre diagnostic.</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="coord">Nizar SALAH — IMC  •  inmycontacts@gmail.com  •  WhatsApp +216 24 423 506  •  '
                'linkedin.com/in/nizar-salah-7ab3b9125</div>', unsafe_allow_html=True)
