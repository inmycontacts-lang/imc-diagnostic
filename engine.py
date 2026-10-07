# -*- coding: utf-8 -*-
"""
MOTEUR FINANCIER — Outil de Diagnostic Financier IMC
Réimplémentation Python native du modèle Excel v3.1 (calculs en direct).
Aucune dépendance Streamlit : 100% testable en isolation.
Auteur : Nizar SALAH — IMC
"""
from copy import deepcopy

YEARS = ["2023", "2024", "2025", "2026 (P)", "2027 (P)"]  # 0..4 ; N=2(2025), N+1=3

# ----------------------------------------------------------------------------
# Données d'exemple (PME services) — modifiables dans l'interface
# ----------------------------------------------------------------------------
DEFAULT_HIST = dict(
    ca=[980000, 1100000, 1250000],
    ach=[441000, 495000, 562500],
    cext=[180000, 195000, 210000],
    ms=[260000, 295000, 330000],
    dot=[45000, 50000, 55000],
    chfin=[18000, 16000, 22000],
    is_=[9500, 12000, 10500],
    ai=[280000, 300000, 320000],
    stk=[70000, 82000, 95000],
    cre=[150000, 175000, 205000],
    four=[120000, 130000, 140000],
    cp=[300000, 345000, 380000],
    df=[180000, 180000, 260000],
    capex=[60000, 70000, 80000],
    emp=[0, 0, 120000],
    remb=[40000, 45000, 50000],
    div=[0, 0, 0],
)

# Hypothèses par scénario
SCENARIOS = {
    "Cas de Base": dict(croiss=0.10, marge=0.55, evolCF=0.05, evolMS=0.06, dso=55, dpo=45,
                        dio=40, capex=80000, duree=5, emp=0, remb=55000, tint=0.08, tdiv=0.0,
                        tis=0.15, bfrc=45),
    "Optimiste":  dict(croiss=0.18, marge=0.57, evolCF=0.04, evolMS=0.05, dso=45, dpo=55,
                        dio=30, capex=120000, duree=5, emp=100000, remb=55000, tint=0.07, tdiv=0.20,
                        tis=0.15, bfrc=35),
    "Dégradé":    dict(croiss=-0.05, marge=0.50, evolCF=0.08, evolMS=0.09, dso=70, dpo=35,
                        dio=55, capex=40000, duree=5, emp=0, remb=55000, tint=0.10, tdiv=0.0,
                        tis=0.15, bfrc=45),
}

# Benchmarks sectoriels : [Services, Commerce, Industrie, BTP]
SECTORS = ["Services", "Commerce / Négoce", "Industrie", "BTP / Construction"]
BENCH = {
    "mb":[0.60,0.30,0.35,0.28], "ebe":[0.15,0.08,0.12,0.09], "net":[0.08,0.03,0.05,0.03],
    "roe":[0.15,0.12,0.12,0.10], "roce":[0.12,0.10,0.10,0.08], "lg":[1.30,1.20,1.40,1.20],
    "dso":[45,30,60,75], "dpo":[45,45,60,60], "dio":[20,60,75,45], "ccc":[20,45,75,60],
    "auto":[0.40,0.30,0.35,0.25], "cap":[2.0,2.5,3.0,3.0], "gear":[1.0,1.2,1.5,1.5], "cov":[6,4,4,3],
}

# Valorisation (défauts)
DEFAULT_VAL = dict(wacc=0.12, g=0.02, mult=5.0)


def sdiv(a, b):
    return a / b if b else 0.0


def bench_of(key, sector):
    return BENCH[key][SECTORS.index(sector)]


# ----------------------------------------------------------------------------
# MOTEUR PRINCIPAL
# ----------------------------------------------------------------------------
def compute_model(hist=None, hyp=None, val=None):
    H = deepcopy(DEFAULT_HIST if hist is None else hist)
    h = deepcopy(SCENARIOS["Cas de Base"] if hyp is None else hyp)
    V = deepcopy(DEFAULT_VAL if val is None else val)

    n = 5
    def arr(key):
        a = list(H[key]) + [0.0, 0.0]
        return a
    ca, ach, cext, ms, dot, chfin, is_ = (arr(k) for k in ["ca","ach","cext","ms","dot","chfin","is_"])
    ai, stk, cre, four, cp, df = (arr(k) for k in ["ai","stk","cre","four","cp","df"])
    capex, emp, remb, div = (arr(k) for k in ["capex","emp","remb","div"])

    # projections N+1, N+2  (ordre de dépendance : dette AVANT charges financières)
    for t in (3, 4):
        p = t - 1
        ca[t]    = ca[p] * (1 + h["croiss"])
        ach[t]   = ca[t] * (1 - h["marge"])
        cext[t]  = cext[p] * (1 + h["evolCF"])
        ms[t]    = ms[p] * (1 + h["evolMS"])
        capex[t] = h["capex"]; emp[t] = h["emp"]; remb[t] = h["remb"]
        dot[t]   = dot[p] + sdiv(capex[t], h["duree"])
        df[t]    = df[p] + emp[t] - remb[t]      # dette financière (indépendante du résultat)
        chfin[t] = df[p] * h["tint"]             # intérêts sur dette d'ouverture

    # dérivés (toutes années)
    mb=[0]*n; va=[0]*n; ebe=[0]*n; rex=[0]*n; rcai=[0]*n; rn=[0]*n
    bfr=[0]*n; treso=[0]*n; tot=[0]*n; caf=[0]*n
    for t in range(n):
        mb[t]  = ca[t] - ach[t]
        va[t]  = mb[t] - cext[t]
        ebe[t] = va[t] - ms[t]
        rex[t] = ebe[t] - dot[t]
        rcai[t]= rex[t] - chfin[t]
        if t >= 3:
            is_[t] = max(0, rcai[t] * h["tis"])
            div[t] = h["tdiv"] * (rcai[t] - is_[t])
        rn[t]  = rcai[t] - is_[t]
    # bilan projeté (ordre dépendant)
    for t in (3, 4):
        p = t - 1
        ai[t]   = ai[p] + capex[t] - dot[t]
        stk[t]  = h["dio"] * ach[t] / 365
        cre[t]  = h["dso"] * ca[t] / 365
        four[t] = h["dpo"] * ach[t] / 365
        cp[t]   = cp[p] + rn[t] - div[t]
    for t in range(n):
        bfr[t]   = stk[t] + cre[t] - four[t]
        treso[t] = cp[t] + df[t] - ai[t] - bfr[t]
        tot[t]   = ai[t] + bfr[t] + max(treso[t], 0)
        caf[t]   = rn[t] + dot[t]

    # TFT
    dbfr=[0]*n; fexp=[0]*n; finv=[0]*n; ffin=[0]*n; dtre=[0]*n
    for t in range(n):
        finv[t] = -capex[t]
        ffin[t] = emp[t] - remb[t] - div[t]
        if t >= 1:
            dbfr[t] = bfr[t] - bfr[t-1]
            fexp[t] = caf[t] - dbfr[t]
            dtre[t] = fexp[t] + finv[t] + ffin[t]

    # RATIOS (toutes années)
    def R():
        return [0.0]*n
    ratios = {}
    ratios["mb"]   = [sdiv(mb[t], ca[t]) for t in range(n)]
    ratios["ebe"]  = [sdiv(ebe[t], ca[t]) for t in range(n)]
    ratios["net"]  = [sdiv(rn[t], ca[t]) for t in range(n)]
    ratios["roe"]  = [sdiv(rn[t], cp[t]) for t in range(n)]
    ratios["roce"] = [sdiv(rex[t], cp[t]+df[t]) for t in range(n)]
    ratios["sr"]   = [sdiv(cext[t]+ms[t]+dot[t], sdiv(mb[t], ca[t])) if ca[t] and mb[t] else 0 for t in range(n)]
    ratios["pm"]   = [sdiv(ratios["sr"][t], ca[t])*365 for t in range(n)]
    ratios["lg"]   = [sdiv(stk[t]+cre[t]+max(treso[t],0), four[t]+max(-treso[t],0)) for t in range(n)]
    ratios["lr"]   = [sdiv(cre[t]+max(treso[t],0), four[t]+max(-treso[t],0)) for t in range(n)]
    ratios["li"]   = [sdiv(max(treso[t],0), four[t]+max(-treso[t],0)) for t in range(n)]
    ratios["frng"] = [cp[t]+df[t]-ai[t] for t in range(n)]
    ratios["bfr"]  = [bfr[t] for t in range(n)]
    ratios["treso"]= [treso[t] for t in range(n)]
    ratios["dso"]  = [sdiv(cre[t], ca[t])*365 for t in range(n)]
    ratios["dpo"]  = [sdiv(four[t], ach[t])*365 for t in range(n)]
    ratios["dio"]  = [sdiv(stk[t], ach[t])*365 for t in range(n)]
    ratios["ccc"]  = [ratios["dso"][t]+ratios["dio"][t]-ratios["dpo"][t] for t in range(n)]
    ratios["auto"] = [sdiv(cp[t], tot[t]) for t in range(n)]
    ratios["cap"]  = [sdiv(df[t]-max(treso[t],0), ebe[t]) for t in range(n)]
    ratios["gear"] = [sdiv(df[t]-max(treso[t],0), cp[t]) for t in range(n)]
    ratios["cov"]  = [sdiv(rex[t], chfin[t]) for t in range(n)]
    # complémentaires
    ratios["va_ca"]= [sdiv(va[t], ca[t]) for t in range(n)]
    ratios["ms_va"]= [sdiv(ms[t], va[t]) for t in range(n)]
    ratios["rot"]  = [sdiv(ca[t], tot[t]) for t in range(n)]
    ratios["bfrj"] = [sdiv(bfr[t], ca[t])*365 for t in range(n)]
    ratios["cafca"]= [sdiv(caf[t], ca[t]) for t in range(n)]
    ratios["endet"]= [sdiv(df[t]+four[t]+max(-treso[t],0), tot[t]) for t in range(n)]
    ratios["intens"]=[sdiv(ai[t], ca[t]) for t in range(n)]

    # SCORE (N+1 = index 3)
    i = 3
    def pu(x, a, b): return 100 if x >= a else (60 if x >= b else 20)
    def pd(x, a, b): return 100 if x <= a else (60 if x <= b else 20)
    s_rent = round((pu(ratios["ebe"][i],0.12,0.07)+pu(ratios["net"][i],0.05,0.02)+pu(ratios["roce"][i],0.12,0.06))/3)
    tre_pt = 100 if treso[i] >= 0 else (50 if treso[i] >= -0.05*ca[i] else 10)
    s_liq  = round((pu(ratios["lg"][i],1.5,1.0)+tre_pt+pd(ratios["ccc"][i],30,60))/3)
    s_str  = round((pu(ratios["auto"][i],0.40,0.25)+pd(ratios["cap"][i],2,3.5)+pd(ratios["gear"][i],1,2)+pu(ratios["cov"][i],5,2))/4)
    score  = round(0.35*s_rent + 0.30*s_liq + 0.35*s_str)
    note   = "EXCELLENT" if score>=80 else ("BON" if score>=65 else ("FRAGILE" if score>=50 else "CRITIQUE"))

    # Z''-score (N=2 et N+1=3)
    def zscore(t):
        x1 = sdiv(bfr[t]+treso[t], tot[t])
        x2 = sdiv(rn[t], tot[t])
        x3 = sdiv(rex[t], tot[t])
        x4 = sdiv(cp[t], df[t]+four[t]+max(-treso[t],0))
        return 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4
    z_n, z_n1 = zscore(2), zscore(3)
    def zzone(z): return ("🟢 Zone sûre", "safe") if z>2.6 else (("🟡 Zone grise","warn") if z>=1.1 else ("🔴 Détresse","danger"))

    # VALORISATION
    fcf1 = fexp[3]+finv[3]; fcf2 = fexp[4]+finv[4]
    ebe_n = ebe[2]; net_debt = df[2]-max(treso[2],0)
    wacc, gg, mult = V["wacc"], V["g"], V["mult"]
    vt = sdiv(fcf2*(1+gg), (wacc-gg)) if wacc > gg else 0
    ev_dcf = sdiv(fcf1,(1+wacc)) + sdiv(fcf2,(1+wacc)**2) + sdiv(vt,(1+wacc)**2)
    eq_dcf = ev_dcf - net_debt
    ev_mult = ebe_n*mult; eq_mult = ev_mult - net_debt
    val_low, val_high = min(eq_dcf, eq_mult), max(eq_dcf, eq_mult)
    val_avg = (eq_dcf+eq_mult)/2

    res = dict(
        years=YEARS, hyp=h, val=V,
        lines=dict(ca=ca,ach=ach,mb=mb,cext=cext,va=va,ms=ms,ebe=ebe,dot=dot,rex=rex,chfin=chfin,
                   rcai=rcai,is_=is_,rn=rn,ai=ai,stk=stk,cre=cre,four=four,bfr=bfr,cp=cp,df=df,
                   treso=treso,tot=tot,caf=caf,capex=capex,emp=emp,remb=remb,div=div,
                   dbfr=dbfr,fexp=fexp,finv=finv,ffin=ffin,dtre=dtre),
        ratios=ratios,
        score=dict(global_=score, rent=s_rent, liq=s_liq, struct=s_str, note=note),
        zscore=dict(n=z_n, n1=z_n1, zone_n=zzone(z_n), zone_n1=zzone(z_n1)),
        valo=dict(fcf1=fcf1,fcf2=fcf2,ebe_n=ebe_n,net_debt=net_debt,vt=vt,ev_dcf=ev_dcf,eq_dcf=eq_dcf,
                  ev_mult=ev_mult,eq_mult=eq_mult,low=val_low,high=val_high,avg=val_avg),
    )
    res["alerts"] = build_alerts(res)
    res["reco"] = build_reco(res)
    return res


# seuils de statut (N+1) : (good, warn, direction)
TH = {
 "mb":(0.50,0.35,"up"),"ebe":(0.12,0.07,"up"),"net":(0.05,0.02,"up"),
 "roe":(0.12,0.06,"up"),"roce":(0.12,0.06,"up"),"pm":(270,330,"down"),
 "lg":(1.5,1.0,"up"),"lr":(1.0,0.7,"up"),"li":(0.3,0.1,"up"),
 "treso":(0.0001,-0.0001,"up"),"dso":(45,60,"down"),"dpo":(45,30,"up"),
 "dio":(45,60,"down"),"ccc":(30,60,"down"),
 "auto":(0.40,0.25,"up"),"cap":(2.0,3.5,"down"),"gear":(1.0,2.0,"down"),"cov":(5,2,"up"),
}

def statut(key, value):
    good, warn, d = TH[key]
    if d == "up":
        return "🟢" if value >= good else ("🟡" if value >= warn else "🔴")
    return "🟢" if value <= good else ("🟡" if value <= warn else "🔴")


def build_alerts(res):
    r = res["ratios"]; L = res["lines"]; i = 3
    tre, cap, dso, ebe, auto, ca = r["treso"][i], r["cap"][i], r["dso"][i], r["ebe"][i], r["auto"][i], L["ca"][i]
    A = []
    if tre < 0:
        A.append(("danger", f"Trésorerie nette négative ({tre:,.0f} DT) : risque de rupture de liquidité."))
    elif tre < 0.05*ca:
        A.append(("warn", "Trésorerie faible (< 5% du CA) : constituer un coussin de sécurité."))
    else:
        A.append(("safe", "Trésorerie nette confortable."))
    if cap > 3.5:
        A.append(("danger", f"Dette lourde : {cap:,.1f} ans d'EBE pour rembourser (seuil 3,5 ans)."))
    elif cap > 2:
        A.append(("warn", f"Endettement à surveiller ({cap:,.1f} ans)."))
    else:
        A.append(("safe", "Capacité de remboursement saine."))
    if dso > 60:
        A.append(("danger", f"Délai clients élevé : {dso:,.0f} j. Ramener à 45 j libérerait ~{(dso-45)*ca/365:,.0f} DT."))
    elif dso > 45:
        A.append(("warn", f"Délai clients à optimiser ({dso:,.0f} j)."))
    else:
        A.append(("safe", "Délai clients maîtrisé."))
    if ebe < 0.08:
        A.append(("danger", f"Rentabilité d'exploitation faible ({ebe:.1%})."))
    elif ebe < 0.15:
        A.append(("warn", f"Marge d'EBE perfectible ({ebe:.1%})."))
    else:
        A.append(("safe", "Rentabilité d'exploitation solide."))
    if auto < 0.25:
        A.append(("danger", f"Structure financière fragile : autonomie {auto:.1%} (seuil 25%)."))
    elif auto < 0.40:
        A.append(("warn", f"Autonomie financière moyenne ({auto:.1%})."))
    else:
        A.append(("safe", "Structure financière solide."))
    return A


def build_reco(res):
    """Matrice conseil IMC : (domaine, état, constat, mission, format)."""
    r = res["ratios"]; L = res["lines"]; i = 3
    tre, ccc, ebe, auto, cap = r["treso"][i], r["ccc"][i], r["ebe"][i], r["auto"][i], r["cap"][i]
    ca = L["ca"][i]; z = res["zscore"]["n1"]; score = res["score"]["global_"]
    out = []
    # Trésorerie & BFR
    if tre < 0:
        e, c = "🔴", "Trésorerie négative : risque de rupture."
    elif ccc > 60 or tre < 0.05*ca:
        e, c = "🟡", ("Cycle d'exploitation long, BFR lourd." if ccc > 60 else "Trésorerie juste, peu de marge.")
    else:
        e, c = "🟢", "Trésorerie et BFR maîtrisés."
    m = ("Optimisation du BFR & plan de trésorerie 13 semaines : relances, négociation fournisseurs, pilotage des stocks."
         if (tre < 0 or ccc > 60) else "Suivi mensuel de trésorerie via tableau de bord dédié.")
    out.append(("Trésorerie & BFR", e, c, m, "One-shot + suivi mensuel", "1 800 – 3 000 DT"))
    # Rentabilité
    if ebe < 0.08: e, c = "🔴", "Rentabilité d'exploitation insuffisante."
    elif ebe < 0.15: e, c = "🟡", "Marge perfectible."
    else: e, c = "🟢", "Rentabilité solide."
    m = ("Diagnostic de rentabilité & structure de coûts : pricing, achats, mix produit/service."
         if ebe < 0.15 else "Optimisation fine des marges et du mix produit.")
    out.append(("Rentabilité", e, c, m, "Mission ponctuelle", "1 200 – 1 800 DT"))
    # Structure
    if auto < 0.25 or cap > 3.5: e, c = "🔴", ("Sous-capitalisation, dépendance à la dette." if auto<0.25 else "Endettement lourd.")
    elif auto < 0.40 or cap > 2: e, c = "🟡", "Structure à consolider."
    else: e, c = "🟢", "Structure financière saine."
    m = ("Conseil en structure financière & recherche de financement : mix dette/fonds propres, dossier bancaire."
         if (auto < 0.40 or cap > 2) else "Veille sur la capacité d'endettement pour financer la croissance.")
    out.append(("Structure financière & financement", e, c, m, "Mission", "2 000 – 3 500 DT"))
    # Défaillance
    if z < 1.1: e, c = "🔴", "Zone de détresse (Z'' < 1,1)."
    elif z < 2.6: e, c = "🟡", "Zone grise à sécuriser."
    else: e, c = "🟢", "Zone sûre."
    m = ("Plan de redressement / sortie de crise : mesures d'urgence, négociation créanciers, retour à l'équilibre."
         if z < 1.1 else ("Sécurisation : renforcement des fonds propres et de la trésorerie." if z < 2.6
         else "Maintien de la discipline financière."))
    out.append(("Risque de défaillance", e, c, m, "Mission dédiée", "3 500 – 6 000 DT"))
    # Croissance
    if score < 50: e, c = "🔴", "Priorité à la consolidation avant d'accélérer."
    elif score < 65: e, c = "🟡", "Base correcte, croissance à structurer."
    else: e, c = "🟢", "Entreprise saine, prête à accélérer."
    m = ("Stabiliser les fondamentaux, puis bâtir un plan d'acquisition." if score < 65
         else "Conseil en croissance & développement commercial : plan d'acquisition + exécution digitale (pont IMC).")
    out.append(("Croissance & développement", e, c, m, "Accompagnement", "dès 500 DT/mois"))
    # Valorisation
    if score >= 65: e, c = "🟢", "Profil valorisable : opportunité à préparer."
    elif score >= 50: e, c = "🟡", "Valorisation à améliorer avant une opération."
    else: e, c = "🔴", "Valorisation fragilisée par la situation."
    m = ("Valorisation & préparation cession/levée : rapport de valorisation, data room, argumentaire."
         if score >= 65 else "Travailler les fondamentaux pour accroître la valeur avant toute opération.")
    out.append(("Valorisation & transmission", e, c, m, "Mission", "2 500 – 4 500 DT"))
    return out


def compute_monthly(res, saison=None):
    """Prévision de trésorerie mensuelle N+1 (12 mois)."""
    L = res["lines"]; h = res["hyp"]
    ca_a = L["ca"][3]
    if saison is None:
        saison = [1/12]*12
    MONTHS = ["Jan","Fév","Mar","Avr","Mai","Juin","Juil","Août","Sep","Oct","Nov","Déc"]
    dec_c = round(h["dso"]/30); dec_f = round(h["dpo"]/30)
    cre_open = L["cre"][2]; four_open = L["four"][2]
    ca_m  = [ca_a*s for s in saison]
    ach_m = [c*(1-h["marge"]) for c in ca_m]
    enc_v, enc_o, pay_a, pay_o = [0.]*12, [0.]*12, [0.]*12, [0.]*12
    for j in range(12):
        enc_v[j] = ca_m[j-dec_c] if (j-dec_c) >= 0 else 0.0
        enc_o[j] = cre_open/max(dec_c,1) if j < max(dec_c,1) else 0.0
        pay_a[j] = ach_m[j-dec_f] if (j-dec_f) >= 0 else 0.0
        pay_o[j] = four_open/max(dec_f,1) if j < max(dec_f,1) else 0.0
    cext_m = L["cext"][3]/12; ms_m = L["ms"][3]/12; chfin_m = L["chfin"][3]/12
    is_m = L["is_"][3]/12; capex_m = L["capex"][3]/12; remb_m = L["remb"][3]/12; div_m = L["div"][3]/12
    enc_tot, dec_tot, solde, tdeb, tfin = [0.]*12,[0.]*12,[0.]*12,[0.]*12,[0.]*12
    treso_start = L["treso"][2]
    for j in range(12):
        enc_tot[j] = enc_v[j]+enc_o[j]
        dec_tot[j] = pay_a[j]+pay_o[j]+cext_m+ms_m+chfin_m+is_m+capex_m+remb_m+div_m
        solde[j]   = enc_tot[j]-dec_tot[j]
        tdeb[j]    = treso_start if j == 0 else tfin[j-1]
        tfin[j]    = tdeb[j]+solde[j]
    return dict(months=MONTHS, ca=ca_m, enc=enc_tot, dec=dec_tot, solde=solde, tfin=tfin,
                tmin=min(tfin), tmin_month=MONTHS[tfin.index(min(tfin))],
                n_neg=sum(1 for x in tfin if x < 0), fin_dec=tfin[-1], treso_annual=L["treso"][3])


def sensitivity_matrix(res, growths=None, margins=None):
    """Trésorerie N+1 en fonction de (croissance CA, marge brute)."""
    L = res["lines"]; h = res["hyp"]
    if growths is None: growths = [-0.10,-0.05,0.0,0.05,0.10,0.15,0.20]
    if margins is None: margins = [0.45,0.50,0.55,0.60,0.65]
    ca_n = L["ca"][2]; cext_n=L["cext"][2]; ms_n=L["ms"][2]; dot_n=L["dot"][2]
    ai_n=L["ai"][2]; cp_n=L["cp"][2]; df_n=L["df"][2]
    cext1 = cext_n*(1+h["evolCF"]); ms1 = ms_n*(1+h["evolMS"])
    dot1  = dot_n + sdiv(h["capex"], h["duree"])
    chfin1= df_n*h["tint"]; ai1 = ai_n + h["capex"] - dot1; df1 = df_n + h["emp"] - h["remb"]
    def treso_of(g, m):
        ca1=ca_n*(1+g); ach1=ca1*(1-m); mb1=ca1*m
        ebe1=mb1-cext1-ms1; rex1=ebe1-dot1; rcai1=rex1-chfin1
        rn1=rcai1-max(0,rcai1*h["tis"])
        bfr1=h["dio"]*ach1/365+h["dso"]*ca1/365-h["dpo"]*ach1/365
        cp1=cp_n+rn1*(1-h["tdiv"])
        return cp1+df1-ai1-bfr1
    Z = [[treso_of(g, m) for m in margins] for g in growths]
    return dict(growths=growths, margins=margins, Z=Z)


def whatif(res, d_dso=0, d_marge=0.0, d_croiss=0.0):
    """Impact 'Et si…' sur la trésorerie N+1."""
    L = res["lines"]; h = res["hyp"]
    base = L["treso"][3]
    ca_n=L["ca"][2]; cext_n=L["cext"][2]; ms_n=L["ms"][2]; dot_n=L["dot"][2]
    ai_n=L["ai"][2]; cp_n=L["cp"][2]; df_n=L["df"][2]
    cext1=cext_n*(1+h["evolCF"]); ms1=ms_n*(1+h["evolMS"]); dot1=dot_n+sdiv(h["capex"],h["duree"])
    chfin1=df_n*h["tint"]; ai1=ai_n+h["capex"]-dot1; df1=df_n+h["emp"]-h["remb"]
    g=h["croiss"]+d_croiss; m=h["marge"]+d_marge; dso=h["dso"]+d_dso
    ca1=ca_n*(1+g); ach1=ca1*(1-m); mb1=ca1*m
    ebe1=mb1-cext1-ms1; rex1=ebe1-dot1; rcai1=rex1-chfin1
    rn1=rcai1-max(0,rcai1*h["tis"])
    bfr1=h["dio"]*ach1/365+dso*ca1/365-h["dpo"]*ach1/365
    cp1=cp_n+rn1*(1-h["tdiv"])
    stressed=cp1+df1-ai1-bfr1
    return dict(base=base, stressed=stressed, impact=stressed-base)


# ============================================================================
# ANALYSE NARRATIVE AUTOMATIQUE (par règles — zéro coût, pas de LLM)
# ============================================================================
def _fr(x, dec=0):
    s = f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s

def build_narrative(res):
    """Génère un commentaire rédigé du diagnostic à partir des chiffres.
    Retourne un dict de sections prêtes à afficher."""
    R = res["ratios"]; L = res["lines"]; i = 3
    sc = res["score"]; z = res["zscore"]; v = res["valo"]
    ca = L["ca"][i]; ebe = L["ebe"][i]; rn = L["rn"][i]; tre = L["treso"][i]
    croiss = res["hyp"]["croiss"]

    note = sc["note"]
    # --- Synthèse d'ouverture
    tone = {"EXCELLENT":"très solide","BON":"saine","FRAGILE":"fragile","CRITIQUE":"préoccupante"}[note]
    synth = (f"Avec un score de santé financière de {sc['global_']}/100 ({note}), "
             f"l'entreprise présente une situation {tone} sur l'exercice projeté (N+1). "
             f"Le chiffre d'affaires atteint {_fr(ca)} DT pour un EBE de {_fr(ebe)} DT "
             f"({_fr(R['ebe'][i]*100,1)} % du CA) et un résultat net de {_fr(rn)} DT. "
             f"Le risque de défaillance (Z''-score d'Altman = {_fr(z['n1'],2)}) situe l'entreprise en {z['zone_n1'][0]}.")

    # --- Forces (statut vert)
    forces = []
    if R["ebe"][i] >= 0.15: forces.append(f"une rentabilité d'exploitation solide ({_fr(R['ebe'][i]*100,1)} % d'EBE)")
    if R["auto"][i] >= 0.40: forces.append(f"une structure financière robuste (autonomie {_fr(R['auto'][i]*100,1)} %)")
    if tre >= 0.05*ca: forces.append(f"une trésorerie confortable ({_fr(tre)} DT)")
    if R["cap"][i] <= 2: forces.append(f"un endettement maîtrisé ({_fr(R['cap'][i],1)} ans d'EBE)")
    if R["cov"][i] >= 5: forces.append(f"des charges financières largement couvertes ({_fr(R['cov'][i],1)}x)")
    if R["roce"][i] >= 0.12: forces.append(f"un bon rendement des capitaux (ROCE {_fr(R['roce'][i]*100,1)} %)")
    if not forces: forces.append("peu de points forts marqués à ce stade — la priorité est au redressement des fondamentaux")

    # --- Vigilances (statut orange/rouge)
    vig = []
    if tre < 0: vig.append(f"🔴 trésorerie nette négative ({_fr(tre)} DT) — risque de rupture de liquidité")
    elif tre < 0.05*ca: vig.append(f"🟡 trésorerie juste ({_fr(tre)} DT, < 5 % du CA)")
    if R["ebe"][i] < 0.08: vig.append(f"🔴 rentabilité d'exploitation insuffisante ({_fr(R['ebe'][i]*100,1)} %)")
    elif R["ebe"][i] < 0.15: vig.append(f"🟡 marge d'EBE perfectible ({_fr(R['ebe'][i]*100,1)} %)")
    if R["dso"][i] > 60: vig.append(f"🔴 délai clients élevé ({_fr(R['dso'][i])} j) — trésorerie immobilisée")
    elif R["dso"][i] > 45: vig.append(f"🟡 délai clients à optimiser ({_fr(R['dso'][i])} j)")
    if R["cap"][i] > 3.5: vig.append(f"🔴 endettement lourd ({_fr(R['cap'][i],1)} ans d'EBE)")
    if R["auto"][i] < 0.25: vig.append(f"🔴 sous-capitalisation (autonomie {_fr(R['auto'][i]*100,1)} %)")
    elif R["auto"][i] < 0.40: vig.append(f"🟡 autonomie financière moyenne ({_fr(R['auto'][i]*100,1)} %)")
    if R["ccc"][i] > 60: vig.append(f"🟡 cycle d'exploitation long ({_fr(R['ccc'][i])} j)")
    if not vig: vig.append("🟢 aucun point de vigilance majeur — les grands équilibres sont respectés")

    # --- Priorités (3 leviers chiffrés tirés du plan d'action)
    prio = []
    gain_dso = max(0, R["dso"][i]-45) * ca / 365
    if gain_dso > 1000:
        prio.append(f"Ramener le délai clients à 45 j libérerait environ {_fr(gain_dso)} DT de trésorerie.")
    if R["ebe"][i] < 0.15:
        prio.append(f"Gagner 2 points de marge brute représenterait ~{_fr(0.02*ca)} DT de marge supplémentaire.")
    if R["cap"][i] > 2.5:
        prio.append("Renégocier la dette (taux/maturité) allégerait la pression sur la trésorerie.")
    if not prio:
        prio.append("Maintenir la discipline actuelle et placer l'excédent de trésorerie.")
        prio.append("Envisager un plan de croissance : les fondamentaux le permettent.")

    # --- Valorisation
    valo_txt = (f"Sur la base des flux projetés, la valeur des capitaux propres est estimée entre "
                f"{_fr(v['low'])} et {_fr(v['high'])} DT (moyenne {_fr(v['avg'])} DT), "
                f"selon les méthodes DCF et multiple d'EBE.")

    # --- Conclusion orientée conseil IMC
    if note in ("EXCELLENT","BON"):
        concl = ("L'entreprise dispose de bases saines pour accélérer. L'enjeu : structurer la croissance "
                 "et valoriser cette performance. IMC peut accompagner le plan de développement et le pilotage.")
    elif note == "FRAGILE":
        concl = ("La situation appelle une consolidation avant toute accélération. "
                 "Un accompagnement sur le BFR et la rentabilité sécuriserait la trajectoire — c'est le cœur du conseil IMC.")
    else:
        concl = ("La situation exige des mesures correctives rapides. Un plan de redressement structuré "
                 "(trésorerie, dette, rentabilité) est prioritaire. IMC peut le bâtir et le piloter avec vous.")

    return dict(synthese=synth, forces=forces, vigilances=vig,
                priorites=prio, valorisation=valo_txt, conclusion=concl)
