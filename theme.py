# -*- coding: utf-8 -*-
"""Thème IMC partagé : couleurs, CSS global, helpers de formatage, chemin logo."""
import os

NAVY, TURQ, GOLD = "#1B2A49", "#3DB9BB", "#C9A961"
GREEN, AMBER, RED = "#1E7E34", "#9C6500", "#B02A37"
GREEN_BG, AMBER_BG, RED_BG = "#D4EDDA", "#FFF3CD", "#F8D7DA"
LOGO = os.path.join(os.path.dirname(__file__), "logo_imc.png")
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

CONTACT = ("Nizar SALAH — IMC  •  inmycontacts@gmail.com  •  WhatsApp +216 24 423 506  "
           "•  linkedin.com/in/nizar-salah-7ab3b9125")

CSS = f"""
<style>
  .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}
  h1, h2, h3 {{ color: {NAVY}; }}
  .imc-band {{ background:{NAVY}; color:white; padding:16px 20px; border-radius:12px;
               font-size:1.45rem; font-weight:700; line-height:1.25; }}
  .imc-band small {{ display:block; font-size:.78rem; color:#aeb8cc; font-weight:500; margin-top:4px; }}
  .imc-sub {{ background:{GOLD}; color:{NAVY}; padding:6px 20px; border-radius:0 0 12px 12px;
              font-weight:600; font-size:.85rem; margin-top:-8px; margin-bottom:8px; }}
  .alert {{ padding:10px 14px; border-radius:8px; margin-bottom:7px; font-size:.92rem; }}
  .a-safe {{ background:{GREEN_BG}; color:{GREEN}; }}
  .a-warn {{ background:{AMBER_BG}; color:{AMBER}; }}
  .a-danger {{ background:{RED_BG}; color:{RED}; }}
  [data-testid="stMetricValue"] {{ color:{NAVY}; font-weight:700; font-size:1.6rem; line-height:1.25;
      white-space:nowrap; overflow:visible; }}
  [data-testid="stMetricLabel"] {{ white-space:normal; }}
  @media (max-width:680px) {{ [data-testid="stMetricValue"] {{ font-size:1.15rem; }} }}
  .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
  .stTabs [data-baseweb="tab"] {{ background:#F4F6F9; border-radius:8px 8px 0 0; padding:8px 14px; }}
  .stTabs [aria-selected="true"] {{ background:{NAVY}; color:white; }}
  .cta {{ background:{NAVY}; color:white; padding:14px 18px; border-radius:10px; text-align:center;
          font-weight:700; font-size:1.02rem; }}
  .cta-gold {{ background:linear-gradient(90deg,{GOLD},#d9bd82); color:{NAVY}; padding:14px 18px;
          border-radius:10px; text-align:center; font-weight:700; font-size:1.02rem; }}
  .coord {{ background:{GOLD}; color:{NAVY}; padding:9px 18px; border-radius:10px;
            text-align:center; font-weight:600; font-size:.82rem; word-break:break-word; }}
  .pcard {{ border:1px solid #e3e8f0; border-left:6px solid {TURQ}; border-radius:10px;
            padding:12px 16px; margin-bottom:10px; background:#fff; }}
  .pcard h4 {{ margin:0 0 4px 0; color:{NAVY}; font-size:1rem; }}
  .lockbox {{ border:2px dashed {GOLD}; border-radius:12px; padding:18px 20px; background:#fffdf5; }}
  .svc {{ border:1px solid #e3e8f0; border-radius:10px; padding:14px 16px; margin-bottom:12px;
          background:#fff; }}
  .svc h4 {{ margin:0 0 6px 0; color:{NAVY}; }}
  .price {{ color:{TURQ}; font-weight:700; }}
  .badge-vip {{ background:{GOLD}; color:{NAVY}; padding:2px 10px; border-radius:999px;
          font-size:.72rem; font-weight:700; }}
</style>
"""

def dt(x):   return f"{x:,.0f}".replace(",", " ") + " DT"
def pct(x):  return f"{x*100:,.1f}".replace(",", " ") + " %"
def num(x, s=""): return f"{x:,.2f}".replace(",", " ") + s

def maturity_label(score):
    if score >= 80: return ("Excellent", GREEN, "safe")
    if score >= 60: return ("Correct", TURQ, "safe")
    if score >= 40: return ("Fragile", AMBER, "warn")
    return ("Critique", RED, "danger")
