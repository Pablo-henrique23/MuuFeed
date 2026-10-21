"""Páginas do MuuFeed. Só apresentação: nenhuma regra nutricional mora aqui."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from models import ESTADOS, PADROES_AVANCADOS, Lote
from services.demo_scenario import cenario_demonstrativo
from services.pdf_report import gerar_relatorio_pdf
from services.formulation_service import executar_formulacao, formulador_conectado
from ui.state import adicionar, get_catalogo, ir_para, montar_requisicao
from ui.theme import banner, brl, card, num

ROTULO_STATUS = {
    None: "Não calculado", "nao_conectado": "Formulador não conectado",
    "demonstracao": "Cenário demonstrativo (não calculado)", "otimo": "Dieta candidata calculada",
    "inviavel": "Sem solução viável", "escopo_nao_suportado": "Fora do escopo", "erro": "Erro na formulação",
}
VERDE, AZUL = "#1F6B4F", "#2B6CB0"


# ---------------------------------------------------------------- Painel
def pagina_painel() -> None:
    ss, lote, res = st.session_state, st.session_state["lote"], st.session_state["resultado"]
    st.markdown('<div class="mf-hero"><h1>MuuFeed</h1><p>Sistema especialista para formulação inteligente e '
                'econômica de dietas para bovinos leiteiros.</p></div>', unsafe_allow_html=True)
    custo = res.custo_vaca_dia if res and res.status == "otimo" else None
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
              ("Formular a dieta", bool(res and res.status == "otimo"), "Formular dieta")]
    st.subheader("Como formular em três passos")
    for i, (txt, feito, destino) in enumerate(passos):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"{'✅' if feito else '⬜'} **{i + 1}. {txt}**" + (f" — {n_ing} ingrediente(s)" if i == 1 and n_ing else ""))
        if c2.button("Abrir", key=f"abrir_{i}", use_container_width=True):
            ir_para(destino)
    st.caption("Decisões nutricionais são tomadas por código determinístico e base de conhecimento explícita. "
               "Nenhum modelo de linguagem calcula dietas.")


# ---------------------------------------------------------------- Lote
CAMPOS_FORM = {"f_nome": "", "f_n": 50, "f_raca": "", "f_idade": 4.0, "f_idade_un": "anos", "f_peso": 600.0,
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
        raca = a.text_input("Raça (informativa)", key="f_raca", help="Não altera as exigências por si só; entram o peso e a produção.")
        estado = b.selectbox("Estado fisiológico", list(ESTADOS), format_func=ESTADOS.get, key="f_estado")
        c1, c2 = a.columns([2, 1])
        idade = c1.number_input("Idade média", 0.0, 40.0, key="f_idade", step=0.25, format="%.2f")
        un = c2.selectbox("Unidade", ["anos", "meses"], key="f_idade_un")
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
            ss["lote"], ss["resultado"], ss["requisicao_resultado"] = lote, None, None  # novo lote invalida o resultado
            st.success(f"Lote salvo. Idade usada pelo formulador: {lote.idade_dias:,.0f} dias.".replace(",", "."))
            for w in avisos:
                st.warning(w)


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
    req, erros = montar_requisicao()
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


# ---------------------------------------------------------------- Resultados
def _banner_resultado(res) -> None:
    if res.status == "demonstracao":
        st.markdown(f'<div class="mf-demo">EXEMPLO DE LAYOUT — NÃO É UMA DIETA CALCULADA PELO MUUFEED. {res.mensagem}</div>',
                    unsafe_allow_html=True)
    elif res.status == "otimo":
        banner("ok", res.mensagem or "Dieta candidata de menor custo encontrada. Ela atende apenas às restrições "
                                     "listadas como atendidas; confira as não avaliadas antes de qualquer uso.")
    elif res.status == "inviavel":
        banner("err", res.mensagem or "Não há dieta viável com os ingredientes e restrições informados.")
    else:
        banner("warn" if res.status == "escopo_nao_suportado" else "info" if res.status == "nao_conectado" else "err",
               res.mensagem)


def _exportar(res) -> None:
    """PDF só para resultado real (otimo) ou para o cenário demonstrativo, com marca d'água."""
    ss = st.session_state
    if res is not None and res.status in ("otimo", "demonstracao"):
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
    if not res.itens:
        for t in res.nao_avaliadas:
            st.caption(f"Não avaliado: {t}")
        return
    n = lote.n_vacas if (lote and res.status == "otimo") else None
    m = st.columns(3)
    m[0].metric("Custo por vaca/dia", brl(res.custo_vaca_dia))
    m[1].metric("Custo do lote/dia", brl(res.custo_vaca_dia * n) if n else "—")
    m[2].metric("Custo mensal estimado (30 dias)", brl(res.custo_vaca_dia * n * 30) if n else "—")
    t1, t2, t3, t4 = st.tabs(["Dieta", "Nutrientes", "Regras e restrições", "Avisos e limitações"])
    with t1:
        df = pd.DataFrame([{"Ingrediente": i.nome, "kg MS/vaca/dia": i.kg_ms, "kg MN/vaca/dia": i.kg_mn,
                            "Custo (R$/vaca/dia)": i.custo_brl} for i in res.itens])
        st.dataframe(df, hide_index=True, use_container_width=True, column_config={
            c: st.column_config.NumberColumn(format="%.2f") for c in df.columns[1:]})
        tot_ms = df["kg MS/vaca/dia"].sum()
        fig = go.Figure(go.Bar(x=df["kg MS/vaca/dia"] / tot_ms * 100, y=df["Ingrediente"], orientation="h",
                               marker_color=VERDE, hovertemplate="%{y}: %{x:.1f}% da MS<extra></extra>"))
        fig.update_layout(title="Composição da dieta (% da MS)", height=80 + 36 * len(df), margin=dict(l=0, r=10, t=40, b=0),
                          yaxis=dict(autorange="reversed"), xaxis_title="% da matéria seca", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with t2:
        par = [i for i in res.indicadores if i.ingerido is not None and i.exigido]
        if par:
            cols = st.columns(len(par))
            for c, i in zip(cols, par):
                c.metric(i.rotulo, num(i.ingerido, 1, i.unidade), f"exigido: {num(i.exigido, 1, i.unidade)}", delta_color="off")
            fig = go.Figure(go.Bar(x=[i.rotulo for i in par], y=[i.ingerido / i.exigido * 100 for i in par], marker_color=AZUL))
            fig.add_hline(y=100, line_dash="dash", annotation_text="exigido = 100%")
            fig.update_layout(title="Ingerido ÷ exigido (%)", height=320, margin=dict(l=0, r=10, t=40, b=0),
                              plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("O formulador não devolveu indicadores com valores ingerido e exigido.")
        st.caption("Indicadores informativos não constituem veredito de adequação.")
    with t3:
        if res.regras:
            st.markdown("**Regras do sistema especialista acionadas**")
            st.dataframe(pd.DataFrame([vars(r) for r in res.regras]), hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma regra acionada informada pelo formulador.")
        for rot, st_ in (("Restrições atendidas", "atendida"), ("Restrições violadas", "violada"), ("Restrições não avaliadas", "nao_avaliada")):
            itens = [r for r in res.restricoes if r.status == st_]
            if itens:
                st.markdown(f"**{rot}**")
                st.dataframe(pd.DataFrame([vars(r) for r in itens]).drop(columns="status"), hide_index=True, use_container_width=True)
        if res.nao_avaliadas:
            st.markdown("**Itens não avaliados**")
            for t in res.nao_avaliadas:
                st.write(f"• {t}")
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
