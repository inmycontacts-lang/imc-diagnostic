# -*- coding: utf-8 -*-
"""Rapport PDF du Diagnostic Stratégique 360° IMC (fpdf2, police unicode DejaVu)."""
import os
from datetime import datetime
from fpdf import FPDF

HERE = os.path.dirname(__file__)
FONT_R = os.path.join(HERE, "DejaVuSans.ttf")
FONT_B = os.path.join(HERE, "DejaVuSans-Bold.ttf")
LOGO = os.path.join(HERE, "logo_imc.png")

NAVY = (27, 42, 73); TURQ = (61, 185, 187); GOLD = (201, 169, 97)
GREEN = (30, 126, 52); AMBER = (156, 101, 0); RED = (176, 42, 55)
GREY = (90, 100, 115); LIGHT = (244, 246, 249)


def _maturity(score):
    if score >= 80: return "Excellent", GREEN
    if score >= 60: return "Correct", TURQ
    if score >= 40: return "Fragile", AMBER
    return "Critique", RED


class PDF(FPDF):
    def header(self):
        pass
    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*GREY)
        self.cell(0, 5, "In My Contacts (IMC) — Diagnostic Stratégique 360°  ·  "
                        "inmycontacts@gmail.com  ·  +216 24 423 506", align="C")
        self.set_y(-10)
        self.cell(0, 5, "Page %s" % self.page_no(), align="C")


def build_pdf(lead, res360, recos):
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("DejaVu", "", FONT_R)
    pdf.add_font("DejaVu", "B", FONT_B)
    pdf.add_page()
    W = pdf.epw  # largeur utile

    # --- bandeau navy
    pdf.set_fill_color(*NAVY); pdf.rect(0, 0, 210, 32, "F")
    try:
        pdf.image(LOGO, x=12, y=8, h=16)
    except Exception:
        pass
    pdf.set_xy(70, 10); pdf.set_font("DejaVu", "B", 15); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "Diagnostic Stratégique 360°")
    pdf.set_xy(70, 19); pdf.set_font("DejaVu", "", 9); pdf.set_text_color(200, 208, 220)
    pdf.cell(0, 6, "Par In My Contacts (IMC) — Nizar SALAH")
    pdf.ln(24)

    # --- infos client
    pdf.set_text_color(*GREY); pdf.set_font("DejaVu", "", 9)
    nom = ("%s %s" % (lead.get("prenom", ""), lead.get("nom", ""))).strip()
    pdf.cell(0, 6, "Entreprise : %s   ·   Contact : %s   ·   Date : %s" % (
        lead.get("entreprise", "—"), nom or "—", datetime.now().strftime("%d/%m/%Y")))
    pdf.ln(9)

    # --- score global
    g = res360["global"]; lab, col = _maturity(g)
    pdf.set_fill_color(*LIGHT); pdf.rect(pdf.l_margin, pdf.get_y(), W, 20, "F")
    pdf.set_xy(pdf.l_margin + 4, pdf.get_y() + 4)
    pdf.set_font("DejaVu", "B", 22); pdf.set_text_color(*NAVY)
    pdf.cell(42, 12, "%d/100" % g)
    pdf.set_xy(pdf.l_margin + 50, pdf.get_y())
    pdf.set_font("DejaVu", "B", 12); pdf.set_text_color(*col)
    pdf.cell(0, 6, "Maturité globale : %s" % lab)
    pdf.set_xy(pdf.l_margin + 50, pdf.get_y() + 7)
    pdf.set_font("DejaVu", "", 8); pdf.set_text_color(*GREY)
    pdf.cell(0, 5, "Moyenne des 6 piliers stratégiques évalués")
    pdf.ln(16)

    # --- tableau des 6 piliers
    pdf.set_font("DejaVu", "B", 11); pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "Maturité par pilier"); pdf.ln(9)
    pdf.set_font("DejaVu", "B", 8); pdf.set_text_color(255, 255, 255); pdf.set_fill_color(*NAVY)
    pdf.cell(W * 0.60, 7, "  Pilier", fill=True)
    pdf.cell(W * 0.18, 7, "Score", align="C", fill=True)
    pdf.cell(W * 0.22, 7, "Maturité", align="C", fill=True); pdf.ln(7)
    for i, r in enumerate(res360["pillars"]):
        lab, col = _maturity(r["score"])
        if i % 2 == 0:
            pdf.set_fill_color(248, 250, 252); fill = True
        else:
            fill = False
        pdf.set_font("DejaVu", "", 8); pdf.set_text_color(40, 50, 70)
        pdf.cell(W * 0.60, 7, "  " + r["nom"], fill=fill)
        pdf.set_font("DejaVu", "B", 8)
        pdf.cell(W * 0.18, 7, "%d %%" % r["score"], align="C", fill=fill)
        pdf.set_text_color(*col)
        pdf.cell(W * 0.22, 7, lab, align="C", fill=fill); pdf.ln(7)
    pdf.ln(6)

    # --- recommandations IMC
    pdf.set_font("DejaVu", "B", 11); pdf.set_text_color(*NAVY)
    pdf.cell(0, 8, "Recommandations prioritaires — comment IMC peut vous aider"); pdf.ln(9)
    if not recos:
        pdf.set_font("DejaVu", "", 9); pdf.set_text_color(*GREEN)
        pdf.multi_cell(W, 6, "Tous vos piliers sont au-dessus du seuil critique. "
                             "IMC peut vous accompagner pour passer de « correct » à « excellent » et "
                             "structurer votre croissance.")
    else:
        for nom, icon, score, services in recos:
            lab, col = _maturity(score)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("DejaVu", "B", 9); pdf.set_text_color(*col)
            pdf.multi_cell(W, 6, "%s — %d %% (%s)" % (nom, score, lab),
                           new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("DejaVu", "", 8.5); pdf.set_text_color(40, 50, 70)
            for s in services:
                pdf.set_x(pdf.l_margin + 6)
                pdf.multi_cell(W - 6, 5.5, "•  " + s, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # --- CTA
    pdf.ln(2)
    y = pdf.get_y()
    if y > 250:
        pdf.add_page(); y = pdf.get_y()
    pdf.set_fill_color(*NAVY); pdf.rect(pdf.l_margin, y, W, 22, "F")
    pdf.set_xy(pdf.l_margin + 5, y + 4)
    pdf.set_font("DejaVu", "B", 10); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 6, "Passez à l'action avec un expert In My Contacts")
    pdf.set_xy(pdf.l_margin + 5, y + 12)
    pdf.set_font("DejaVu", "", 8.5); pdf.set_text_color(*GOLD)
    pdf.cell(0, 6, "inmycontacts@gmail.com   ·   WhatsApp +216 24 423 506   ·   imc-diagnostic.streamlit.app")

    out = pdf.output()
    return bytes(out)
