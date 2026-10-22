"""Rótulos em português para ingredientes NASEM (somente apresentação).

Não modifica nomes usados pelo NASEM, códigos UID ou valores nutricionais.
Traduções explícitas prevalecem; para itens não catalogados, somente estruturas
previsíveis recebem tradução. Se não houver tradução segura, preserva o original.
"""
from __future__ import annotations

import re

TRADUCOES_COMPLEMENTARES: dict[str, str] = {
    # Formulados para bezerros — aviso de espécie/idade é informação de segurança.
    'Casein': 'Caseína',
    'DGS wet': 'Grãos úmidos de destilaria (DGS)',
    'Distillers solubles': 'Solúveis de destilaria',
    'EDDI': 'EDDI (etilenodiamina di-hidroiodeto)',
    'Grain screenings, source unknwn': 'Resíduos da limpeza de grãos (origem não identificada)',
    'Corn grain screenings': 'Resíduos da limpeza de grãos de milho',
    'Grain sorghum hay': 'Feno de sorgo granífero',
    'Oat silage, immature': 'Silagem de aveia, imatura',
    'Oat silage, mid-maturity': 'Silagem de aveia, maturidade intermediária',
    'Wheat silage, HEADED': 'Silagem de trigo, espigado',
    'Wheat silage, VEGETATIVE': 'Silagem de trigo, estágio vegetativo',
    'Wheat hay, vegetative': 'Feno de trigo, estágio vegetativo',
    'Soybean hay': 'Feno de soja',
    'Soybean meal, extruded': 'Farelo de soja extrusado',
    'Soybean silage': 'Silagem de soja',
    'Legume silage, mid-maturity': 'Silagem de leguminosa, maturidade intermediária',
    'Fat, cottonseed oil': 'Gordura: óleo de algodão',
    'Fruit and vegetable byprod, wet': 'Subprodutos úmidos de frutas e hortaliças',
    'Sodium selenite': 'Selenito de sódio',
    'Sodium selenate': 'Selenato de sódio',
    'Zinc, organic generic': 'Zinco orgânico (genérico)',
    'Milk replacer 20 CP 20 fat': 'Sucedâneo do leite (20% PB, 20% gordura; bezerros)',
    'Milk replacer 26 CP 17 fat': 'Sucedâneo do leite (26% PB, 17% gordura; bezerros)',
    'Milk replacer 28 CP 17.5 fat': 'Sucedâneo do leite (28% PB, 17,5% gordura; bezerros)',
    'Skim milk, fresh': 'Leite desnatado fresco',
    'Skim milk, powder': 'Leite desnatado em pó',
    'Calf grower 14CP (Fed to calves only)': 'Ração de crescimento para bezerros (14% PB; somente bezerros)',
    'Calf grower 16CP (Fed to calves only)': 'Ração de crescimento para bezerros (16% PB; somente bezerros)',
    'Calf starter 18CP high starch (Fed to calves only)': 'Ração inicial para bezerros (18% PB, alto amido; somente bezerros)',
    'Calf starter 18CP low starch (Fed to calves only)': 'Ração inicial para bezerros (18% PB, baixo amido; somente bezerros)',
    'Calf starter 22CP high starch (Fed to calves only)': 'Ração inicial para bezerros (22% PB, alto amido; somente bezerros)',
    'Calf starter 22CP med starch (Fed to calves only)': 'Ração inicial para bezerros (22% PB, amido médio; somente bezerros)',
    'Barley malt sprouts': 'Brotos de malte de cevada',
    'Barley grain, steam rolled': 'Cevada em grão laminada a vapor',
    'Bakery byproduct, bread waste': 'Resíduo de panificação (pães)',
    'Bakery byproduct, cereal': 'Subproduto de panificação (cereais)',
    'Bakery byproduct, cookies': 'Subproduto de panificação (biscoitos)',
    'Apple pomace or byproduct, wet': 'Bagaço ou subproduto úmido de maçã',
    'Brewers yeast, wet': 'Levedura úmida de cervejaria',
    'Candy (not chocolate) byproduct': 'Subproduto de doces (exceto chocolate)',
    'Candy byproduct, high protein': 'Subproduto de doces com alto teor de proteína',
    'Chocolate byproduct': 'Subproduto de chocolate',
    'Cool season grass hay, mid-mtr': 'Feno de gramínea de clima frio, maturidade intermediária',
    'Corn germ meal': 'Farelo de gérmen de milho',
    'Corn grain HM, medium grind': 'Milho grão úmido, moagem média',
    'Ammonium chloride': 'Cloreto de amônio',
    'Ammonium phosphate (dibasic)': 'Fosfato diamônico (dibásico)',
    'Ammonium phosphate (monobasic)': 'Fosfato monoamônico (monobásico)',
    'Calcium chloride': 'Cloreto de cálcio',
    'Calcium chloride (2H2O)': 'Cloreto de cálcio (2H2O)',
    'Calcium hydroxide': 'Hidróxido de cálcio',
    'Calcium iodate': 'Iodato de cálcio',
    'Calcium oxide': 'Óxido de cálcio',
    'Calcium sulfate (2H2O)': 'Sulfato de cálcio (2H2O)',
    'Cobalt carbonate': 'Carbonato de cobalto',
    'Cobalt carbonate (6H2O)': 'Carbonato de cobalto (6H2O)',
    'Cobalt chloride (6H2O)': 'Cloreto de cobalto (6H2O)',
    'Cobalt organic generic': 'Cobalto orgânico (genérico)',
    'Cobalt sulfate (7H2O)': 'Sulfato de cobalto (7H2O)',
    'Copper chloride (2H2O)': 'Cloreto de cobre (2H2O)',
    'Copper organic, generic': 'Cobre orgânico (genérico)',
    'Copper oxide': 'Óxido de cobre',
    'Fat, corn oil': 'Gordura: óleo de milho',
    'Fat, palm oil': 'Gordura: óleo de palma',
    'Fat, canola oil': 'Gordura: óleo de canola',
    'Fat, sunflower oil': 'Gordura: óleo de girassol',
    'Fat, fish oil': 'Gordura: óleo de peixe',
    'Glucose': 'Glicose',
    'Dextrose': 'Dextrose',
    'Fructose': 'Frutose',
    'Lactose': 'Lactose',
    'Maize gluten meal': 'Farelo de glúten de milho',
    'Soybean meal, solvent 44CP': 'Farelo de soja, solvente (44% PB)',
    'Zinc, sulfate monohydrate': 'Sulfato de zinco monoidratado',
    'Zinc chloride': 'Cloreto de zinco',
    'Zinc carbonate': 'Carbonato de zinco',
    'Zinc sulfate (7H2O)': 'Sulfato de zinco (7H2O)',
    'Copper sulfate (5H2O)': 'Sulfato de cobre (5H2O)',
}

# Somente fórmulas químicas reconhecidas e estruturas altamente regulares.
ELEMENTOS = {
    'Ammonium': 'amônio', 'Calcium': 'cálcio', 'Cobalt': 'cobalto',
    'Copper': 'cobre', 'Iron': 'ferro', 'Magnesium': 'magnésio',
    'Manganese': 'manganês', 'Potassium': 'potássio', 'Sodium': 'sódio',
    'Zinc': 'zinco', 'Selenium': 'selênio', 'Iodine': 'iodo',
    'Chromium': 'cromo', 'Molybdenum': 'molibdênio',
}
SAIS = {
    'carbonate': 'Carbonato', 'bicarbonate': 'Bicarbonato',
    'chloride': 'Cloreto', 'iodate': 'Iodato', 'hydroxide': 'Hidróxido',
    'oxide': 'Óxido', 'phosphate': 'Fosfato', 'sulfate': 'Sulfato',
    'sulphate': 'Sulfato', 'nitrate': 'Nitrato', 'acetate': 'Acetato',
    'selenite': 'Selenito', 'selenate': 'Selenato',
}


def traduzir_nome(nome: str, traducoes: dict[str, str] | None = None) -> tuple[str, bool]:
    """Retorna rótulo em português e indicador de tradução auditável.

    Qualquer rótulo não reconhecido permanece no inglês original em vez de
    inventar uma tradução de nome técnico.
    """
    if not isinstance(nome, str) or not nome.strip():
        return nome, False
    if traducoes and nome in traducoes:
        return traducoes[nome], True
    if nome in TRADUCOES_COMPLEMENTARES:
        return TRADUCOES_COMPLEMENTARES[nome], True

    # Fórmulas genéricas para rações de bezerros que variam no teor de PB.
    m = re.fullmatch(r'Calf grower (\d+(?:\.\d+)?)\s*CP \(Fed to calves only\)', nome, flags=re.I)
    if m:
        return f'Ração de crescimento para bezerros ({m.group(1)}% PB; somente bezerros)', True
    m = re.fullmatch(r'Calf starter (\d+(?:\.\d+)?)\s*CP (high|med|medium|low) starch \(Fed to calves only\)', nome, flags=re.I)
    if m:
        amido = {'high': 'alto', 'low': 'baixo', 'med': 'médio', 'medium': 'médio'}[m.group(2).lower()]
        return f'Ração inicial para bezerros ({m.group(1)}% PB, {amido} amido; somente bezerros)', True

    # Aminoácidos ruminalmente protegidos, identificados por código padrão.
    aminoacidos = {
        'Arg': 'arginina', 'His': 'histidina', 'Ile': 'isoleucina',
        'Leu': 'leucina', 'Lys': 'lisina', 'Met': 'metionina',
        'Phe': 'fenilalanina', 'Thr': 'treonina', 'Trp': 'triptofano',
        'Val': 'valina',
    }
    m = re.fullmatch(r'Rumen Protected (Arg|His|Ile|Leu|Lys|Met|Phe|Thr|Trp|Val)', nome)
    if m:
        return f'{aminoacidos[m.group(1)].capitalize()} protegida da degradação ruminal', True

    # Culturas forrageiras com padrão de nome e estádio explicitados.
    culturas = {
        'Oat': 'aveia', 'Wheat': 'trigo', 'Barley': 'cevada',
        'Soybean': 'soja', 'Corn': 'milho', 'Rye': 'centeio',
        'Sorghum': 'sorgo', 'Alfalfa': 'alfafa',
    }
    estagios = {
        'immature': 'imatura', 'mature': 'madura',
        'mid-maturity': 'maturidade intermediária',
        'vegetative': 'estádio vegetativo', 'typical': 'típica',
    }
    m = re.fullmatch(r'(Oat|Wheat|Barley|Soybean|Corn|Rye|Sorghum|Alfalfa) (silage|hay|straw)(?:,? (immature|mature|mid-maturity|vegetative|typical))?', nome, flags=re.I)
    if m:
        c = culturas[m.group(1).capitalize()]
        produto = {'silage': 'Silagem', 'hay': 'Feno', 'straw': 'Palha'}[m.group(2).lower()]
        estado = (f', {estagios[m.group(3).lower()]}' if m.group(3) else '')
        return f'{produto} de {c}{estado}', True

    # Formas minerais simples ou hidratadas: não inferir sais fora do dicionário.
    m = re.fullmatch(r'([A-Za-z]+) (carbonate|bicarbonate|chloride|iodate|hydroxide|oxide|phosphate|sulfate|sulphate|nitrate|acetate|selenite|selenate)(?:\s*(\([^)]*\)))?', nome, flags=re.I)
    if m:
        el = next((pt for en, pt in ELEMENTOS.items() if en.casefold() == m.group(1).casefold()), None)
        sal = SAIS.get(m.group(2).lower())
        if el and sal:
            return f'{sal} de {el}' + (f' {m.group(3)}' if m.group(3) else ''), True
    m = re.fullmatch(r'([A-Za-z]+)(?:,?\s+)organic,?\s*generic', nome, flags=re.I)
    if m:
        el = next((pt for en, pt in ELEMENTOS.items() if en.casefold() == m.group(1).casefold()), None)
        if el:
            return f'{el.capitalize()} orgânico (genérico)', True
    return nome, False
