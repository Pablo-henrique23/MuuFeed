"""Páginas do MuuFeed. Só apresentação: nenhuma regra nutricional mora aqui."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models import ESTADOS, PADROES_AVANCADOS, Lote
from services.diet_analysis import analisar_dieta
from services.demo_scenario import cenario_demonstrativo
from services.financeiro import resumo_financeiro
from services.ingredient_suggestion import sugerir_ingredientes
from services.pdf_report import gerar_relatorio_pdf
from services.rotulos import rotulo_legivel, eh_chave_tecnica, nao_avaliadas_unicas
from services.formulation_service import executar_formulacao, formulador_conectado
from ui.state import adicionar, get_catalogo, ir_para, montar_requisicao
from ui.theme import banner, brl, card, num

ROTULO_STATUS = {
    None: "Não calculado", "nao_conectado": "Formulador não conectado",
    "demonstracao": "Cenário demonstrativo (não calculado)", "otimo": "Dieta candidata calculada",
    "candidata_experimental": "Candidata experimental (avaliação parcial)",
    "inviavel": "Sem solução viável", "escopo_nao_suportado": "Fora do escopo", "erro": "Erro na formulação",
}
VERDE, AZUL = "#1F6B4F", "#2B6CB0"


# ---------------------------------------------------------------- Painel
def pagina_painel() -> None:
    ss, lote, res = st.session_state, st.session_state["lote"], st.session_state["resultado"]
    st.markdown('<div class="mf-hero"><h1>MuuFeed</h1><p>Sistema especialista para formulação inteligente e '
                'econômica de dietas para bovinos leiteiros.</p></div>', unsafe_allow_html=True)
    custo = res.custo_vaca_dia if res and res.status in ("otimo", "candidata_experimental") else None
    cols = st.columns(5)
    with cols[0]:
        card("Lote selecionado", lote.nome if lote else "Não definido", ESTADOS[lote.estado] if lote else "")
    with cols[1]:
        card("Número de vacas", str(lote.n_vacas) if lote else "—")
    with cols[2]:
        card("Produção média", num(lote.leite_kg_dia, 1, "kg/vaca/dia") if lote else "—")
    with cols[3]:
        card("Custo da dieta", brl(custo) + "/vaca/dia" if custo is not None else "Não calculado")
    with cols[4]:
        card("Estado da formulação", ROTULO_STATUS.get(res.status if res else None))
    st.write("")
    n_ing = sum(1 for d in ss["selecionados"].values() if d["disponivel"])
    passos = [("Caracterizar o lote", lote is not None, "Lote"),
              ("Escolher ingredientes e informar preços", n_ing > 0, "Ingredientes e preços"),
              ("Formular a dieta", bool(res and res.status in ("otimo", "candidata_experimental")), "Formular dieta")]
    st.subheader("Como formular em três passos")
    for i, (txt, feito, destino) in enumerate(passos):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"{'✅' if feito else '⬜'} **{i + 1}. {txt}**" + (f" — {n_ing} ingrediente(s)" if i == 1 and n_ing else ""))
        if c2.button("Abrir", key=f"abrir_{i}", use_container_width=True):
            ir_para(destino)
    if lote and st.button("Sugerir ingredientes automaticamente", type="primary", key="abrir_assistido"):
        ir_para("Sugestão automática")
    st.caption("Decisões nutricionais são tomadas por código determinístico e base de conhecimento explícita. "
               "Nenhum modelo de linguagem calcula dietas.")


# ---------------------------------------------------------------- Lote
CAMPOS_FORM = {"f_nome": "", "f_n": 50, "f_raca": "Holandesa", "f_idade": 4.0, "f_idade_un": "anos", "f_idade_dias": 821.0, "f_idade_meses": 27.0, "f_peso": 600.0,
               "f_ordem": 2, "f_dias": 100, "f_estado": "Lactating Cow", "f_leite": 25.0, "f_gord": 3.7,
               "f_prot": 3.2, "f_bcs": PADROES_AVANCADOS["bcs"], "f_lac": PADROES_AVANCADOS["lactose_pct"],
               "f_maduro": PADROES_AVANCADOS["peso_maduro_kg"], "f_gest": PADROES_AVANCADOS["dias_gestacao"]}


def _exemplo() -> None:
    st.session_state.update({"f_nome": "Lote exemplo (valores ilustrativos)", "f_n": 50, "f_raca": "Holandesa",
                             "f_idade": 2.25, "f_idade_un": "anos", "f_peso": 625.0, "f_ordem": 1, "f_dias": 100,
                             "f_leite": 25.0, "f_gord": 4.55, "f_prot": 3.66, "f_gest": 46})


def pagina_lote() -> None:
    ss = st.session_state
    for k, v in CAMPOS_FORM.items():
        ss.setdefault(k, v)
    st.title("Caracterização do lote")
    st.caption("Informe os dados médios do lote. Os campos marcados como padrão são hipóteses, não medições.")
    st.button("Carregar lote de exemplo (valores ilustrativos)", on_click=_exemplo)
    with st.form("form_lote"):
        a, b = st.columns(2)
        nome = a.text_input("Nome ou identificação do lote", key="f_nome")
        n = b.number_input("Número de vacas", 1, 100000, key="f_n", step=1)
        raca = a.selectbox("Raça", ["Holandesa", "Jersey", "Outra / não parametrizada"], key="f_raca",
                           help="Holandesa e Jersey são convertidas para An_Breed no NASEM. Outras raças requerem revisão do suporte no modelo.")
        estado = b.selectbox("Estado fisiológico", list(ESTADOS), format_func=ESTADOS.get, key="f_estado")
        c1, c2 = a.columns([2, 1])
        # Dentro de st.form, mudar a unidade NÃO provoca rerun imediato.
        # Portanto o limite do widget não pode depender de `un` neste formulário.
        # O limite de 12000 é apenas técnico; Lote.validar() aplica a faixa
        # plausível em dias depois de converter a unidade selecionada.
        idade = c1.number_input("Idade média", min_value=0.0, max_value=12000.0,
                                key="f_idade", step=0.01, format="%.2f")
        un = c2.selectbox("Unidade", ["anos", "meses", "dias"], key="f_idade_un")
        st.caption("Informe a idade na unidade selecionada; a validação converte para dias ao salvar.")
        peso = b.number_input("Peso médio (kg)", 0.0, 1500.0, key="f_peso", step=5.0)
        ordem = a.number_input("Ordem de lactação (1 = primeira)", 1, 15, key="f_ordem", step=1)
        dias = b.number_input("Dias em lactação (dias)", 0, 800, key="f_dias", step=1)
        leite = a.number_input("Produção média de leite (kg/vaca/dia)", 0.0, 120.0, key="f_leite", step=0.5)
        gord = b.number_input("Gordura do leite (%)", 0.0, 12.0, key="f_gord", step=0.05)
        prot = a.number_input("Proteína do leite (%)", 0.0, 8.0, key="f_prot", step=0.05)
        with st.expander("Campos avançados (hipóteses padrão)"):
            st.caption("Valores iniciais vêm do exemplo do pacote nasem_dairy. São hipóteses: substitua por medições.")
            x, y = st.columns(2)
            bcs = x.number_input("Escore de condição corporal (1 a 5)", 1.0, 5.0, key="f_bcs", step=0.25)
            lac = y.number_input("Lactose do leite (%)", 0.0, 8.0, key="f_lac", step=0.05)
            mad = x.number_input("Peso à maturidade (kg)", 0.0, 1500.0, key="f_maduro", step=10.0)
            gest = y.number_input("Dias de gestação (dias)", 0, 300, key="f_gest", step=1)
        ok = st.form_submit_button("Salvar lote", type="primary")
    if ok:
        lote = Lote(nome, int(n), raca, float(idade), un, float(peso), int(ordem), int(dias), estado,
                    float(leite), float(gord), float(prot), float(bcs), float(lac), float(mad), int(gest))
        erros, avisos = lote.validar()
        for e in erros:
            st.error(e)
        if not erros:
            ss["lote"], ss["resultado"], ss["requisicao_resultado"] = lote, None, None
            ss["analise_resultado"] = None  # novo lote invalida o resultado
            st.success(f"Lote salvo. Idade usada pelo formulador: {lote.idade_dias:,.0f} dias.".replace(",", "."))
            for w in avisos:
                st.warning(w)


# ---------------------------------------------------------------- Sugestão assistida

def pagina_sugestao_automatica() -> None:
    ss, cat = st.session_state, get_catalogo()
    st.title("Sugestão automática de ingredientes")
    st.caption("Modo assistido: o MuuFeed propõe ingredientes candidatos para vacas em lactação. "
               "A seleção não é uma dieta e não garante adequação nutricional. "
               "Você confirma disponibilidade e preços antes de usar o formulador.")
    if ss.get("lote") is None:
        st.warning("Cadastre e salve o lote primeiro.")
        if st.button("Ir ao lote", key="assistir_lote"):
            ir_para("Lote")
        return
    sugestoes, avisos = sugerir_ingredientes(ss["lote"], cat)
    for aviso in avisos:
        st.warning(aviso)
    if not sugestoes:
        return
    st.info("Preços iniciais são ILUSTRATIVOS, não cotações. Alimentos sugeridos não significam que estão "
            "disponíveis na propriedade. Confirme cada um. Você pode acrescentar outros no modo manual.")
    linhas = []
    for sug in sugestoes:
        atual = ss["selecionados"].get(sug.uid, {})
        linhas.append({"uid": sug.uid, "Incluir": bool(atual.get("disponivel", True)),
                       "Ingrediente": sug.nome_pt, "Grupo": sug.grupo,
                       "Justificativa da sugestão": sug.motivo,
                       "Preço (R$/kg MN)": atual.get("preco", sug.preco_ilustrativo)})
    editado = st.data_editor(
        pd.DataFrame(linhas), hide_index=True, use_container_width=True, key="sugestao_editor",
        disabled=["uid", "Ingrediente", "Grupo", "Justificativa da sugestão"],
        column_config={"uid": None, "Incluir": st.column_config.CheckboxColumn("Disponível e incluir"),
                       "Preço (R$/kg MN)": st.column_config.NumberColumn(min_value=0.0, format="%.2f")})
    st.caption("A coluna 'Disponível e incluir' requer confirmação do produtor; preços podem ser editados aqui "
               "ou na tela Ingredientes e preços. A lista final é somente um conjunto candidato.")
    if ss["selecionados"]:
        st.warning("Você já possui ingredientes selecionados. Ao confirmar, a lista atual será SUBSTITUÍDA "
                   "pelos candidatos marcados; os preços previamente editados desses mesmos alimentos são preservados.")
    confirmar = st.checkbox("Confirmei a disponibilidade dos ingredientes marcados e revisei seus preços.",
                            key="assistido_confirma")
    if st.button("Usar ingredientes confirmados", type="primary", disabled=not confirmar):
        novos = {}
        for _, linha in editado.iterrows():
            if not bool(linha["Incluir"]):
                continue
            uid = linha["uid"]
            preco = linha["Preço (R$/kg MN)"]
            if pd.isna(preco) or float(preco) <= 0:
                st.error(f"Informe um preço positivo para {linha['Ingrediente']} antes de continuar.")
                return
            anterior = ss["selecionados"].get(uid, {})
            sug = next(s for s in sugestoes if s.uid == uid)
            preco = float(preco)
            origem = (anterior.get("origem", "") if preco == anterior.get("preco") else
                      "ilustrativo" if preco == sug.preco_ilustrativo else "informado")
            novos[uid] = {"preco": preco, "origem": origem or "informado", "disponivel": True,
                           "min_mn": anterior.get("min_mn"), "max_mn": anterior.get("max_mn")}
        if len(novos) < 2:
            st.error("Confirme pelo menos dois ingredientes candidatos para tentar a formulação.")
            return
        ss["selecionados"] = novos
        ss["resultado"] = None
        ss["requisicao_resultado"] = None
        ir_para("Ingredientes e preços")


# ---------------------------------------------------------------- Ingredientes
def pagina_ingredientes() -> None:
    cat, ss = get_catalogo(), st.session_state
    sel = ss["selecionados"]
    st.title("Ingredientes e preços")
    st.markdown("**MS** é a matéria seca; **MN** é a matéria natural (como o alimento é comprado e fornecido). "
                "O preço é informado em **R$/kg de MN**; o custo por kg de MS é calculado como preço ÷ (MS ÷ 100). "
                "Composição e valores originais da biblioteca NASEM não são alterados.")
    banner("warn", cat.aviso_precos)
    c1, c2 = st.columns([3, 2])
    q = c1.text_input("Buscar ingrediente (português ou inglês)", key="busca_ing", placeholder="ex.: milho, soybean, calcário")
    cats = c2.multiselect("Categoria", cat.categorias(), key="cat_ing")
    df = cat.buscar(q, cats)
    st.caption(f"{len(df)} de {len(cat.tabela)} ingredientes · {len(sel)} selecionado(s)")
    vista = df[["uid", "nome_pt", "nome_original", "categoria_pt", "tipo_pt", "ms_pct"]].copy()
    vista.insert(0, "Usar", vista["uid"].isin(sel))
    ed = st.data_editor(
        vista, hide_index=True, height=300, use_container_width=True, key=f"cat_{abs(hash((q, tuple(cats))))}",
        disabled=["nome_pt", "nome_original", "categoria_pt", "tipo_pt", "ms_pct"],
        column_config={"uid": None, "Usar": st.column_config.CheckboxColumn("Usar"),
                       "nome_pt": "Ingrediente", "nome_original": "Nome original (NASEM)",
                       "categoria_pt": "Categoria", "tipo_pt": "Tipo",
                       "ms_pct": st.column_config.NumberColumn("MS (% da MN)", format="%.1f")})
    for uid, usar in zip(ed["uid"], ed["Usar"]):
        if usar and uid not in sel:
            adicionar(uid)
        elif not usar and uid in sel:
            del sel[uid]
    if len(df):
        uid_v = st.selectbox("Ver composição nutricional", list(df["uid"]),
                             format_func=lambda u: cat.obter(u).nome_pt, key="ver_comp")
        comp = pd.DataFrame(cat.composicao(uid_v))
        comp["Valor"] = comp["Valor"].map(lambda v: "não disponível" if v is None else f"{v:.2f}".replace(".", ","))
        st.dataframe(comp, hide_index=True, use_container_width=True)
        st.caption(f"Identificador original: {uid_v}")
    st.subheader("Ingredientes selecionados")
    if not sel:
        st.info("Nenhum ingrediente selecionado. Marque “Usar” na tabela acima; só os selecionados vão ao formulador.")
        return
    ss["data_ref_precos"] = st.date_input("Data de referência dos preços (opcional)", value=ss["data_ref_precos"],
                                          format="DD/MM/YYYY")
    linhas = []
    for uid, d in sel.items():
        r = cat.obter(uid)
        ps = None if d["preco"] is None else d["preco"] / (r.ms_pct / 100)
        linhas.append({"uid": uid, "Disponível": d["disponivel"], "Ingrediente": r.nome_pt, "MS (%)": r.ms_pct,
                       "Preço (R$/kg MN)": d["preco"], "Custo (R$/kg MS)": ps,
                       "Mín. (kg MN/vaca/dia)": d["min_mn"], "Máx. (kg MN/vaca/dia)": d["max_mn"],
                       "Origem do preço": d["origem"] or "a informar", "Remover": False})
    ed2 = st.data_editor(
        pd.DataFrame(linhas), hide_index=True, use_container_width=True, key=f"sel_{len(sel)}",
        disabled=["Ingrediente", "MS (%)", "Custo (R$/kg MS)", "Origem do preço"],
        column_config={"uid": None, "MS (%)": st.column_config.NumberColumn(format="%.1f"),
                       "Preço (R$/kg MN)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
                       "Custo (R$/kg MS)": st.column_config.NumberColumn(format="%.2f"),
                       "Mín. (kg MN/vaca/dia)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
                       "Máx. (kg MN/vaca/dia)": st.column_config.NumberColumn(min_value=0.0, format="%.2f")})
    mudou = False
    for _, l in ed2.iterrows():
        uid, d = l["uid"], sel.get(l["uid"])
        if d is None:
            continue
        if l["Remover"]:
            del sel[uid]; mudou = True; continue
        novo = None if pd.isna(l["Preço (R$/kg MN)"]) else float(l["Preço (R$/kg MN)"])
        if novo != d["preco"]:
            d["preco"], d["origem"], mudou = novo, ("informado" if novo is not None else ""), True
        d["disponivel"] = bool(l["Disponível"])
        d["min_mn"] = None if pd.isna(l["Mín. (kg MN/vaca/dia)"]) else float(l["Mín. (kg MN/vaca/dia)"])
        d["max_mn"] = None if pd.isna(l["Máx. (kg MN/vaca/dia)"]) else float(l["Máx. (kg MN/vaca/dia)"])
    if mudou:
        st.rerun()
    st.caption("Mínimo e máximo são restrições opcionais definidas por você; o MuuFeed não impõe limites próprios aqui.")


# ---------------------------------------------------------------- Formular
def pagina_formular() -> None:
    ss = st.session_state
    st.title("Formular dieta")
    st.markdown("**Objetivo:** minimizar o custo diário da dieta por vaca, respeitando as exigências e restrições "
                "nutricionais implementadas no sistema especialista.")
    lote = ss["lote"]
    a, b = st.columns(2)
    with a.container(border=True):
        st.markdown("**Lote**")
        if lote:
            st.write(f"{lote.nome} · {lote.n_vacas} vacas · {ESTADOS[lote.estado]}")
            st.write(f"{num(lote.leite_kg_dia, 1, 'kg')} de leite/vaca/dia · {num(lote.peso_kg, 0, 'kg')} · "
                     f"idade {lote.idade_dias / 365.25:.1f} anos · {lote.ordem_lactacao}ª lactação · {lote.dias_lactacao} dias em lactação")
            if lote.campos_padrao:
                st.caption("Contém hipóteses padrão (não medidas) nos campos avançados.")
        else:
            st.warning("Lote não caracterizado.")
    with b.container(border=True):
        st.markdown("**Ingredientes disponíveis**")
        cat = get_catalogo()
        disp = [(u, d) for u, d in ss["selecionados"].items() if d["disponivel"]]
        for u, d in disp[:8]:
            st.write(f"• {cat.obter(u).nome_pt} — {brl(d['preco'])}/kg MN ({d['origem'] or 'preço a informar'})")
        if len(disp) > 8:
            st.caption(f"+ {len(disp) - 8} ingrediente(s)")
        if not disp:
            st.warning("Nenhum ingrediente disponível.")
    # O consumo de MS é informado, não presumido. Campo da formulação experimental.
    consumo_ms = st.number_input(
        "Consumo estimado de matéria seca (kg MS/vaca/dia)", min_value=0.1,
        value=None, step=0.5, format="%.2f", key="form_consumo_ms",
        help="Obrigatório neste protótipo; deve vir de medição/estimativa técnica do lote, não de valor padrão.")
    st.markdown("**Restrições opcionais de composição (% da matéria seca)**")
    st.caption("Sem valor informado, FDN e amido são calculados apenas como indicadores informativos. "
               "Valores digitados são definidos pelo usuário, não recomendações automáticas NASEM.")
    col_fdn, col_amido = st.columns(2)
    limite_fdn = col_fdn.number_input(
        "FDN mínima (% da MS)", min_value=0.0, max_value=100.0, value=None,
        step=0.5, format="%.2f", key="form_fdn_min",
        help="Opcional; use somente um limite tecnicamente justificado para o seu lote.")
    limite_amido = col_amido.number_input(
        "Amido máximo (% da MS)", min_value=0.0, max_value=100.0, value=None,
        step=0.5, format="%.2f", key="form_amido_max",
        help="Opcional; use somente um limite tecnicamente justificado para o seu lote.")
    st.caption("A FDN de forragens é calculada separadamente da FDN total; isso NÃO mede fibra fisicamente efetiva. "
               "Segundo o NASEM 2021, sua interpretação depende de FDN total, amido e características físicas da dieta.")
    limite_fdn_forragem = st.number_input(
        "FDN proveniente de forragens — mínimo (% da MS, opcional)",
        min_value=0.0, max_value=100.0, value=None, step=0.5, format="%.2f",
        key="form_fdn_forragem_min",
        help="Apenas limite explicitamente informado e tecnicamente justificado; não há mínimo automático neste protótipo.")
    exigir_ca_p = st.checkbox(
        "Exigir cálcio e fósforo ABSORVIDOS (NASEM, experimental)",
        value=False, key="form_minerais_abs",
        help="Restringe a busca usando oferta absorvida e exigência calculadas pelo próprio NASEM. "
             "Pode não haver solução com os ingredientes disponíveis; não verifica os demais nutrientes.")
    st.caption("Sem marcar, o MuuFeed ainda pode exibir o balanço mineral calculado pelo NASEM, "
               "mas não altera a dieta para corrigi-lo.")
    req, erros = montar_requisicao()
    if req is not None:
        req.opcoes.consumo_ms_kg_dia = consumo_ms
        req.opcoes.min_ndf_pct_dm = limite_fdn
        req.opcoes.max_starch_pct_dm = limite_amido
        req.opcoes.min_forage_ndf_pct_dm = limite_fdn_forragem
        req.opcoes.require_absorbed_ca_p = exigir_ca_p
    for e in erros:
        st.error(e)
    if not formulador_conectado():
        banner("info", "O formulador nutricional ainda não está conectado a esta interface. "
                       "Ao formular, nenhuma dieta será calculada.")
    if st.button("FORMULAR DIETA", type="primary", use_container_width=True, disabled=req is None):
        with st.status("Formulando a dieta…", expanded=True) as status:
            st.write("Validando lote e ingredientes…")
            st.write("Aplicando regras e otimizando o custo…")
            ss["resultado"] = executar_formulacao(req)
            ss["requisicao_resultado"] = req
            status.update(label="Processamento concluído", state="complete")
        ir_para("Resultados")


# ---------------------------------------------------------------- Análise de dieta existente

def pagina_analisar_dieta() -> None:
    ss = st.session_state
    st.title("Analisar dieta existente")
    st.caption("Informe a dieta que o lote já recebe, em kg de matéria natural por vaca/dia. "
               "O sistema avalia as quantidades fixas: não altera ingredientes nem otimiza preços.")
    lote = ss.get("lote")
    if lote is None:
        st.warning("Cadastre o lote antes de analisar uma dieta.")
        if st.button("Ir ao lote", key="analise_ir_lote"):
            ir_para("Lote")
        return
    cat = get_catalogo()
    selecionados = ss.get("selecionados", {})
    linhas = []
    for uid, dados in selecionados.items():
        info = cat.obter(uid)
        linhas.append({"uid": uid, "Ingrediente": info.nome_pt,
                       "Quantidade (kg MN/vaca/dia)": 0.0,
                       "Preço (R$/kg MN)": dados.get("preco")})
    if not linhas:
        st.info("Selecione ingredientes na página 'Ingredientes e preços' e retorne para informar as quantidades.")
        if st.button("Escolher ingredientes", key="analise_ingredientes"):
            ir_para("Ingredientes e preços")
        return
    st.info("Esta análise utiliza as quantidades digitadas, não uma dieta otimizada. "
            "Os preços continuam editáveis; valores ilustrativos não são cotações reais.")
    frame = pd.DataFrame(linhas)
    ed = st.data_editor(frame, hide_index=True, use_container_width=True,
                        key="analise_dieta_editor", disabled=["uid", "Ingrediente"],
                        column_config={"uid": None,
                                       "Quantidade (kg MN/vaca/dia)": st.column_config.NumberColumn(min_value=0.0, format="%.3f"),
                                       "Preço (R$/kg MN)": st.column_config.NumberColumn(min_value=0.0, format="%.2f")})
    signature = tuple((str(r["uid"]), str(r["Quantidade (kg MN/vaca/dia)"]),
                       str(r["Preço (R$/kg MN)"])) for _, r in ed.iterrows())
    if st.button("ANALISAR DIETA INFORMADA", type="primary", use_container_width=True):
        from models import Ingrediente
        ingredientes, quantidades = [], {}
        for _, r in ed.iterrows():
            uid = r["uid"]
            cat_row = cat.obter(uid)
            preco = r["Preço (R$/kg MN)"]
            qty = r["Quantidade (kg MN/vaca/dia)"]
            if pd.isna(qty) or float(qty) < 0:
                st.error(f"Quantidade inválida: {cat_row.nome_pt}")
                return
            if float(qty) == 0:
                continue
            if pd.isna(preco) or float(preco) <= 0:
                st.error(f"Informe preço positivo: {cat_row.nome_pt}")
                return
            ingredientes.append(Ingrediente(uid, cat_row.nome_original, cat_row.nome_pt,
                                            float(cat_row.ms_pct), float(preco)))
            quantidades[uid] = float(qty)
        if not ingredientes:
            ss["analise_resultado"] = None
            st.error("Informe uma quantidade maior que zero para pelo menos um ingrediente.")
            return
        try:
            ss["analise_resultado"] = analisar_dieta(lote, ingredientes, quantidades)
            ss["analise_assinatura"] = signature
        except Exception as exc:
            ss["analise_resultado"] = None
            st.error(f"Não foi possível analisar a dieta: {exc}")
            return
    res = ss.get("analise_resultado")
    if res is None:
        return
    if ss.get("analise_assinatura") != signature:
        st.info("As quantidades ou preços foram alterados. Clique em 'ANALISAR DIETA INFORMADA' novamente para atualizar a análise.")
        return
    st.warning("AVALIAÇÃO PARCIAL DE DIETA INFORMADA — NÃO É VALIDAÇÃO NUTRICIONAL COMPLETA.")
    st.caption("Esta análise não substitui a avaliação de médico-veterinário ou zootecnista.")
    a, b, c = st.columns(3)
    a.metric("Matéria seca (kg/vaca/dia)", f"{res['total_dm_kg']:.2f}")
    b.metric("Custo (R$/vaca/dia)", f"{res['cost_cow_day']:.2f}")
    c.metric("Custo do lote (R$/dia)", f"{res['cost_herd_day']:.2f}")
    st.dataframe(pd.DataFrame([{"Ingrediente": x["name"], "kg MS": x["kg_dm"],
                                "kg MN": x["kg_mn"], "% MS": x["pct_dm"],
                                "Custo R$": x["cost_brl"]} for x in res["items"]]),
                 use_container_width=True, hide_index=True)
    st.subheader("Indicadores nutricionais")
    indicadores = [
        {"Indicador": "Energia metabolizável", "Ingestão": res["me_in"], "Exigência": res["me_req"], "Unidade": "Mcal/dia",
         "Situação": "Atende" if res["me_in"] >= res["me_req"] else "Abaixo da exigência"},
        {"Indicador": "Proteína metabolizável", "Ingestão": res["mp_in"], "Exigência": res["mp_req"], "Unidade": "g/dia",
         "Situação": "Atende" if res["mp_in"] >= res["mp_req"] else "Abaixo da exigência"},
    ]
    for key, title in [("ndf_pct_dm", "FDN"), ("starch_pct_dm", "Amido"),
                       ("forage_ndf_pct_dm", "FDN de forragens")]:
        indicadores.append({"Indicador": title, "Ingestão": res[key], "Exigência": "—",
                           "Unidade": "% MS", "Situação": "Informativo (sem limite verificado)"})
    minerais = res.get("minerals") or {}
    for sym, label in (("ca", "Cálcio total"), ("p", "Fósforo total")):
        for key, unidade in ((f"{sym}_pct_dm", "% MS"), (f"{sym}_g_day", "g/dia")):
            if minerais.get(key) is not None:
                indicadores.append({"Indicador": label, "Ingestão": minerais[key],
                                   "Exigência": "—", "Unidade": unidade,
                                   "Situação": "Informativo (sem exigência absorvível verificada)"})
    for perfil in (res.get("additional_nutrients") or {}).values():
        if perfil.get("pct_dm") is not None:
            indicadores.append({"Indicador": perfil["label"], "Ingestão": perfil["pct_dm"],
                                "Exigência": "—", "Unidade": "% MS",
                                "Situação": "Informativo (sem exigência validada)"})
    # Requisitos absorvidos obtidos do mesmo modelo NASEM, se retornados.
    for mineral in (res.get("absorbed_mineral_checks") or {}).values():
        if mineral.get("status") != "nao_avaliado":
            indicadores.append({"Indicador": mineral["label"], "Ingestão": mineral["intake"],
                                "Exigência": mineral["requirement"], "Unidade": "g/dia (absorvido)",
                                "Situação": "Atende" if mineral["status"] == "atende" else "Abaixo da exigência"})
    st.caption("Composição bruta (Ca/P total) difere de nutrientes absorvidos; quando disponíveis, "
               "as exigências minerais são do próprio NASEM.")
    st.dataframe(pd.DataFrame(indicadores), hide_index=True, use_container_width=True,
                 column_config={"Ingestão": st.column_config.NumberColumn(format="%.2f")})
    for warning in res["alerts"]:
        st.caption("• " + warning)
    st.caption("A dieta analisada não foi formulada pelo motor. Os resultados não substituem avaliação profissional.")
    from services.analysis_pdf import gerar_pdf_analise_dieta
    try:
        pdf_analise = gerar_pdf_analise_dieta(res, lote)
        st.download_button("Exportar PDF desta análise", pdf_analise,
                           file_name="MuuFeed_analise_dieta.pdf", mime="application/pdf",
                           key="analise_pdf_export")
    except Exception as exc:
        st.warning(f"PDF da análise indisponível: {exc}")


# ---------------------------------------------------------------- Resultados
def _banner_resultado(res) -> None:
    if res.status == "demonstracao":
        st.markdown(f'<div class="mf-demo">EXEMPLO DE LAYOUT — NÃO É UMA DIETA CALCULADA PELO MUUFEED. {res.mensagem}</div>',
                    unsafe_allow_html=True)
    elif res.status in ("otimo", "candidata_experimental"):
        banner("warn" if res.status == "candidata_experimental" else "ok", res.mensagem or "Dieta candidata de menor custo encontrada. Ela atende apenas às restrições "
                                     "listadas como atendidas; confira as não avaliadas antes de qualquer uso.")
    elif res.status == "inviavel":
        banner("err", res.mensagem or "Não há dieta viável com os ingredientes e restrições informados.")
    else:
        banner("warn" if res.status == "escopo_nao_suportado" else "info" if res.status == "nao_conectado" else "err",
               res.mensagem)


def _exportar(res) -> None:
    """PDF para dieta real devolvida pelo formulador (otimo ou candidata_experimental) ou cenário demonstrativo."""
    ss = st.session_state
    real = res is not None and res.status in ("otimo", "candidata_experimental") and bool(res.itens)
    if real or (res is not None and res.status == "demonstracao"):
        demo = res.status == "demonstracao"
        req = ss.get("requisicao_resultado")
        lote = None if demo else (req.lote if req else ss["lote"])
        try:
            pdf = gerar_relatorio_pdf(res, lote, None if (demo or not req) else req.ingredientes,
                                      None if demo else ss.get("data_ref_precos"))
        except Exception as exc:
            st.error(f"Não foi possível gerar o PDF: {exc}")
            return
        st.download_button("Exportar PDF do cenário demonstrativo" if demo else "Exportar relatório PDF", pdf,
                           file_name=f"MuuFeed_{res.id_formulacao or 'relatorio'}.pdf", mime="application/pdf",
                           type="primary")
        if demo:
            st.caption("O PDF do cenário demonstrativo leva marca d'água e não é um relatório de dieta formulada.")
        elif res.status == "candidata_experimental":
            st.caption("O PDF identifica esta dieta como candidata experimental, não validada nutricionalmente.")
    else:
        st.button("Exportar relatório PDF", disabled=True, help="Disponível quando houver uma dieta formulada.")


def pagina_resultados() -> None:
    cat, ss = get_catalogo(), st.session_state
    res, lote = ss["resultado"], ss["lote"]
    st.title("Resultados")
    _exportar(res)
    if res is None:
        st.info("Nenhuma formulação executada ainda. Formule uma dieta ou veja o layout com um cenário demonstrativo.")
        c1, c2 = st.columns(2)
        if c1.button("Ir para Formular dieta", type="primary"):
            ir_para("Formular dieta")
        if c2.button("Ver cenário demonstrativo (layout)"):
            ss["resultado"] = cenario_demonstrativo(cat)
            st.rerun()
        return
    _banner_resultado(res)
    if res.status in ("otimo", "candidata_experimental"):
        st.caption("Esta formulação não substitui a avaliação de médico-veterinário ou zootecnista. "
                   "Confira os requisitos não avaliados antes de qualquer aplicação prática.")
    if not res.itens:
        for label, _ in nao_avaliadas_unicas(res):
            st.caption(f"Não avaliado: {label}")
        return
    req = ss.get("requisicao_resultado")
    lote_ref = req.lote if req else lote  # mesma fonte do PDF: o lote usado na formulação
    n = lote_ref.n_vacas if (lote_ref and res.status in ("otimo", "candidata_experimental")) else None
    resumo = resumo_financeiro(res, n, req.ingredientes if (req and res.status != "demonstracao") else None)
    m = st.columns(4)
    m[0].metric("Consumo de MS (kg MS/vaca/dia)", num(resumo.consumo_ms_kg, 2))
    m[1].metric("Custo por vaca/dia", brl(resumo.custo_vaca_dia))
    m[2].metric("Custo do lote/dia", brl(resumo.custo_lote_dia))
    m[3].metric("Custo mensal estimado (30 dias)", brl(resumo.custo_mes))
    for aviso_fin in resumo.inconsistencias:
        st.warning(f"Inconsistência financeira: {aviso_fin}")
    t1, t2, t3, t4 = st.tabs(["Dieta", "Nutrientes", "Regras e restrições", "Avisos e limitações"])
    with t1:
        linhas = [{"Ingrediente": l.nome, "kg MS/vaca/dia": l.kg_ms, "kg MN/vaca/dia": l.kg_mn,
                   "Preço (R$/kg MN)": l.preco_mn_brl_kg, "Custo (R$/vaca/dia)": l.custo_brl} for l in resumo.linhas]
        linhas.append({"Ingrediente": "Total", "kg MS/vaca/dia": resumo.consumo_ms_kg, "kg MN/vaca/dia": resumo.consumo_mn_kg,
                       "Preço (R$/kg MN)": None, "Custo (R$/vaca/dia)": resumo.custo_vaca_dia})
        df = pd.DataFrame(linhas)
        graf = df.iloc[:-1]
        st.dataframe(df, hide_index=True, use_container_width=True, column_config={
            c: st.column_config.NumberColumn(format="%.2f") for c in df.columns[1:]})
        tot_ms = resumo.consumo_ms_kg
        fig = go.Figure(go.Bar(x=graf["kg MS/vaca/dia"] / tot_ms * 100, y=graf["Ingrediente"], orientation="h",
                               marker_color=VERDE, hovertemplate="%{y}: %{x:.1f}% da MS<extra></extra>"))
        fig.update_layout(title="Composição da dieta (% da MS)", height=80 + 36 * len(graf), margin=dict(l=0, r=10, t=40, b=0),
                          yaxis=dict(autorange="reversed"), xaxis_title="% da matéria seca", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        if res.indicadores:
            rows = []
            for i in res.indicadores:
                limite = ("Mínimo" if i.chave in ("fdn", "fdn_forragens") else "Máximo" if i.chave == "amido"
                          else "Exigência")
                rows.append({"Indicador": i.rotulo, "Valor": i.ingerido, "Unidade": i.unidade,
                             "Tipo de limite": limite if i.exigido is not None else "—",
                             "Limite": i.exigido,
                             "Situação": {"atende": "Atende", "viola": "Não atende",
                                          "informativo": "Informativo (sem limite)",
                                          "nao_avaliado": "Não avaliado"}.get(i.status, i.status)})
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            # Comparação ingerido/exigido é válida para ME e MP. Limites máximo/mínimo
            # de amido/FDN têm outra semântica e não devem entrar no gráfico de 100%.
            par = [i for i in res.indicadores if i.chave in ("me", "mp")
                   and i.ingerido is not None and i.exigido is not None and i.exigido > 0]
            if par:
                fig = go.Figure(go.Bar(x=[i.rotulo for i in par],
                                       y=[i.ingerido / i.exigido * 100 for i in par], marker_color=AZUL))
                fig.add_hline(y=100, line_dash="dash", annotation_text="exigido = 100%")
                fig.update_layout(title="Ingerido ÷ exigido (ME e MP)", height=320,
                                  margin=dict(l=0, r=10, t=40, b=0), plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("O formulador não devolveu indicadores nutricionais.")
        st.caption("FDN e amido sem limites configurados são informativos, não vereditos nutricionais.")
    with t3:
        if res.regras:
            st.markdown("**Regras do sistema especialista acionadas**")
            st.dataframe(pd.DataFrame([{"ID": r.id, "Explicação": r.descricao, "Fonte": r.fonte}
                                       for r in res.regras]), hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma regra acionada informada pelo formulador.")
        for rot, status in (("Restrições atendidas", "atendida"), ("Restrições violadas", "violada")):
            itens = [r for r in res.restricoes if r.status == status]
            if itens:
                st.markdown(f"**{rot}**")
                st.dataframe(pd.DataFrame([{"ID": r.id if not eh_chave_tecnica(r.id) else "—",
                                           "Restrição": rotulo_legivel(r.descricao or r.id),
                                           "Detalhe": r.detalhe or "—"} for r in itens]),
                             hide_index=True, use_container_width=True)
        pendentes = nao_avaliadas_unicas(res)
        if pendentes:
            st.markdown("**Restrições não avaliadas**")
            st.dataframe(pd.DataFrame([{"Requisito": titulo, "Detalhe": detalhe or "—"}
                                       for titulo, detalhe in pendentes]),
                         hide_index=True, use_container_width=True)
    with t4:
        for a in res.avisos:
            st.warning(a)
        st.write("• Esta interface não declara a dieta como nutricionalmente completa: só o que o formulador verificou é exibido.")
        st.write("• Preços marcados como ilustrativos não são preços de mercado confirmados.")
        if res.modelo_referencia:
            st.caption(f"Modelo de referência: {res.modelo_referencia}")
    if st.button("Limpar resultado"):
        ss["resultado"], ss["requisicao_resultado"] = None, None
        st.rerun()
