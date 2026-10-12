"""Mostra no terminal o rastro de uma mensagem a partir dos logs gravados (não chama API).
Uso: python3 -m harness.show runs/20261012-holdout-live m246 [--estrategia msd1]"""
import json, sys, pathlib

def main(run, mid, est="msd1"):
    run = pathlib.Path(run)
    T = [json.loads(l) for l in (run / "turns.jsonl").read_text().splitlines()]
    D = [json.loads(l) for l in (run / "decisions.jsonl").read_text().splitlines()]
    J = {(j["estrategia"], j["id"]): j for j in map(json.loads, (run / "judge.jsonl").read_text().splitlines())}
    t = next(x for x in T if x["id"] == mid and x["estrategia"] == est)
    out = [f"$ python3 -m harness.show {run.as_posix().split('/')[-2] + '/' + run.name if '/' in run.as_posix() else run} {mid} --estrategia {est}",
           f"[{est}] {mid}  cliente: \"{t['mensagem']}\"  (rótulo: {t['label']}/{t['tier_minimo']})"]
    for d in D:
        if d["id"] == mid and d["estrategia"] == est:
            pr = "  ".join(f"{k}={v:.3f}" for k, v in sorted(d["probs"].items(), key=lambda kv: -kv[1]))
            dec = d.get("tier_final") if d["camada"] == 2 else ("clarificar" if d["fallback"] else d["raw_choice"])
            out.append(f"  C{d['camada']} MSD1  {pr}")
            out.append(f"      p_max={d['p_max']:.3f} τ={d['tau']} → {dec}   {d['lat_ms']:.0f} ms  US${d['cost']:.7f}")
    if t["tipo"] == "resposta":
        u = t["usage"]
        out.append(f"  GERAÇÃO {t['modelo']}  in={u['prompt_tokens']} out={u['completion_tokens']} finish={t.get('finish')}  {t['lat_geracao_ms']:.0f} ms  US${t['custo_geracao']:.6f}")
    else:
        out.append(f"  {t['tipo'].upper()} (resposta fixa, sem geração)")
    out.append(f"  resposta: {t['resposta'][:150].replace(chr(10), ' ')}{'…' if len(t['resposta']) > 150 else ''}")
    j = J.get((est, mid))
    if j: out.append(f"  juiz: média {j['media']:.2f}  " + " ".join(f"{k}={j['nota'][k]}" for k in ("correcao", "resolucao", "politica", "tom")))
    out.append(f"  total do turno: US${t['custo_geracao'] + t['custo_decisoes']:.6f}  latência {((t['lat_geracao_ms'] or 0) + t['lat_decisoes_ms'])/1000:.2f} s")
    print("\n".join(out)); return out

if __name__ == "__main__":
    a = sys.argv[1:]; est = a[a.index("--estrategia") + 1] if "--estrategia" in a else "msd1"
    main(a[0], a[1], est)
