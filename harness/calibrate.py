"""Calibra τ1/τ2 no split 'calib' (só chamadas MSD1) e congela em config/thresholds.json.
Uso: python -m harness.calibrate --live|--mock [--split calib] [--out runs/<dir>]
Critérios (definidos ANTES de ver o holdout):
- τ1: maximiza utilidade média por mensagem: +1 roteou certo; +1 clarificou ambígua; +0,5 roteou ambígua p/ rótulo aceito;
       -1 roteou errado (inclui ambígua p/ rótulo não aceito); 0 clarificou mensagem clara (custa um turno).
- τ2: maximiza utilidade: +1 tier exato; -2 sub-roteamento (risco de qualidade); -0,5 por nível de super-roteamento (custo).
Desempate: menor τ (menos fallback)."""
import argparse, json, time, pathlib
from .budget import Budget
from .client import Client, load_prices
from . import pipeline as P
from .run import load_items

ROOT = pathlib.Path(__file__).resolve().parents[1]
GRID = [round(x, 3) for x in [0.0, .3, .4, .5, .6, .7, .8, .9, .95, .98, .99, .995, .999]]


def u1(d, it, tau):
    acc = d["p_max"] >= tau; ch = d["raw_choice"]; lab = it["label"]
    if lab == "clarificar":
        return 1 if not acc else (0.5 if ch in (it.get("aceitos") or []) else -1)
    return (1 if ch == lab else -1) if acc else 0


def u2(d, it, tau, fb):
    raw, probs = d["raw_choice"], d["probs"]
    if d["p_max"] >= tau: t = raw
    elif fb == "+1": t = P.TIER_ORDER[min(P.TIER_ORDER.index(raw) + 1, 2)]
    else: t = "complexa"
    a, b = P.TIER_ORDER.index(t), P.TIER_ORDER.index(it["tier_minimo"])
    return 1 if a == b else (-2 if a < b else -0.5 * (a - b))


def main(argv=None):
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mock", action="store_true"); g.add_argument("--live", action="store_true")
    ap.add_argument("--split", default="calib"); ap.add_argument("--out"); ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv)
    budget = Budget(ROOT / ("runs/ledger.json" if a.live else "runs/ledger-mock.json"))
    c = Client(budget, load_prices(), mock=a.mock)
    out = pathlib.Path(a.out or ROOT / "runs" / (time.strftime("%Y%m%d-%H%M%S") + f"-calib-{'live' if a.live else 'mock'}"))
    out.mkdir(parents=True, exist_ok=True)
    items = load_items(a.split); recs = []
    with open(out / "decisions.jsonl", "w") as f:
        for it in items:
            st = P.state_of(it["mensagem"])
            _, d1 = P.camada1(c, st, tau1=0)
            r = {"id": it["id"], "label": it["label"], "aceitos": it.get("aceitos"), "tier_minimo": it.get("tier_minimo"), "d1": {k: d1[k] for k in ("probs", "raw_choice", "p_max", "lat_ms", "cost", "model", "provider")}}
            if it["label"] in ("devolucao", "suporte", "financeiro"):
                _, d2 = P.camada2(c, st, it["label"], tau2=0)  # subagente correto, para isolar a C2
                r["d2"] = {k: d2[k] for k in ("probs", "raw_choice", "score", "p_max", "lat_ms", "cost", "model")}
            recs.append(r); f.write(json.dumps(r, ensure_ascii=False) + "\n")
    t1 = {t: sum(u1(r["d1"], r, t) for r in recs) / len(recs) for t in GRID}
    r2 = [r for r in recs if "d2" in r]
    t2 = {fb: {t: sum(u2(r["d2"], r, t, fb) for r in r2) / len(r2) for t in GRID} for fb in ("complexa", "+1")}
    best1 = max(GRID, key=lambda t: (round(t1[t], 6), -t)); best2 = max(GRID, key=lambda t: (round(t2["complexa"][t], 6), -t))
    res = {"split": a.split, "n": len(recs), "n_c2": len(r2), "utilidade_tau1": t1, "utilidade_tau2": t2,
           "tau1": best1, "tau2": best2, "gasto_usd": budget.session_spent}
    (out / "calibracao.json").write_text(json.dumps(res, indent=2))
    if not a.no_write:
        th = {"_nota": f"Calibrado em {time.strftime('%Y-%m-%d %H:%M %Z')} no split {a.split} ({out.name}). CONGELADO antes do holdout.",
              "tau1": best1, "tau2": best2, "fallback_c2": "complexa", "congelado": True}
        (ROOT / "config/thresholds.json").write_text(json.dumps(th, indent=2, ensure_ascii=False))
    print(json.dumps({k: res[k] for k in ("n", "n_c2", "tau1", "tau2", "gasto_usd")}), out)
    return out


if __name__ == "__main__":
    main()
