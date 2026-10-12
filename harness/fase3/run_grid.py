"""Fase 3 — coleta em grade (retomável): para cada conversa,
  C1 (MSD1 choice, com histórico) -> para as roteadas: C2 nas 3 variantes (só decisões, baratas);
  para os itens marcados "gerar": resposta nos 3 tiers com o subagente escolhido pela C1 + juiz em cada uma.
Toda política (always-*, msd1 com qualquer τ/variante, oracle) é avaliada depois por REPLAY desses registros,
com pareamento perfeito (mesmas mensagens e mesmas respostas). Ver harness/fase3/replay.py.
Uso: python -m harness.fase3.run_grid --mock|--live [--split calib|teste|all] [--limit N] [--ids c0001,..]
                                      [--sem-geracao] [--session-cap US$] --out runs/<dir>"""
import argparse, json, time, hashlib, pathlib, sys
from ..budget import Budget, BudgetExceeded
from ..client import Client, load_prices
from .. import pipeline as P
from ..judge import SYS as JUIZ_SYS, parse
from . import variantes as V

ROOT = pathlib.Path(__file__).resolve().parents[2]
DS = ROOT / "datasets/fase3/conversas.jsonl"
VARS = ["v1_score", "v2_ctx", "v3_noul"]


def load(split="all", limit=None, ids=None):
    rows = [json.loads(l) for l in DS.read_text().splitlines() if l.strip()]
    if split != "all": rows = [r for r in rows if r["split"] == split]
    if ids: rows = [r for r in rows if r["id"] in ids]
    return rows[:limit] if limit else rows


def julgar(client, item, ctx, resposta):
    hist = "\n".join(f"{h['role'].upper()}: {h['content']}" for h in item.get("historico", []))
    u = f"CONTEXTO:\n{ctx}\n\nHISTÓRICO:\n{hist or '(sem histórico)'}\n\nCLIENTE: {item['mensagem']}\n\nRESPOSTA DO ATENDENTE:\n{resposta}"
    r = client.chat(P.MODELS["judge"], [{"role": "system", "content": JUIZ_SYS}, {"role": "user", "content": u}], max_tokens=500, temperature=0,
                    extra={"reasoning": {"enabled": False}, "response_format": {"type": "json_object"}})
    n = parse(r["text"]) or {}
    media = sum(n.get(k, 0) for k in ("correcao", "resolucao", "politica", "tom")) / 4 if n else None
    return {"nota": n, "media": media, "cost": r["cost"], "lat_ms": r["lat_ms"]}


def main(argv=None):
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mock", action="store_true"); g.add_argument("--live", action="store_true")
    ap.add_argument("--split", default="all"); ap.add_argument("--limit", type=int); ap.add_argument("--ids")
    ap.add_argument("--sem-geracao", action="store_true"); ap.add_argument("--workers", type=int, default=1); ap.add_argument("--session-cap", type=float); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    ids_m = {P.MODELS["msd1"], P.MODELS["judge"], *P.MODELS["tiers"].values()}
    prices = load_prices(refresh=a.live, ids=ids_m)
    budget = Budget(ROOT / ("runs/ledger.json" if a.live else "runs/ledger-mock.json"), session_cap=a.session_cap)
    c = Client(budget, prices, mock=a.mock)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True); gf = out / "grid.jsonl"
    feitos = set()
    if gf.exists():
        for l in gf.read_text().splitlines():
            r = json.loads(l); feitos.add((r["id"], r["tipo"], r.get("variante") or r.get("tier")))
    c1_cache = {json.loads(l)["id"]: json.loads(l) for l in gf.read_text().splitlines() if json.loads(l)["tipo"] == "c1"} if gf.exists() else {}
    items = load(a.split, a.limit, set(a.ids.split(",")) if a.ids else None)
    man = {"inicio": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "modo": "live" if a.live else "mock", "models": P.MODELS, "tau1": P.TH["tau1"],
           "dataset_sha256": hashlib.sha256(DS.read_bytes()).hexdigest(), "n_itens": len(items), "ledger_antes_usd": budget.spent,
           "max_tokens": P.MAX_TOKENS, "variantes_c2": VARS, "precos": {k: prices.get(k) for k in ids_m}}
    status = "ok"
    import threading
    from concurrent.futures import ThreadPoolExecutor
    lock = threading.Lock(); parar = threading.Event()
    f = open(gf, "a")
    def w(r):
        with lock: f.write(json.dumps({"ts": time.time(), **r}, ensure_ascii=False) + "\n"); f.flush()
    def proc(it):
        if parar.is_set(): return
        try:
            st = P.state_of(it["mensagem"], it.get("historico"))
            c1 = c1_cache.get(it["id"])
            if c1 is None:
                _, d1 = P.camada1(c, st, tau1=0)
                c1 = {"id": it["id"], "tipo": "c1", "probs": d1["probs"], "raw_choice": d1["raw_choice"], "p_max": d1["p_max"],
                      "cost": d1["cost"], "lat_ms": d1["lat_ms"], "model": d1.get("model")}
                w(c1); c1_cache[it["id"]] = c1
            sub = c1["raw_choice"]
            if sub == "fora_de_escopo": return
            for v in VARS:
                if (it["id"], "c2", v) in feitos: continue
                w({"id": it["id"], "tipo": "c2", "subagente": sub, **V.decidir(c, it, sub, v)})
            if not it.get("gerar") or a.sem_geracao: return
            for tier in P.TIER_ORDER:
                if (it["id"], "ger", tier) in feitos: continue
                g_ = P.gerar(c, sub, tier, it["mensagem"], it.get("historico"))
                j = julgar(c, it, g_["contexto"], g_["text"])
                w({"id": it["id"], "tipo": "ger", "tier": tier, "subagente": sub, "modelo": g_.get("model"), "provider": g_.get("provider"),
                   "usage": g_.get("usage"), "finish": g_.get("finish"), "cost": g_["cost"], "lat_ms": g_["lat_ms"], "resposta": g_["text"],
                   "contexto": g_["contexto"], "juiz": j})
        except BudgetExceeded as e:
            parar.set(); erros.append(f"ABORTADO_ORCAMENTO: {e}")
        except Exception as e:  # erro HTTP persistente: registra e segue (item fica incompleto, retomável)
            erros.append(f"{it['id']}: {str(e)[:200]}")
    erros = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(proc, items))
    f.close()
    aborts = [e for e in erros if e.startswith("ABORTADO")]
    if aborts: status = aborts[0]; print(status, file=sys.stderr)
    man["erros"] = erros[:50]; man["n_erros"] = len(erros)
    man.update({"fim": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "status": status, "ledger_depois_usd": budget.spent, "gasto_sessao_usd": budget.session_spent})
    (out / f"manifest-{time.strftime('%H%M%S')}.json").write_text(json.dumps(man, indent=2, ensure_ascii=False))
    print(f"{out}  status={status}  gasto_sessao=US${budget.session_spent:.6f}  ledger=US${budget.spent:.6f}")
    return out


if __name__ == "__main__":
    main()
