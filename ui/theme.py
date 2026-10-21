"""Identidade visual do MuuFeed: verde de pasto, tinta escura, fontes do sistema (funciona offline)."""
from __future__ import annotations

import html

import streamlit as st

from services.formatting import brl, num  # noqa: F401  (reexportados para as páginas)

CSS = """
<style>
html, body, [class*="css"] { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
.stAppDeployButton, [data-testid="stAppDeployButton"], .stDeployButton { display:none !important; }
.block-container { padding-top: 2rem; max-width: 1180px; }
h1, h2, h3 { letter-spacing: -0.01em; color: #14211B; }
.mf-hero { background: linear-gradient(135deg,#1F6B4F 0%,#17503B 100%); color:#fff; border-radius:14px; padding:1.6rem 1.8rem; margin-bottom:1.2rem; }
.mf-hero h1 { color:#fff; margin:0 0 .3rem 0; font-size:2.1rem; }
.mf-hero p { margin:0; color:#DCEBE3; font-size:1.05rem; max-width:44rem; }
.mf-card { background:#fff; border:1px solid #D5E0D8; border-radius:12px; padding:.9rem 1rem; height:100%; }
.mf-card .l { color:#51625A; font-size:.85rem; }
.mf-card .v { color:#14211B; font-size:1.45rem; font-weight:650; line-height:1.25; }
.mf-card .h { color:#6B7A72; font-size:.78rem; margin-top:.15rem; }
.mf-banner { border-radius:10px; padding:.8rem 1rem; margin:.4rem 0 1rem 0; border-left:6px solid; }
.mf-info { background:#E7F0F8; border-color:#2B6CB0; } .mf-ok { background:#E4F3EA; border-color:#1F6B4F; }
.mf-warn { background:#FBF1DC; border-color:#B7791F; } .mf-err { background:#FBE6E3; border-color:#B42318; }
.mf-demo { background:#FDECEA; border:2px dashed #B42318; border-radius:10px; padding:.8rem 1rem; margin-bottom:1rem; color:#7A1A12; font-weight:600; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(4) { background:#1F6B4F; border-radius:8px; padding:.25rem .6rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type(4) * { color:#fff !important; font-weight:700; }
@media (prefers-reduced-motion: no-preference) { .mf-card { transition: box-shadow .15s; } .mf-card:hover { box-shadow:0 2px 10px rgba(20,33,27,.12); } }
</style>
"""


def aplicar_tema() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def card(rotulo: str, valor: str, dica: str = "") -> None:
    st.markdown(f'<div class="mf-card"><div class="l">{html.escape(rotulo)}</div>'
                f'<div class="v">{html.escape(valor)}</div><div class="h">{html.escape(dica)}</div></div>',
                unsafe_allow_html=True)


def banner(tipo: str, texto: str) -> None:
    st.markdown(f'<div class="mf-banner mf-{tipo}">{html.escape(texto)}</div>', unsafe_allow_html=True)
