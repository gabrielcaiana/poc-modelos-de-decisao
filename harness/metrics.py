"""Métricas a partir de runs/<dir>. Uso: python -m harness.metrics runs/<dir>  (gera report.md dentro do run)"""
import json, sys, pathlib, statistics as stt
from collections import Counter, defaultdict

ORD = ["simples", "media", "complexa"]


def ece(confs, oks, bins=10):
    n = len(confs); e = 0.0
    for b in range(bins):
        idx = [i for i, c in enumerate(confs) if b / bins < c <= (b + 1) / bins or (b == 0 and c == 0)]
        if idx: e += len(idx) / n * abs(sum(oks[i] for i in idx) / len(idx) - sum(confs[i] for i in idx) / len(idx))
    return e


def f1_macro(y, p, labels):
    fs = []
    for l in labels:
        tp = sum(a == l and b == l for a, b in zip(y, p)); fp = sum(a != l and b == l for a, b in zip(y, p)); fn = sum(a == l and b != l for a, b in zip(y, p))
        pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
        fs.append(2 * pr * rc / (pr + rc) if pr + rc else 0)
    return sum(fs) / len(fs)


def compute(run):
    run = pathlib.Path(run)
    T = [json.loads(l) for l in (run / "turns.jsonl").read_text().splitlines() if l.strip()]
    J = [json.loads(l) for l in (run / "judge.jsonl").read_text().splitlines()] if (run / "judge.jsonl").exists() else []
    out = {}
    c1 = {t["id"]: t for t in T if t["estrategia"] != "oracle"}  # C1 é idêntica entre estratégias
    D = [json.loads(l) for l in (run / "decisions.jsonl").read_text().splitlines() if l.strip()]
    d1 = {}
    for d in D:
        if d["camada"] == 1: d1.setdefault(d["id"], d)
    if d1:
        y, p, confs, oks, clar_desn, err_aceito, ac = [], [], [], [], 0, 0, 0
        for i, d in d1.items():
            lab = c1[i]["label"]; ch = "clarificar" if d["fallback"] else d["raw_choice"]
            if lab == "clarificar":
                ok = ch == "clarificar" or d["raw_choice"] in (c1[i].get("aceitos") or [])
            else:
                ok = ch == lab
            y.append(lab); p.append(ch); confs.append(d["p_max"]); oks.append(int(d["raw_choice"] == lab))
            if ch == "clarificar" and lab != "clarificar": clar_desn += 1
            if ch != "clarificar": ac += 1; err_aceito += int(not ok)
        n = len(y)
        out["c1"] = {"n": n, "acuracia": sum(a == b or (a == "clarificar" and b == "clarificar") for a, b in zip(y, p)) / n,
                     "f1_macro": f1_macro(y, p, ["devolucao", "suporte", "financeiro", "fora_de_escopo", "clarificar"]),
                     "ece_raw": ece(confs, oks), "taxa_clarificacao": p.count("clarificar") / n,
                     "clarificacao_desnecessaria": clar_desn / n, "erro_entre_aceitas": err_aceito / ac if ac else None,
                     "lat_p50_ms": stt.median(d["lat_ms"] for d in d1.values())}
    d2 = [d for d in D if d["camada"] == 2]
    if d2:
        lab = {t["id"]: t["tier_minimo"] for t in T}
        z = [(ORD.index(d["tier_final"]), ORD.index(lab[d["id"]])) for d in d2 if lab.get(d["id"])]
        out["c2"] = {"n": len(z), "acuracia": sum(a == b for a, b in z) / len(z) if z else None,
                     "sub_roteamento": sum(a < b for a, b in z) / len(z) if z else None,
                     "super_roteamento": sum(a > b for a, b in z) / len(z) if z else None,
                     "taxa_fallback": sum(d["fallback"] for d in d2) / len(d2),
                     "distribuicao": dict(Counter(d["tier_final"] for d in d2))}
    by = defaultdict(list)
    for t in T: by[t["estrategia"]].append(t)
    js = defaultdict(list)
    for j in J:
        if j["media"] is not None: js[j["estrategia"]].append(j["media"])
    out["estrategias"] = {}
    for e, ts in by.items():
        custo = sum(t["custo_geracao"] + t["custo_decisoes"] for t in ts)
        out["estrategias"][e] = {"n": len(ts), "custo_total": custo, "custo_por_msg": custo / len(ts),
                                 "nota_juiz": stt.mean(js[e]) if js[e] else None, "n_juiz": len(js[e])}
    if "always-expensive" in out["estrategias"]:
        base = out["estrategias"]["always-expensive"]["custo_por_msg"]
        for e, v in out["estrategias"].items(): v["economia_vs_caro"] = 1 - v["custo_por_msg"] / base if base else None
    return out


if __name__ == "__main__":
    r = compute(sys.argv[1])
    md = "# Métricas\n\n```json\n" + json.dumps(r, indent=2, ensure_ascii=False) + "\n```\n"
    (pathlib.Path(sys.argv[1]) / "report.md").write_text(md); print(md)
