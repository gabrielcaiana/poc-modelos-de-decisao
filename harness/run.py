"""Executa estratégias sobre o dataset e grava runs/<timestamp>/{decisions,turns}.jsonl + manifest.json.
Uso: python -m harness.run --mock --split all --estrategias msd1,always-cheap,always-expensive
     python -m harness.run --live --limit 3 --session-cap 0.10   (smoke)
Aborta (BudgetExceeded) antes de ultrapassar config/budget.json:stop_at_usd."""
import argparse, json, time, hashlib, pathlib, sys
from .budget import Budget, BudgetExceeded
from .client import Client, load_prices
from . import pipeline as P

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_items(split="all", limit=None, ids=None):
    rows = [json.loads(l) for l in (ROOT / "datasets/mensagens.jsonl").read_text().splitlines() if l.strip()]
    if split != "all": rows = [r for r in rows if r["split"] == split]
    if ids: rows = [r for r in rows if r["id"] in ids]
    return rows[:limit] if limit else rows


def strip(d):
    return {k: v for k, v in d.items() if k not in ("answers",)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mock", action="store_true"); g.add_argument("--live", action="store_true")
    ap.add_argument("--split", default="all"); ap.add_argument("--limit", type=int); ap.add_argument("--ids")
    ap.add_argument("--estrategias", default="msd1,always-cheap,always-expensive")
    ap.add_argument("--session-cap", type=float, help="teto extra de gasto para esta execução (US$)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    models = P.MODELS
    ids = {models["msd1"], models["judge"], *models["tiers"].values()}
    prices = load_prices(refresh=a.live, ids=ids)
    ledger = ROOT / ("runs/ledger.json" if a.live else "runs/ledger-mock.json")
    budget = Budget(ledger, session_cap=a.session_cap)
    client = Client(budget, prices, mock=a.mock)
    out = pathlib.Path(a.out or ROOT / "runs" / (time.strftime("%Y%m%d-%H%M%S") + ("-mock" if a.mock else "-live")))
    out.mkdir(parents=True, exist_ok=True)
    items = load_items(a.split, a.limit, set(a.ids.split(",")) if a.ids else None)
    ds = (ROOT / "datasets/mensagens.jsonl").read_bytes()
    manifest = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "modo": "mock" if a.mock else "live", "models": models,
                "thresholds": P.TH, "dataset_sha256": hashlib.sha256(ds).hexdigest(), "n_itens": len(items),
                "estrategias": a.estrategias.split(","), "precos": {k: prices.get(k) for k in ids},
                "ledger_antes_usd": budget.spent, "origem": "box Linux (shared), America/Sao_Paulo"}
    cache_c1, status = {}, "ok"
    fd, ft = open(out / "decisions.jsonl", "a"), open(out / "turns.jsonl", "a")
    try:
        for est in a.estrategias.split(","):
            for it in items:
                r = P.turno(client, est, it, cache_c1)
                for d in r["decisoes"]:
                    fd.write(json.dumps({"ts": time.time(), "estrategia": est, "id": it["id"], **strip(d)}, ensure_ascii=False) + "\n")
                gen = r["geracao"] or {}
                cdec = sum(d["cost"] for d in r["decisoes"])
                ft.write(json.dumps({"ts": time.time(), "estrategia": est, "id": it["id"], "label": it["label"], "aceitos": it.get("aceitos"),
                                     "tier_minimo": it.get("tier_minimo"), "tipo": r["tipo"], "subagente": r["subagente"],
                                     "tier": r["tier"], "modelo": gen.get("model"), "finish": gen.get("finish"), "max_tokens": P.MAX_TOKENS.get(r["tier"]) if r["tier"] else None, "provider": gen.get("provider"),
                                     "usage": gen.get("usage"), "custo_geracao": gen.get("cost", 0.0), "custo_decisoes": cdec,
                                     "lat_geracao_ms": gen.get("lat_ms"), "lat_decisoes_ms": sum(d["lat_ms"] for d in r["decisoes"]),
                                     "mensagem": it["mensagem"], "resposta": r["resposta"], "contexto": gen.get("contexto")}, ensure_ascii=False) + "\n")
                fd.flush(); ft.flush()
    except BudgetExceeded as e:
        status = f"ABORTADO_ORCAMENTO: {e}"
        print(status, file=sys.stderr)
    finally:
        fd.close(); ft.close()
        manifest.update({"fim": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "status": status, "ledger_depois_usd": budget.spent,
                         "gasto_sessao_usd": budget.session_spent})
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"{out}  status={status}  gasto_sessao=US${budget.session_spent:.6f}  ledger=US${budget.spent:.6f}")
    return out


if __name__ == "__main__":
    main()
