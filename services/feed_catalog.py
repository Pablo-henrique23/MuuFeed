"""Catálogo de ingredientes: lê a biblioteca NASEM do pacote nasem_dairy SEM alterar valores."""
from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CATEGORIAS_PT = {
    "Vitamin/Mineral": "Vitaminas e minerais", "By-Product/Other": "Subprodutos e outros",
    "By-product/Other": "Subprodutos e outros", "Grain Crop Forage": "Volumosos de culturas graníferas",
    "Grass/Legume Forage": "Gramíneas e leguminosas", "Energy Source": "Fontes de energia",
    "Plant Protein": "Proteínas vegetais", "Calf Liquid Feed": "Dietas líquidas para bezerros",
    "Additive": "Aditivos", "Fat Supplement": "Suplementos de gordura", "Animal Protein": "Proteínas animais",
    "Pasture": "Pastagem", "Fatty Acid Supplement": "Suplementos de ácidos graxos",
    "Sugar/Sugar Alcohol": "Açúcares e polióis",
}
TIPOS_PT = {"Forage": "Volumoso", "Concentrate": "Concentrado"}
# (coluna, rótulo). Unidades conforme a biblioteca NASEM: % da MS (Fd_DM em % da MN).
COMPOSICAO = [
    ("Fd_NDF", "FDN"), ("Fd_ADF", "FDA"), ("Fd_Lg", "Lignina"), ("Fd_CP", "Proteína bruta"),
    ("Fd_St", "Amido"), ("Fd_WSC", "Carboidratos solúveis em água"), ("Fd_CFat", "Extrato etéreo"),
    ("Fd_Ash", "Cinzas"), ("Fd_Ca", "Cálcio"), ("Fd_P", "Fósforo"), ("Fd_Mg", "Magnésio"),
    ("Fd_K", "Potássio"), ("Fd_Na", "Sódio"), ("Fd_Cl", "Cloro"), ("Fd_S", "Enxofre"),
]


def normalizar(texto: str) -> str:
    s = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return s.lower().strip()


@lru_cache(maxsize=1)
def carregar_biblioteca_bruta() -> pd.DataFrame:
    caminho = files("nasem_dairy.data.feed_library").joinpath("NASEM_feed_library.csv")
    return pd.read_csv(caminho)


def _json(nome: str) -> dict:
    return json.loads((DATA_DIR / nome).read_text(encoding="utf-8"))


class CatalogoIngredientes:
    def __init__(self) -> None:
        self._bruta = carregar_biblioteca_bruta()  # somente leitura
        self._pt: dict[str, str] = _json("feed_names_pt.json")
        b = self._bruta
        t = pd.DataFrame({
            "uid": b["UID"], "nome_original": b["Fd_Name"],
            "nome_pt": b["Fd_Name"].map(lambda n: self._pt.get(n, n)),
            "traduzido": b["Fd_Name"].isin(self._pt),
            "categoria": b["Fd_Category"], "categoria_pt": b["Fd_Category"].map(lambda c: CATEGORIAS_PT.get(c, c)),
            "tipo": b["Fd_Type"], "tipo_pt": b["Fd_Type"].map(lambda c: TIPOS_PT.get(c, c)),
            "ms_pct": b["Fd_DM"],
        })
        t["busca"] = (t["nome_pt"] + " " + t["nome_original"] + " " + t["categoria_pt"]).map(normalizar)
        self.tabela = t.reset_index(drop=True)
        meta = _json("demo_prices.json")
        por_nome = dict(zip(b["Fd_Name"], b["UID"]))
        self.precos_ilustrativos = {por_nome[n]: p for n, p in meta["precos"].items() if n in por_nome}
        self.aviso_precos = meta["_meta"]["aviso"]

    def categorias(self) -> list[str]:
        return sorted(self.tabela["categoria_pt"].unique())

    def buscar(self, consulta: str = "", categorias: list[str] | None = None) -> pd.DataFrame:
        t = self.tabela
        if categorias:
            t = t[t["categoria_pt"].isin(categorias)]
        for token in normalizar(consulta).split():
            t = t[t["busca"].str.contains(token, regex=False)]
        return t

    def obter(self, uid: str) -> pd.Series:
        return self.tabela[self.tabela["uid"] == uid].iloc[0]

    def composicao(self, uid: str) -> list[dict]:
        linha = self._bruta[self._bruta["UID"] == uid].iloc[0]
        saida = [{"Componente": "Matéria seca (MS)", "Valor": float(linha["Fd_DM"]), "Unidade": "% da matéria natural"}]
        for col, rotulo in COMPOSICAO:
            v = linha[col]
            saida.append({"Componente": rotulo, "Valor": None if pd.isna(v) else float(v), "Unidade": "% da MS"})
        return saida
