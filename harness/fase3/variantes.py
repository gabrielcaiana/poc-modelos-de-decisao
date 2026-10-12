"""Variantes da Camada 2 (MSD1) testadas na Fase 3. Cada variante devolve as probabilidades cruas;
a política (τ) é aplicada depois, offline, no replay — assim dá para varrer τ sem pagar novas chamadas.
- v1_score: pergunta da Fase 2 (score 0-2), sem contexto da ferramenta.
- v2_ctx:   score 0-2 com o resultado da ferramenta no estado e critérios focados em cruzar dados do pedido com a política
            (motivado pela análise da Fase 2: o modelo barato falhou sobretudo quando havia nº de pedido).
- v3_noul:  duas perguntas sim/não na MESMA chamada, com contexto: "o modelo simples basta?" e "precisa do modelo forte?"."""
from mocks.dados import contexto_ferramentas
from ..pipeline import Q_COMPLEXIDADE, MODELS

Q_V2 = {"type": "score", "instructions": "Qual o nível mínimo de modelo para responder CORRETAMENTE esta mensagem, considerando os dados do pedido e a política?",
        "criteria": [
            "simples: dá para responder só com a política ou com um dado direto do pedido, sem cruzar informações nem tirar conclusões",
            "media: é preciso cruzar dados do pedido (status, dias desde a entrega, itens, categoria, pagamento) com a política para decidir o que vale",
            "complexa: vários problemas, exceção de política, cálculo de valores com cupom/parcial, divergência entre o que o cliente diz e os dados, fraude ou cliente irritado"]}
Q_V3 = {
    "basta_simples": {"type": "noul", "instructions": "Um modelo pequeno e barato consegue responder corretamente, sem errar fatos do pedido nem a política?",
                      "criteria": {"true": "Sim: resposta direta, sem cruzar dados ou com cruzamento trivial.", "false": "Não: exige cruzar dados do pedido com a política ou raciocínio cuidadoso."}},
    "precisa_forte": {"type": "noul", "instructions": "Esta mensagem exige o modelo mais forte (vários problemas, exceções, cálculos, divergência de dados, risco ou cliente irritado)?",
                      "criteria": {"true": "Sim, exige o modelo mais forte.", "false": "Não, um modelo intermediário resolve."}}}
ORD = ["simples", "media", "complexa"]


def estado(item, subagente, com_ctx):
    st = {"historico": item.get("historico", []), "mensagem_cliente": item["mensagem"], "subagente": subagente}
    if com_ctx:
        ctx = contexto_ferramentas(subagente, item["mensagem"], item.get("historico"))
        st["dados_ferramentas"] = "\n".join(l for l in ctx.splitlines() if l.startswith("[ferramenta"))  # só o resultado da consulta (a política é fixa)
    return st


def decidir(client, item, subagente, variante):
    if variante == "v1_score":
        d = client.decide(MODELS["msd1"], estado(item, subagente, False), {"complexidade": Q_COMPLEXIDADE})
        probs = {ORD[int(k)]: v for k, v in d["answers"]["complexidade"]["probabilities"].items()}
    elif variante == "v2_ctx":
        d = client.decide(MODELS["msd1"], estado(item, subagente, True), {"complexidade": Q_V2})
        probs = {ORD[int(k)]: v for k, v in d["answers"]["complexidade"]["probabilities"].items()}
    elif variante == "v3_noul":
        d = client.decide(MODELS["msd1"], estado(item, subagente, True), Q_V3)
        a = d["answers"]
        def p_true(x):
            if "noul" in x: return float(x["noul"])
            pr = x.get("probabilities", {}); return float(pr.get("true", pr.get("1", 0.5)))
        probs = {"p_basta_simples": p_true(a["basta_simples"]), "p_precisa_forte": p_true(a["precisa_forte"])}
    else:
        raise ValueError(variante)
    return {"variante": variante, "probs": probs, "cost": d["cost"], "lat_ms": d["lat_ms"], "model": d.get("model"), "usage": d.get("usage")}


def politica(rec, variante, params):
    """Aplica τ às probabilidades cruas -> tier. params: v1/v2 {tau, fallback}; v3 {ta, tb}."""
    p = rec["probs"]
    if variante in ("v1_score", "v2_ctx"):
        raw = max(ORD, key=lambda t: p[t])
        if p[raw] >= params["tau"]: return raw
        return "complexa" if params.get("fallback", "complexa") == "complexa" else ORD[min(ORD.index(raw) + 1, 2)]
    if p["p_basta_simples"] >= params["ta"]: return "simples"
    return "complexa" if p["p_precisa_forte"] >= params["tb"] else "media"


def grade(variante):
    taus = [0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98]
    if variante == "v3_noul":
        g = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        return [{"ta": a, "tb": b} for a in g for b in g]
    return [{"tau": t, "fallback": f} for t in taus for f in ("complexa", "+1")]
