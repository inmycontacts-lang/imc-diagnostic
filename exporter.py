# -*- coding: utf-8 -*-
"""
Import / Export Excel pour l'app Diagnostic Financier IMC.
- make_template()  : classeur vierge de saisie (3 ans) à remplir par le dirigeant
- read_template()  : relit ce classeur et renvoie le dict `hist` attendu par engine
- export_report()  : classeur de résultats stylé (Données, Ratios, Score, Valorisation, Synthèse)
Tout est renvoyé en mémoire (BytesIO) pour st.download_button.
"""
import io
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import engine as E

NAVY="1B2A49"; TURQ="3DB9BB"; GOLD="C9A961"; GREY="F4F6F9"; INPUT="E8F0FE"; WHITE="FFFFFF"
FONT="Calibri"
thin=Side(style="thin", color="D5DBE3")
B=Border(left=thin,right=thin,top=thin,bottom=thin)
F_DT='#,##0" DT";(#,##0)" DT";"-"'
F_PCT='0.0%;(0.0%);"-"'

# Lignes de saisie (clé engine -> libellé) — ordre d'affichage
ROWS = [
 ("ca","Chiffre d'affaires"),("ach","Achats consommés / charges variables"),
 ("cext","Charges externes"),("ms","Masse salariale"),("dot","Dotations aux amortissements"),
 ("chfin","Charges financières (intérêts)"),("is_","Impôt sur les bénéfices"),
 ("ai","Actif immobilisé net"),("stk","Stocks"),("cre","Créances clients"),
 ("four","Dettes fournisseurs"),("cp","Capitaux propres"),("df","Dettes financières"),
 ("capex","CapEx (investissements)"),("emp","Nouvel emprunt"),("remb","Remboursement de dette"),
 ("div","Dividendes versés"),
]
YEARS3 = ["2023","2024","2025"]

def _hdr(ws, row, col, text, fill=NAVY, color=WHITE, bold=True, sz=11):
    c=ws.cell(row,col,text); c.font=Font(name=FONT,size=sz,bold=bold,color=color)
    c.fill=PatternFill("solid",fgColor=fill); c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True); c.border=B
    return c

def make_template():
    wb=Workbook(); ws=wb.active; ws.title="Saisie"
    ws.column_dimensions["A"].width=3; ws.column_dimensions["B"].width=42
    for cc in ["C","D","E"]: ws.column_dimensions[cc].width=15
    ws.merge_cells("B1:E1")
    t=ws.cell(1,2,"DIAGNOSTIC FINANCIER IMC — Feuille de saisie"); t.font=Font(name=FONT,size=14,bold=True,color=WHITE)
    t.fill=PatternFill("solid",fgColor=NAVY); t.alignment=Alignment(horizontal="left",vertical="center",indent=1)
    ws.row_dimensions[1].height=28
    ws.merge_cells("B2:E2")
    s=ws.cell(2,2,"Renseignez vos 3 dernières années (en DT). Ne modifiez pas la colonne B.")
    s.font=Font(name=FONT,size=9,italic=True,color="7A8798")
    _hdr(ws,4,2,"Poste")
    for j,y in enumerate(YEARS3): _hdr(ws,4,3+j,y)
    ex = E.DEFAULT_HIST
    for i,(k,lbl) in enumerate(ROWS):
        r=5+i
        c=ws.cell(r,2,lbl); c.font=Font(name=FONT,size=10); c.border=B
        c.alignment=Alignment(horizontal="left",vertical="center",indent=1)
        for j in range(3):
            cell=ws.cell(r,3+j, ex[k][j])  # valeurs d'exemple pré-remplies
            cell.font=Font(name=FONT,size=10,color="1C3A6E"); cell.number_format='#,##0'
            cell.fill=PatternFill("solid",fgColor=INPUT); cell.border=B
            cell.alignment=Alignment(horizontal="right")
    note=ws.cell(5+len(ROWS)+1,2,"Exemple pré-rempli (PME services) — remplacez par vos chiffres, puis réimportez ce fichier dans l'application.")
    note.font=Font(name=FONT,size=9,italic=True,color="7A8798")
    ws.merge_cells(start_row=5+len(ROWS)+1,start_column=2,end_row=5+len(ROWS)+1,end_column=5)
    ws.sheet_view.showGridLines=False
    bio=io.BytesIO(); wb.save(bio); bio.seek(0); return bio

def read_template(file_like):
    """Relit un classeur de saisie et renvoie (hist, msg). hist=None si format invalide."""
    try:
        wb=load_workbook(file_like, data_only=True)
    except Exception as e:
        return None, f"Fichier illisible : {e}"
    ws = wb["Saisie"] if "Saisie" in wb.sheetnames else wb.active
    # retrouver la ligne d'en-tête (celle contenant 'Poste')
    hrow=None
    for r in range(1,12):
        if str(ws.cell(r,2).value).strip().lower()=="poste": hrow=r; break
    if hrow is None: hrow=4
    hist={}
    labels={lbl.lower():k for k,lbl in ROWS}
    read=0
    for r in range(hrow+1, hrow+1+len(ROWS)+3):
        lbl=ws.cell(r,2).value
        if not lbl: continue
        key=labels.get(str(lbl).strip().lower())
        if not key: continue
        vals=[]
        for j in range(3):
            v=ws.cell(r,3+j).value
            try: vals.append(float(v))
            except (TypeError,ValueError): vals.append(0.0)
        hist[key]=vals; read+=1
    missing=[k for k,_ in ROWS if k not in hist]
    for k in missing: hist[k]=list(E.DEFAULT_HIST[k])
    if read < 8:
        return None, "Format non reconnu : utilisez le modèle de saisie téléchargeable dans l'application."
    msg=f"{read}/{len(ROWS)} postes importés."
    if missing: msg+=f" {len(missing)} poste(s) manquant(s) complété(s) par défaut."
    return hist, msg

def export_report(res, scenario, sector):
    wb=Workbook()
    YRS=res["years"]; L=res["lines"]; R=res["ratios"]; sc=res["score"]; z=res["zscore"]; v=res["valo"]
    nar=E.build_narrative(res)

    def style_title(ws, ncols, title, sub=""):
        ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=ncols)
        c=ws.cell(1,1,title); c.font=Font(name=FONT,size=14,bold=True,color=WHITE)
        c.fill=PatternFill("solid",fgColor=NAVY); c.alignment=Alignment(horizontal="left",vertical="center",indent=1)
        ws.row_dimensions[1].height=26
        if sub:
            ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=ncols)
            s=ws.cell(2,1,sub); s.font=Font(name=FONT,size=9,bold=True,italic=True,color=WHITE)
            s.fill=PatternFill("solid",fgColor=GOLD); s.alignment=Alignment(horizontal="left",vertical="center",indent=1)

    # --- Feuille Synthèse
    ws=wb.active; ws.title="Synthèse"
    ws.column_dimensions["A"].width=3; ws.column_dimensions["B"].width=100
    ws.sheet_view.showGridLines=False
    style_title(ws, 3, "DIAGNOSTIC FINANCIER — SYNTHÈSE", f"Scénario : {scenario}  •  Secteur : {sector}  •  IMC — Nizar SALAH")
    r=4
    def block(title, lines, tcol=NAVY):
        nonlocal r
        c=ws.cell(r,2,title); c.font=Font(name=FONT,size=11,bold=True,color=WHITE)
        c.fill=PatternFill("solid",fgColor=tcol); c.alignment=Alignment(horizontal="left",vertical="center",indent=1)
        ws.row_dimensions[r].height=20; r+=1
        for ln in lines:
            cc=ws.cell(r,2,("• "+ln) if not ln.startswith(("🔴","🟡","🟢")) else ln)
            cc.font=Font(name=FONT,size=10); cc.alignment=Alignment(horizontal="left",vertical="top",wrap_text=True)
            ws.row_dimensions[r].height=max(16, 15*(1+len(ln)//95)); r+=1
        r+=1
    tile=ws.cell(r,2,f"Score : {sc['global_']}/100  ({sc['note']})   ·   Z''-score : {E._fr(z['n1'],2)} — {z['zone_n1'][0]}")
    tile.font=Font(name=FONT,size=12,bold=True,color=NAVY); tile.fill=PatternFill("solid",fgColor=GREY)
    tile.border=B; r+=2
    block("SYNTHÈSE", [nar["synthese"]], TURQ)
    block("POINTS FORTS", nar["forces"])
    block("POINTS DE VIGILANCE", nar["vigilances"])
    block("PRIORITÉS", nar["priorites"])
    block("VALORISATION", [nar["valorisation"]])
    block("RECOMMANDATION IMC", [nar["conclusion"]], GOLD)

    # --- Feuille Données
    ws2=wb.create_sheet("Données"); ws2.sheet_view.showGridLines=False
    ws2.column_dimensions["A"].width=3; ws2.column_dimensions["B"].width=38
    for j in range(5): ws2.column_dimensions[chr(67+j)].width=14
    style_title(ws2,7,"DONNÉES FINANCIÈRES","Historique + projections (DT)")
    _hdr(ws2,4,2,"Poste")
    for j,y in enumerate(YRS): _hdr(ws2,4,3+j,y)
    dmap=[("ca","Chiffre d'affaires"),("mb","Marge brute"),("ebe","EBE / EBITDA"),("rex","Résultat d'exploitation"),
          ("rn","Résultat net"),("bfr","BFR"),("treso","Trésorerie nette"),("cp","Capitaux propres"),("df","Dettes financières")]
    for i,(k,lbl) in enumerate(dmap):
        rr=5+i; c=ws2.cell(rr,2,lbl); c.font=Font(name=FONT,size=10,bold=k in("ebe","rn","treso")); c.border=B
        c.alignment=Alignment(horizontal="left",indent=1)
        for j in range(5):
            cell=ws2.cell(rr,3+j, round(L[k][j])); cell.number_format=F_DT; cell.border=B
            cell.font=Font(name=FONT,size=10); cell.alignment=Alignment(horizontal="right")

    # --- Feuille Ratios
    ws3=wb.create_sheet("Ratios"); ws3.sheet_view.showGridLines=False
    ws3.column_dimensions["A"].width=3; ws3.column_dimensions["B"].width=34
    for j in range(5): ws3.column_dimensions[chr(67+j)].width=13
    style_title(ws3,7,"RATIOS FINANCIERS","Sur 5 ans")
    _hdr(ws3,4,2,"Ratio")
    for j,y in enumerate(YRS): _hdr(ws3,4,3+j,y)
    rmap=[("mb","Marge brute",F_PCT),("ebe","Marge EBE",F_PCT),("net","Marge nette",F_PCT),
          ("roce","ROCE",F_PCT),("lg","Liquidité générale",'0.00'),("dso","DSO",'0" j"'),
          ("dpo","DPO",'0" j"'),("dio","DIO",'0" j"'),("ccc","CCC",'0" j"'),
          ("auto","Autonomie financière",F_PCT),("cap","Capacité remb. (ans)",'0.0" ans"'),("cov","Couverture frais fin.",'0.0"x"')]
    for i,(k,lbl,fmt) in enumerate(rmap):
        rr=5+i; c=ws3.cell(rr,2,lbl); c.font=Font(name=FONT,size=10); c.border=B
        c.alignment=Alignment(horizontal="left",indent=1)
        for j in range(5):
            cell=ws3.cell(rr,3+j, R[k][j]); cell.number_format=fmt; cell.border=B
            cell.font=Font(name=FONT,size=10); cell.alignment=Alignment(horizontal="right")

    # --- Feuille Valorisation
    ws4=wb.create_sheet("Valorisation"); ws4.sheet_view.showGridLines=False
    ws4.column_dimensions["A"].width=3; ws4.column_dimensions["B"].width=40; ws4.column_dimensions["C"].width=18
    style_title(ws4,3,"VALORISATION","DCF + multiple d'EBE")
    rows=[("Capitaux propres — DCF",v["eq_dcf"]),("Capitaux propres — multiple d'EBE",v["eq_mult"]),
          ("Estimation basse",v["low"]),("Estimation haute",v["high"]),("Valorisation moyenne retenue",v["avg"])]
    for i,(lbl,val) in enumerate(rows):
        rr=4+i; c=ws4.cell(rr,2,lbl); c.font=Font(name=FONT,size=10,bold=i==4); c.border=B
        c.alignment=Alignment(horizontal="left",indent=1)
        cell=ws4.cell(rr,3,round(val)); cell.number_format=F_DT; cell.border=B
        cell.font=Font(name=FONT,size=11,bold=i==4,color=NAVY); cell.alignment=Alignment(horizontal="right")
        if i==4: cell.fill=PatternFill("solid",fgColor=GREY)

    # tab colors + signature
    for ws_ in wb.worksheets: ws_.sheet_properties.tabColor=NAVY
    sig=ws.cell(r+1,2,"Nizar SALAH — IMC  ·  inmycontacts@gmail.com  ·  +216 24 423 506  ·  imc-diagnostic.streamlit.app")
    sig.font=Font(name=FONT,size=9,bold=True,color=NAVY)

    bio=io.BytesIO(); wb.save(bio); bio.seek(0); return bio
