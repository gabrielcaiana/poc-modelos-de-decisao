"""Gera ESTIMATIVA_CUSTO.md a partir de config/prices.json (preços ao vivo do OpenRouter) + premissas de tokens medidas no smoke.
Uso: python -m harness.estimate [--refresh]"""
import json, sys, pathlib
from .client import load_prices
from .pipeline import MODELS

ROOT = pathlib.Path(__file__).resolve().parents[1]
rows = [json.loads(l) for l in (ROOT / "datasets/mensagens.jsonl").read_text().splitlines() if l.strip()]
# Fase 2: decisões em TODOS os splits (calibração + teste); geração só no split de teste (holdout)
N_ALL = len(rows)
rows_t = [r for r in rows if r["split"] == "holdout"]
N = len(rows_t)
N_GER = sum(r["label"] in ("devolucao", "suporte", "financeiro") for r in rows_t)
TIERS = {t: sum(r.get("tier_minimo") == t for r in rows_t) for t in ("simples", "media", "complexa")}

# Premissas (tokens por chamada). "central" ~ smoke de 12/10/2026 arredondado p/ cima; "pessimista" = teto max_tokens.
PREM = {
    "central": {"gen_in": 550, "out": {"simples": 120, "media": 160, "complexa": 300}, "c1_in": 200, "c2_in": 150,
                "judge_in": 900, "judge_out": 200},
    "pessimista": {"gen_in": 900, "out": {"simples": 400, "media": 400, "complexa": 800}, "c1_in": 300, "c2_in": 250,
                   "judge_in": 1400, "judge_out": 500},
}
# Mistura de tiers assumida p/ a estratégia msd1 (do smoke + labels): 40% simples, 40% média, 20% complexa (+fallback)
MIX_MSD1 = {"simples": .40, "media": .40, "complexa": .20}
MARGEM = 0.5  # retries, repetições, re-rodadas, variação de tokens


def main(refresh=False):
    ids = {MODELS["msd1"], MODELS["judge"], *MODELS["tiers"].values()}
    P = load_prices(refresh=refresh, ids=ids)
    pdate = json.loads((ROOT / "config/prices.json").read_text())["_data"]
    T = MODELS["tiers"]

    def gen(tier, n, pr):
        m = T[tier]; return n * (pr["gen_in"] * P[m]["in"] + pr["out"][tier] * P[m]["out"])

    out = {}
    for cen, pr in PREM.items():
        msd = P[MODELS["msd1"]]["in"]
        c1 = N * pr["c1_in"] * msd
        c2 = N_GER * pr["c2_in"] * msd
        items = {
            "MSD1 Camada 1 (holdout; reaproveitada nas estratégias)": c1,
            "MSD1 Camada 2 (msgs roteadas)": c2,
            "MSD1 calibração τ1/τ2 em todos os splits (C1+C2) + 3 repetições de latência": (N_ALL / N + 3) * (c1 + c2),
            "always-cheap (Gemini 2.5 Flash Lite)": gen("simples", N_GER, pr),
            "always-media (Gemini 3.5 Flash Lite; p/ rótulo empírico de tier)": gen("media", N_GER, pr),
            "always-expensive (GPT-6 Sol)": gen("complexa", N_GER, pr),
            "msd1 (mistura 40/40/20)": sum(gen(t, N_GER * f, pr) for t, f in MIX_MSD1.items()),
            "msd1-up1 (variante fallback +1 tier; ~ msd1)": sum(gen(t, N_GER * f, pr) for t, f in MIX_MSD1.items()),
            "oracle (tier do rótulo)": sum(gen(t, n, pr) for t, n in TIERS.items()),
            "Juiz DeepSeek V4.1 Flash (todas as respostas: 6 configs)": 6 * N_GER * (pr["judge_in"] * P[MODELS["judge"]]["in"] + pr["judge_out"] * P[MODELS["judge"]]["out"]),
        }
        sub = sum(items.values())
        items[f"Margem {int(MARGEM*100)}% (retries, re-rodadas)"] = sub * MARGEM
        out[cen] = items

    L = ["# Estimativa de custo — POC modelos de decisão (Fase 2)", "",
         f"Gerado por `python -m harness.estimate`. Preços: `config/prices.json` (OpenRouter /api/v1/models, {pdate}) + MSD1 de `config/prices_extra.json`.",
         "Orçamento: **teto rígido US$20; o harness aborta ao atingir US$18** (`config/budget.json`). Também configurei o limite de US$20 na própria chave do OpenRouter (GET /api/v1/key: `limit=20`).", "",
         "## Preços ao vivo (US$ por 1M tokens)", "", "| Papel | Modelo | Entrada | Saída |", "|---|---|---|---|"]
    for papel, m in [("decisão (C1/C2)", MODELS["msd1"]), ("tier simples", T["simples"]), ("tier média", T["media"]),
                     ("tier complexa", T["complexa"]), ("juiz", MODELS["judge"])]:
        L.append(f"| {papel} | `{m}` | {P[m]['in']*1e6:.3f} | {P[m]['out']*1e6:.3f} |")
    L += ["", "## Premissas que usei", "",
          f"- Dataset: {N_ALL} mensagens; decisões MSD1 em todas; geração só no holdout ({N} msgs, {N_GER} chegam à geração; fora_de_escopo/ambíguas param na resposta fixa).",
          "- max_tokens: 400 (Gemini) e 800 (GPT-6 Sol, v2).",
          f"- Tiers rotulados: {TIERS}.",
          "- Tokens por chamada (central ≈ smoke de 12/10/2026, arredondado para cima; pessimista ≈ teto de `max_tokens` (Sol 800)):"]
    for cen, pr in PREM.items():
        L.append(f"  - **{cen}**: geração {pr['gen_in']} in / saída {pr['out']} (GPT-6 Sol inclui tokens de raciocínio); C1 {pr['c1_in']} in; C2 {pr['c2_in']} in; juiz {pr['judge_in']} in / {pr['judge_out']} out.")
    L += ["- O que medi no smoke: C1 ≈ 183–192 tokens, C2 ≈ 130–139 tokens (US$0,000006–0,000008 por decisão); geração ≈ 340–480 tokens in; saída Gemini 45–122, GPT-6 Sol 79–277 (39–187 de raciocínio).",
          "- Assumi para msd1 a mistura 40% simples / 40% média / 20% complexa (fallback de baixa confiança sobe para complexa).",
          "- O juiz avalia TODAS as respostas das 6 configurações (é barato); eu reviso manualmente uma amostra cega de 40.",
          "- Cada mensagem é um turno único (sem conversas multi-turno nesta POC).", "",
          "## Tabela", "", "| Item | Central (US$) | Pessimista (US$) |", "|---|---:|---:|"]
    for k in out["central"]:
        L.append(f"| {k} | {out['central'][k]:.4f} | {out['pessimista'][k]:.4f} |")
    tc, tp = sum(out["central"].values()), sum(out["pessimista"].values())
    L += [f"| **Total** | **{tc:.2f}** | **{tp:.2f}** |", "",
          "## Por modelo (central, sem margem)", "", "| Modelo | US$ |", "|---|---:|"]
    c = out["central"]
    per = {MODELS["msd1"]: sum(v for k, v in c.items() if k.startswith("MSD1")),
           T["simples"]: c["always-cheap (Gemini 2.5 Flash Lite)"],
           T["media"]: c["always-media (Gemini 3.5 Flash Lite; p/ rótulo empírico de tier)"],
           T["complexa"]: c["always-expensive (GPT-6 Sol)"]}
    pc = PREM["central"]
    for t, f in MIX_MSD1.items(): per[T[t]] += 2 * gen(t, N_GER * f, pc)
    for t, n in TIERS.items(): per[T[t]] += gen(t, n, pc)
    per[MODELS["judge"]] = c["Juiz DeepSeek V4.1 Flash (todas as respostas: 6 configs)"]
    for m, v in per.items(): L.append(f"| `{m}` | {v:.4f} |")
    L += ["", "## Minha leitura", "",
          f"- Mesmo no cenário pessimista o experimento completo fica em ~US${tp:.2f}, bem abaixo da parada de US$18. Isso dá folga para: dobrar o dataset, rodar a variante de fallback \"+1 tier\", testar C1+C2 numa única chamada, e repetir a rodada.",
          "- O item dominante é o GPT-6 Sol (always-expensive + parte de msd1/oracle). O MSD1 e o juiz custam centavos.",
          "- O gasto real que tive está em `runs/ledger.json` e no README.",
          "- Depois da rodada eu confiro com o painel do OpenRouter (`Client.key_usage()`)."]
    (ROOT / "ESTIMATIVA_CUSTO.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main("--refresh" in sys.argv)
