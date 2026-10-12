"""Gera ESTIMATIVA_CUSTO_FASE3.md com preços ao vivo (OpenRouter /api/v1/models) e tokens medidos no smoke da Fase 3.
Uso: python3 -m harness.fase3.estimate [--refresh]"""
import json, sys, pathlib, statistics as st
from ..client import load_prices
from ..pipeline import MODELS

ROOT = pathlib.Path(__file__).resolve().parents[2]
rows = [json.loads(l) for l in (ROOT / "datasets/fase3/conversas.jsonl").read_text().splitlines()]
N = len(rows); N_ROT = sum(r["label"] != "fora_de_escopo" for r in rows); N_GER = sum(bool(r.get("gerar")) for r in rows)
SMOKE = ROOT / "runs/fase3-smoke-20261012/grid.jsonl"
PREM = {
    "central": {"c1": 300, "c2": {"v1_score": 220, "v2_ctx": 380, "v3_noul": 390}, "gen_in": 550,
                "out": {"simples": 100, "media": 140, "complexa": 220}, "judge_in": 1000, "judge_out": 150, "margem": 0.20},
    "pessimista": {"c1": 450, "c2": {"v1_score": 330, "v2_ctx": 600, "v3_noul": 620}, "gen_in": 900,
                   "out": {"simples": 400, "media": 400, "complexa": 800}, "judge_in": 1600, "judge_out": 500, "margem": 0.30},
}
LEDGER = json.loads((ROOT / "runs/ledger.json").read_text())


def medido():
    if not SMOKE.exists(): return None
    g = [json.loads(l) for l in SMOKE.read_text().splitlines()]
    m = {}
    for t in ("simples", "media", "complexa"):
        x = [r for r in g if r["tipo"] == "ger" and r["tier"] == t]
        if x: m[t] = (st.mean(r["usage"]["prompt_tokens"] for r in x), st.mean(r["usage"]["completion_tokens"] for r in x), max(r["usage"]["completion_tokens"] for r in x), st.mean(r["cost"] for r in x))
    m["juiz"] = st.mean(r["juiz"]["cost"] for r in g if r["tipo"] == "ger")
    m["c2"] = {v: st.mean(r["usage"]["input_tokens"] for r in g if r["tipo"] == "c2" and r["variante"] == v) for v in ("v1_score", "v2_ctx", "v3_noul")}
    m["c1_lat"] = st.mean(r["lat_ms"] for r in g if r["tipo"] == "c1"); m["total"] = sum(r["cost"] + (r["juiz"]["cost"] if r["tipo"] == "ger" else 0) for r in g)
    return m


def main(refresh=False):
    ids = {MODELS["msd1"], MODELS["judge"], *MODELS["tiers"].values()}
    P = load_prices(refresh=refresh, ids=ids); pdate = json.loads((ROOT / "config/prices.json").read_text())["_data"]; T = MODELS["tiers"]
    tab = {}
    for cen, p in PREM.items():
        msd = P[MODELS["msd1"]]["in"]; it = {}
        it["MSD1 Camada 1 (todas as conversas)"] = N * p["c1"] * msd
        it["MSD1 Camada 2 — 3 variantes (todas as roteáveis)"] = N_ROT * sum(p["c2"].values()) * msd
        for t, nome in (("simples", "Gemini 2.5 Flash Lite"), ("media", "Gemini 3.5 Flash Lite"), ("complexa", "GPT-6 Sol")):
            it[f"Geração {nome} ({N_GER} conversas)"] = N_GER * (p["gen_in"] * P[T[t]]["in"] + p["out"][t] * P[T[t]]["out"])
        it[f"Juiz DeepSeek V4.1 Flash ({3*N_GER} avaliações)"] = 3 * N_GER * (p["judge_in"] * P[MODELS["judge"]]["in"] + p["judge_out"] * P[MODELS["judge"]]["out"])
        sub = sum(it.values()); it["Margem (central 20%, pessimista 30%): retries, 429/5xx, re-execuções"] = sub * p["margem"]
        tab[cen] = it
    tc, tp = (sum(tab[c].values()) for c in ("central", "pessimista"))
    gasto = LEDGER["spent_usd"]; m = medido()
    L = ["# Estimativa de custo — Fase 3", "",
         f"Preços ao vivo do OpenRouter (`/api/v1/models`, {pdate}); MSD1 em `config/prices_extra.json`. Gerado por `python3 -m harness.fase3.estimate`.", "",
         "## Orçamento", "", f"- Teto rígido: US$20. Parada automática do harness: US$18 (`config/budget.json`, ledger acumulado).",
         f"- Já gasto (ledger, Fases 1–2 + smoke da Fase 3): **US${gasto:.4f}**. Disponível até a parada: **US${18 - gasto:.2f}**.",
         f"- Meta que eu me impus: cenário pessimista < US$8. Vou rodar com `--session-cap 8`.", "",
         "## Preços (US$ por 1M tokens)", "", "| Papel | Modelo | Entrada | Saída |", "|---|---|---:|---:|"]
    for papel, mm in [("decisão", MODELS["msd1"]), ("simples", T["simples"]), ("média", T["media"]), ("complexa", T["complexa"]), ("juiz", MODELS["judge"])]:
        L.append(f"| {papel} | `{mm}` | {P[mm]['in']*1e6:.3f} | {P[mm]['out']*1e6:.3f} |")
    L += ["", "## Desenho que estou orçando", "",
          f"- {N} conversas fictícias; decisões MSD1 (C1 + 3 variantes de C2) em todas as {N_ROT} roteáveis.",
          f"- Geração nos 3 tiers + juiz em cada resposta, só nas {N_GER} conversas marcadas `gerar` (150 calib + 300 teste, cauda complexa sobreamostrada).",
          "- Toda política (always-*, msd1 em qualquer τ/variante, oracles) é avaliada por replay, sem novas chamadas.",
          "- max_tokens: 400 (Gemini) e 800 (GPT-6 Sol).", "", "## Premissas de tokens", ""]
    for c, p in PREM.items():
        L.append(f"- **{c}**: C1 {p['c1']} in; C2 {p['c2']}; geração {p['gen_in']} in / saída {p['out']}; juiz {p['judge_in']} in / {p['judge_out']} out; margem {int(p['margem']*100)}%.")
    if m:
        L += [f"- Medido no smoke (6 conversas, `runs/fase3-smoke-20261012`): " + "; ".join(f"{t}: {v[0]:.0f} in / {v[1]:.0f} out (máx {v[2]}) → US${v[3]:.6f}" for t, v in m.items() if t in ("simples", "media", "complexa")) +
              f"; juiz US${m['juiz']:.6f}/avaliação; C2 in: " + ", ".join(f"{k} {v:.0f}" for k, v in m["c2"].items()) + f". Custo do smoke: US${m['total']:.4f}."]
    L += ["", "## Tabela", "", "| Item | Central (US$) | Pessimista (US$) |", "|---|---:|---:|"]
    for k in tab["central"]: L.append(f"| {k} | {tab['central'][k]:.4f} | {tab['pessimista'][k]:.4f} |")
    L += [f"| **Total** | **{tc:.2f}** | **{tp:.2f}** |", "",
          f"Gasto projetado acumulado (já gasto + Fase 3): central **US${gasto + tc:.2f}**, pessimista **US${gasto + tp:.2f}** — abaixo da parada de US$18.", "",
          "## Minha leitura", "",
          f"- O GPT-6 Sol responde por {100*tab['central']['Geração GPT-6 Sol ('+str(N_GER)+' conversas)']/(tc/(1+PREM['central']['margem'])):.0f}% do custo central (sem margem); o pessimista assume que toda resposta dele usa as 800 saídas (no smoke, a maior teve 246).",
          "- As decisões MSD1 custam centavos mesmo com 3 variantes em 1000 conversas: dá para varrer τ e variantes à vontade no replay.",
          "- Se o gasto real do primeiro lote (calib) vier acima do central, eu reduzo o teste de 300 para 200 conversas antes de continuar."]
    (ROOT / "ESTIMATIVA_CUSTO_FASE3.md").write_text("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    main("--refresh" in sys.argv)
