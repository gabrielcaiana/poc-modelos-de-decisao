"""Juiz barato (modelo de outra família) em amostra + planilha de revisão humana.
Uso: python -m harness.judge runs/<dir> --mock|--live [--amostra 40] [--session-cap X]"""
import argparse, csv, json, random, re, pathlib, sys
from .budget import Budget, BudgetExceeded
from .client import Client, load_prices
from .pipeline import MODELS
from mocks.dados import contexto_ferramentas

ROOT = pathlib.Path(__file__).resolve().parents[1]
SYS = ("Você é avaliador de atendimento pós-venda. Avalie a RESPOSTA do atendente de 1 a 5 em: correcao (fatos batem com "
       "as ferramentas/política), resolucao (resolve ou encaminha o objetivo do cliente), politica (não promete nada fora da "
       "política), tom. Responda SOMENTE um JSON (NOTA_JSON) com chaves correcao, resolucao, politica, tom, justificativa (curta).")


def parse(txt):
    m = re.search(r"\{.*\}", txt or "", re.S)
    return json.loads(m.group(0)) if m else None


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir")
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--mock", action="store_true"); g.add_argument("--live", action="store_true")
    ap.add_argument("--amostra", type=int, default=40, help="itens por estratégia (mesmos ids em todas)")
    ap.add_argument("--session-cap", type=float); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    run = pathlib.Path(a.run_dir)
    turns = [json.loads(l) for l in (run / "turns.jsonl").read_text().splitlines() if l.strip()]
    turns = [t for t in turns if t["tipo"] == "resposta"]
    ids = sorted({t["id"] for t in turns}); random.Random(a.seed).shuffle(ids); keep = set(ids[:a.amostra])
    prices = load_prices(refresh=False)
    budget = Budget(ROOT / ("runs/ledger.json" if a.live else "runs/ledger-mock.json"), session_cap=a.session_cap)
    client = Client(budget, prices, mock=a.mock)
    outj = open(run / "judge.jsonl", "a"); rows = []
    try:
        for t in turns:
            if t["id"] not in keep: continue
            ctx = t.get("contexto") or contexto_ferramentas(t["subagente"], t["mensagem"])
            u = f"CONTEXTO:\n{ctx}\n\nCLIENTE: {t['mensagem']}\n\nRESPOSTA DO ATENDENTE:\n{t['resposta']}"
            r = client.chat(MODELS["judge"], [{"role": "system", "content": SYS}, {"role": "user", "content": u}], max_tokens=500, temperature=0,
                            extra={"reasoning": {"enabled": False}, "response_format": {"type": "json_object"}})
            nota = parse(r["text"]) or {}
            rec = {"estrategia": t["estrategia"], "id": t["id"], "tier": t["tier"], "juiz": MODELS["judge"], "nota": nota,
                   "media": sum(nota.get(k, 0) for k in ("correcao", "resolucao", "politica", "tom")) / 4 if nota else None,
                   "custo": r["cost"]}
            outj.write(json.dumps(rec, ensure_ascii=False) + "\n"); rows.append((t, rec))
    except BudgetExceeded as e:
        print("ABORTADO_ORCAMENTO:", e, file=sys.stderr)
    finally:
        outj.close()
    # planilha de revisão humana: estratégia oculta (cega), ordem aleatória
    random.Random(a.seed).shuffle(rows)
    with open(run / "revisao_humana_juiz.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["chave", "mensagem", "resposta", "nota_humana_correcao", "nota_humana_resolucao",
                                       "nota_humana_politica", "nota_humana_tom", "comentario"])
        key = {}
        for i, (t, rec) in enumerate(rows):
            k = f"r{i:03d}"; key[k] = {"estrategia": t["estrategia"], "id": t["id"]}
            w.writerow([k, t["mensagem"], t["resposta"], "", "", "", "", ""])
    (run / "revisao_humana_chave.json").write_text(json.dumps(key, indent=1))
    print(f"juiz: {len(rows)} avaliações, gasto sessão US${budget.session_spent:.6f}, ledger US${budget.spent:.6f}")


if __name__ == "__main__":
    main()
