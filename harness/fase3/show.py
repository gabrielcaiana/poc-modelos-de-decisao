"""Rastro de uma conversa da Fase 3 a partir do grid gravado (sem chamar API).
Uso: python3 -m harness.fase3.show runs/fase3-grid c0123"""
import json, sys, pathlib
from . import variantes as V

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main(grid, cid):
    cg = json.loads((ROOT / "config/fase3_congelado.json").read_text())
    ds = {r["id"]: r for r in map(json.loads, (ROOT / "datasets/fase3/conversas.jsonl").read_text().splitlines())}
    rs = [json.loads(l) for l in (pathlib.Path(grid) / "grid.jsonl").read_text().splitlines() if f'"id": "{cid}"' in l]
    it = ds[cid]; L = [f"$ python3 -m harness.fase3.show {grid} {cid}", f"[{cid}] split={it['split']} rótulo={it['label']}/{it['tier_regra']} peso={it.get('peso')}"]
    for h in it["historico"]: L.append(f"  {h['role']:>9}: {h['content']}")
    L.append(f"  {'cliente':>9}: {it['mensagem']}")
    for r in rs:
        if r["tipo"] == "c1":
            pr = "  ".join(f"{k}={v:.3f}" for k, v in sorted(r["probs"].items(), key=lambda kv: -kv[1]))
            L.append(f"  C1 MSD1  {pr}  → {r['raw_choice'] if r['p_max'] >= cg['tau1'] else 'clarificar'} (τ1={cg['tau1']}, {r['lat_ms']:.0f} ms)")
    for r in rs:
        if r["tipo"] == "c2":
            v = r["variante"]; t = V.politica(r, v, cg["c2"][v]["params"])
            L.append(f"  C2 {v:<9} " + "  ".join(f"{k}={x:.3f}" for k, x in r["probs"].items()) + f"  → {t}")
    for r in sorted((r for r in rs if r["tipo"] == "ger"), key=lambda r: ["simples", "media", "complexa"].index(r["tier"])):
        u = r["usage"]; j = r["juiz"]
        L.append(f"  GER {r['tier']:<8} {r['modelo']:<30} in={u['prompt_tokens']} out={u['completion_tokens']}  {r['lat_ms']/1000:.2f} s  US${r['cost']:.6f}  juiz={j['media']}")
        L.append(f"      “{r['resposta'][:140].replace(chr(10), ' ')}…”")
    print("\n".join(L)); return L


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
