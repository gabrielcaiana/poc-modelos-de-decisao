"""Tier empírico mínimo e análise de discordância com o rótulo de complexidade.
Funciona com os logs da Fase 2 (turns.jsonl + judge.jsonl) e com o grid da Fase 3 (grid.jsonl).
Definições (todas a partir das notas do juiz para a MESMA mensagem nos 3 tiers):
- relativa: tier mais barato cuja média fica a ≤ delta (0,25) da melhor média entre os 3;
- absoluta: tier mais barato com média ≥ 4,5 E nota de política ≥ 4 ("passa"); se nenhum passa → complexa (nao_resolvido=True).
Uso: python3 -m harness.fase3.tier_empirico fase2 runs/20261012-holdout-live  [--out report/fase3]"""
import json, sys, csv, pathlib
from collections import Counter, defaultdict

ORD = ["simples", "media", "complexa"]
TIER_OF = {"always-cheap": "simples", "always-media": "media", "always-expensive": "complexa"}
ROOT = pathlib.Path(__file__).resolve().parents[2]


def tier_relativo(notas, delta=0.25):
    best = max(notas[t]["media"] for t in ORD)
    return next(t for t in ORD if notas[t]["media"] >= best - delta)


def passa(n):
    return n["media"] >= 4.5 and n.get("politica", 0) >= 4


def tier_absoluto(notas):
    for t in ORD:
        if passa(notas[t]): return t, False
    return "complexa", True


def carregar_fase2(run):
    run = pathlib.Path(run)
    T = [json.loads(l) for l in (run / "turns.jsonl").read_text().splitlines()]
    J = {(j["estrategia"], j["id"]): j for j in map(json.loads, (run / "judge.jsonl").read_text().splitlines())}
    ds = {r["id"]: r for r in map(json.loads, (ROOT / "datasets/mensagens.jsonl").read_text().splitlines())}
    por = defaultdict(dict)
    for t in T:
        if t["estrategia"] in TIER_OF and t["tipo"] == "resposta" and (t["estrategia"], t["id"]) in J:
            j = J[(t["estrategia"], t["id"])]
            por[t["id"]][TIER_OF[t["estrategia"]]] = {"media": j["media"], **j["nota"], "resposta": t["resposta"]}
    itens = []
    for i, n in por.items():
        if len(n) == 3:
            itens.append({"id": i, "mensagem": ds[i]["mensagem"], "label": ds[i]["label"], "tier_rotulo": ds[i].get("tier_minimo"), "notas": n})
    return itens


def analisar(itens):
    rows, conf_rel, conf_abs = [], Counter(), Counter()
    for it in itens:
        n = it["notas"]; rel = tier_relativo(n); ab, nr = tier_absoluto(n); lab = it["tier_rotulo"]
        it.update(tier_relativo=rel, tier_absoluto=ab, nao_resolvido=nr)
        if lab: conf_rel[(lab, rel)] += 1; conf_abs[(lab, ab)] += 1
        rows.append(it)
    lab_ok = [r for r in rows if r["tier_rotulo"]]
    def taxa(k): return sum(r[k] == r["tier_rotulo"] for r in lab_ok) / len(lab_ok)
    # direção da discordância
    def direcao(k):
        c = Counter()
        for r in lab_ok:
            a, b = ORD.index(r[k]), ORD.index(r["tier_rotulo"])
            c["igual" if a == b else ("empirico_mais_barato" if a < b else "empirico_mais_caro")] += 1
        return c
    # quanto o modelo barato já resolve
    barato_passa = sum(passa(r["notas"]["simples"]) for r in rows) / len(rows)
    gap = {t: sum(r["notas"][t]["media"] for r in rows) / len(rows) for t in ORD}
    import re
    feat = defaultdict(lambda: Counter())
    for r in rows:
        k = "com_pedido" if re.search(r"\b1\d{4}\b", r["mensagem"] + " ".join(h.get("content", "") for h in r.get("historico", []))) else "sem_pedido"
        c = feat[k]; c["n"] += 1; c["barato_passa"] += passa(r["notas"]["simples"])
        if r["tier_rotulo"]:
            a, b = ORD.index(r["tier_relativo"]), ORD.index(r["tier_rotulo"])
            c["rotulados"] += 1; c["igual"] += a == b; c["emp_mais_caro"] += a > b; c["emp_mais_barato"] += a < b
    return {"features": feat, "n": len(rows), "n_rotulados": len(lab_ok), "concordancia_relativa": taxa("tier_relativo"),
            "concordancia_absoluta": taxa("tier_absoluto"), "direcao_relativa": direcao("tier_relativo"),
            "direcao_absoluta": direcao("tier_absoluto"), "dist_rotulo": Counter(r["tier_rotulo"] for r in lab_ok),
            "dist_relativo": Counter(r["tier_relativo"] for r in rows), "dist_absoluto": Counter(r["tier_absoluto"] for r in rows),
            "nao_resolvidos": sum(r["nao_resolvido"] for r in rows), "barato_passa": barato_passa, "nota_media_por_tier": gap,
            "conf_rel": conf_rel, "conf_abs": conf_abs}, rows


def relatorio(res, rows, titulo, out):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    pct = lambda x: f"{100*x:.1f}%"
    L = [f"# {titulo}", "", "Neste arquivo eu investigo por que o rótulo de complexidade bate tão pouco com o tier que de fato foi necessário.", "",
         f"- Mensagens com resposta e nota nos 3 tiers: **{res['n']}** ({res['n_rotulados']} com rótulo de tier).",
         f"- Concordância rótulo × tier empírico **relativo** (≤0,25 da melhor nota): **{pct(res['concordancia_relativa'])}**; × **absoluto** (média ≥4,5 e política ≥4): **{pct(res['concordancia_absoluta'])}**.",
         f"- Direção (relativo): {dict(res['direcao_relativa'])}. Direção (absoluto): {dict(res['direcao_absoluta'])}.",
         f"- Nota média por tier: " + ", ".join(f"{t} {v:.2f}" for t, v in res["nota_media_por_tier"].items()) + f". O modelo barato já passa no critério absoluto em **{pct(res['barato_passa'])}** das mensagens; {res['nao_resolvidos']} mensagens não passam em nenhum tier.",
         f"- Distribuição — rótulo: {dict(res['dist_rotulo'])}; empírico relativo: {dict(res['dist_relativo'])}; empírico absoluto: {dict(res['dist_absoluto'])}.", "",
         "## Por presença de número de pedido (exige cruzar dados da ferramenta com a política)", "",
         "| grupo | n | barato passa (absoluto) | rótulo = empírico | empírico mais caro que o rótulo | empírico mais barato que o rótulo |", "|---|---:|---:|---:|---:|---:|"]
    for k, c in sorted(res["features"].items()):
        L.append(f"| {k} | {c['n']} | {pct(c['barato_passa']/c['n'])} | {c['igual']}/{c['rotulados']} | {c['emp_mais_caro']} | {c['emp_mais_barato']} |")
    L += ["", "## Matriz rótulo (linhas) × tier empírico relativo (colunas)", "", "| rótulo | simples | media | complexa |", "|---|---:|---:|---:|"]
    for a in ORD: L.append(f"| {a} | " + " | ".join(str(res["conf_rel"].get((a, b), 0)) for b in ORD) + " |")
    L += ["", "## Matriz rótulo × tier empírico absoluto", "", "| rótulo | simples | media | complexa |", "|---|---:|---:|---:|"]
    for a in ORD: L.append(f"| {a} | " + " | ".join(str(res["conf_abs"].get((a, b), 0)) for b in ORD) + " |")
    L += ["", "## Discordâncias (rótulo ≠ empírico relativo)", "", "| id | mensagem | rótulo | relativo | absoluto | notas simples/media/complexa |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r["tier_rotulo"] and r["tier_rotulo"] != r["tier_relativo"]:
            L.append(f"| {r['id']} | {r['mensagem'][:70]} | {r['tier_rotulo']} | {r['tier_relativo']} | {r['tier_absoluto']} | " + " / ".join(f"{r['notas'][t]['media']:.2f}" for t in ORD) + " |")
    (out / "analise_tier_empirico.md").write_text("\n".join(L) + "\n")
    with open(out / "tier_empirico.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "label", "tier_rotulo", "tier_relativo", "tier_absoluto", "nao_resolvido", "nota_simples", "nota_media", "nota_complexa", "mensagem"])
        for r in rows: w.writerow([r["id"], r["label"], r["tier_rotulo"], r["tier_relativo"], r["tier_absoluto"], r["nao_resolvido"]] + [r["notas"][t]["media"] for t in ORD] + [r["mensagem"]])
    print("\n".join(L[:9]))


def carregar_fase3(grid):
    ds = {r["id"]: r for r in map(json.loads, (ROOT / "datasets/fase3/conversas.jsonl").read_text().splitlines())}
    por = defaultdict(dict)
    for l in (pathlib.Path(grid) / "grid.jsonl").read_text().splitlines():
        r = json.loads(l)
        if r["tipo"] == "ger" and r["juiz"]["media"] is not None:
            por[r["id"]][r["tier"]] = {"media": r["juiz"]["media"], **r["juiz"]["nota"], "resposta": r["resposta"]}
    return [{"id": i, "mensagem": ds[i]["mensagem"], "historico": ds[i]["historico"], "label": ds[i]["label"], "tier_rotulo": ds[i]["tier_regra"], "notas": n}
            for i, n in por.items() if len(n) == 3]


if __name__ == "__main__":
    a = sys.argv[1:]; out = a[a.index("--out") + 1] if "--out" in a else "report/fase3"
    if a[0] == "fase2":
        res, rows = analisar(carregar_fase2(a[1])); relatorio(res, rows, "Análise do tier empírico — dados da Fase 2 (holdout)", out)
    else:
        res, rows = analisar(carregar_fase3(a[1])); relatorio(res, rows, "Análise do tier empírico — Fase 3 (calib + teste, rótulo = regra)", out)
