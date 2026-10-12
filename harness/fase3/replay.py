"""Fase 3 — avaliação por replay do grid (sem novas chamadas de API).
1) Ajusta, SÓ no split calib, τ/variante da Camada 2 (critério pré-registrado abaixo).
2) Avalia no split teste: always-cheap/media/expensive, oracle-regra, oracle-empírico, e msd1 nas 3 variantes com os parâmetros congelados.
3) Estatística pareada (mesmas mensagens, mesmas respostas): IC95% por bootstrap das diferenças de nota e custo,
   teste de permutação por troca de sinal (nota), McNemar (taxa de "passa") e correção de Holm.
Critério de ajuste (pré-registrado): entre os parâmetros cuja nota média ponderada no calib ≥ nota(always-media) − 0,05,
escolher o de MENOR custo; se nenhum atingir, escolher o de maior nota.
Médias são ponderadas por "peso" (desfaz a sobreamostragem da cauda complexa).
Uso: python3 -m harness.fase3.replay runs/<dir-grid> [--tau1 0.9] [--out report/fase3]"""
import json, sys, random, math, pathlib
from collections import defaultdict, Counter
from . import variantes as V
from .tier_empirico import tier_relativo, passa

ROOT = pathlib.Path(__file__).resolve().parents[2]
ORD = ["simples", "media", "complexa"]


def carregar(grid):
    ds = {r["id"]: r for r in map(json.loads, (ROOT / "datasets/fase3/conversas.jsonl").read_text().splitlines())}
    c1, c2, ger = {}, defaultdict(dict), defaultdict(dict)
    for l in (pathlib.Path(grid) / "grid.jsonl").read_text().splitlines():
        r = json.loads(l)
        if r["tipo"] == "c1": c1[r["id"]] = r
        elif r["tipo"] == "c2": c2[r["id"]][r["variante"]] = r
        else: ger[r["id"]][r["tier"]] = r
    return ds, c1, c2, ger


def itens_avaliaveis(ds, c1, c2, ger, split, tau1):
    out = []
    for i, g in ger.items():
        it = ds[i]
        if it["split"] != split or len(g) < 3 or any(g[t]["juiz"]["media"] is None for t in ORD): continue
        if c1[i]["p_max"] < tau1 or c1[i]["raw_choice"] == "fora_de_escopo": continue  # clarificou: igual em todas as estratégias
        notas = {t: {"media": g[t]["juiz"]["media"], **g[t]["juiz"]["nota"]} for t in ORD}
        out.append({"id": i, "peso": it.get("peso", 1.0), "tier_regra": it["tier_regra"], "c1_cost": c1[i]["cost"], "c1_lat": c1[i]["lat_ms"],
                    "q": {t: g[t]["juiz"]["media"] for t in ORD}, "pass": {t: passa(notas[t]) for t in ORD},
                    "cost": {t: g[t]["cost"] for t in ORD}, "lat": {t: g[t]["lat_ms"] for t in ORD},
                    "c2": c2.get(i, {}), "emp": tier_relativo(notas), "trunc": {t: g[t].get("finish") == "length" for t in ORD}})
    return out


def escolhas(itens, estrategia):
    """lista de (tier, custo_decisao_extra, lat_decisao_extra) por item"""
    out = []
    for it in itens:
        if isinstance(estrategia, str) and estrategia.startswith("always-"):
            out.append(({"always-cheap": "simples", "always-media": "media", "always-expensive": "complexa"}[estrategia], 0, 0))
        elif estrategia == "oracle-regra": out.append((it["tier_regra"] or "media", 0, 0))
        elif estrategia == "oracle-empirico": out.append((it["emp"], 0, 0))
        else:
            var, params = estrategia
            rec = it["c2"][var]; out.append((V.politica(rec, var, params), rec["cost"], rec["lat_ms"]))
    return out


def metricas(itens, ch):
    W = sum(it["peso"] for it in itens)
    wm = lambda xs: sum(it["peso"] * x for it, x in zip(itens, xs)) / W
    q = [it["q"][t] for it, (t, _, _) in zip(itens, ch)]
    c = [it["c1_cost"] + dc + it["cost"][t] for it, (t, dc, _) in zip(itens, ch)]
    lat = sorted(it["c1_lat"] + dl + it["lat"][t] for it, (t, _, dl) in zip(itens, ch))
    ps = [it["pass"][t] for it, (t, _, _) in zip(itens, ch)]
    sub = [ORD.index(t) < ORD.index(it["emp"]) for it, (t, _, _) in zip(itens, ch)]
    return {"nota": wm(q), "custo": wm(c), "passa": wm(ps), "sub_vs_empirico": wm(sub), "lat_p50": lat[len(lat) // 2], "lat_p95": lat[int(.95 * len(lat))],
            "dist": dict(Counter(t for t, _, _ in ch)), "_q": q, "_c": c, "_p": ps}


def ajustar(itens_calib):
    ref = metricas(itens_calib, escolhas(itens_calib, "always-media"))
    best = {}
    for var in ("v1_score", "v2_ctx", "v3_noul"):
        cands = [(p, metricas(itens_calib, escolhas(itens_calib, (var, p)))) for p in V.grade(var)]
        ok = [x for x in cands if x[1]["nota"] >= ref["nota"] - 0.05]
        p, m = min(ok, key=lambda x: x[1]["custo"]) if ok else max(cands, key=lambda x: x[1]["nota"])
        best[var] = {"params": p, "atinge_criterio": bool(ok), "calib_nota": m["nota"], "calib_custo": m["custo"]}
    return best, ref


def pareado(itens, a, b, n=5000, seed=7):
    """a, b: métricas de duas estratégias nos mesmos itens. Retorna diferenças (a−b) com IC e p-valores."""
    r = random.Random(seed); w = [it["peso"] for it in itens]; N = len(itens)
    dq = [x - y for x, y in zip(a["_q"], b["_q"])]; dc = [x - y for x, y in zip(a["_c"], b["_c"])]
    wmean = lambda d, idx: sum(w[i] * d[i] for i in idx) / sum(w[i] for i in idx)
    bq, bc = [], []
    for _ in range(n):
        idx = [r.randrange(N) for _ in range(N)]; bq.append(wmean(dq, idx)); bc.append(wmean(dc, idx))
    bq.sort(); bc.sort(); ic = lambda v: (v[int(.025 * n)], v[int(.975 * n)])
    obs = wmean(dq, range(N)); ext = 0
    for _ in range(n):
        s = [d if r.random() < .5 else -d for d in dq]
        ext += abs(wmean(s, range(N))) >= abs(obs) - 1e-12
    b01 = sum(1 for x, y in zip(a["_p"], b["_p"]) if x and not y); b10 = sum(1 for x, y in zip(a["_p"], b["_p"]) if y and not x)
    mcn = 1.0 if b01 + b10 == 0 else min(1.0, 2 * sum(math.comb(b01 + b10, k) for k in range(0, min(b01, b10) + 1)) / 2 ** (b01 + b10))
    return {"d_nota": obs, "d_nota_ic": ic(bq), "d_custo": wmean(dc, range(N)), "d_custo_ic": ic(bc), "p_perm_nota": (ext + 1) / (n + 1),
            "mcnemar_p": mcn, "a_passa_b_nao": b01, "b_passa_a_nao": b10}


def holm(ps):
    ordem = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0] * len(ps); m = len(ps); run = 0
    for k, i in enumerate(ordem): run = max(run, min(1, (m - k) * ps[i])); adj[i] = run
    return adj


GRID_T1 = [0.0, .3, .4, .5, .6, .7, .8, .85, .9, .95, .98, .99, .995, .999]


def u1(c, it, tau):
    """mesma utilidade da Fase 2 (harness/calibrate.py): +1 certo; +1 clarificou ambígua; +0,5 ambígua p/ rótulo aceito; -1 errado; 0 clarificou clara"""
    acc = c["p_max"] >= tau; ch = c["raw_choice"]; lab = it["label"]
    if lab == "clarificar": return 1 if not acc else (0.5 if ch in (it.get("aceitos") or []) else -1)
    return (1 if ch == lab else -1) if acc else 0


def c1_metricas(ds, c1, split, tau):
    ids = [i for i in c1 if ds[i]["split"] == split]; claras = [i for i in ids if ds[i]["label"] != "clarificar"]
    amb = [i for i in ids if ds[i]["label"] == "clarificar"]
    aceitas = [i for i in claras if c1[i]["p_max"] >= tau]
    return {"n": len(ids), "acuracia_bruta_claras": sum(c1[i]["raw_choice"] == ds[i]["label"] for i in claras) / max(1, len(claras)),
            "taxa_clarificacao": sum(c1[i]["p_max"] < tau for i in ids) / max(1, len(ids)),
            "clarificacao_desnecessaria": sum(c1[i]["p_max"] < tau for i in claras) / max(1, len(claras)),
            "erro_entre_aceitas": sum(c1[i]["raw_choice"] != ds[i]["label"] for i in aceitas) / max(1, len(aceitas)),
            "ambiguas_ok": sum((c1[i]["p_max"] < tau) or (c1[i]["raw_choice"] in (ds[i].get("aceitos") or [])) for i in amb) / max(1, len(amb)),
            "utilidade": sum(u1(c1[i], ds[i], tau) for i in ids) / max(1, len(ids))}


def ajustar_tau1(ds, c1):
    ids = [i for i in c1 if ds[i]["split"] == "calib"]
    curva = {t: sum(u1(c1[i], ds[i], t) for i in ids) / len(ids) for t in GRID_T1}
    return max(GRID_T1, key=lambda t: (round(curva[t], 6), -t)), curva


def main(grid, tau1=None, out="report/fase3"):
    from ..pipeline import TH
    ds, c1, c2, ger = carregar(grid)
    tau1_fase2 = TH["tau1"]
    CONG = ROOT / "config/fase3_congelado.json"
    if CONG.exists():  # parâmetros congelados ANTES de olhar o teste
        cg = json.loads(CONG.read_text()); tau1_ajustado, curva_t1 = cg["tau1"], {float(k): v for k, v in cg["curva_tau1_calib"].items()}
    else:
        cg = None; tau1_ajustado, curva_t1 = ajustar_tau1(ds, c1)
    tau1 = tau1_ajustado if tau1 is None else tau1
    c1_tab = {f"τ1={t} ({nome})": {sp: c1_metricas(ds, c1, sp, t) for sp in ("calib", "teste")} for t, nome in ((tau1_fase2, "Fase 2"), (tau1_ajustado, "reajustado no calib Fase 3"), (0.0, "sem threshold"))}
    cal, tst = itens_avaliaveis(ds, c1, c2, ger, "calib", tau1), itens_avaliaveis(ds, c1, c2, ger, "teste", tau1)
    best, ref_cal = ajustar(cal)
    if cg:
        assert all(best[v]["params"] == cg["c2"][v]["params"] for v in best), "ajuste do calib diverge do congelado"
        best = cg["c2"]
    est = {"always-cheap": "always-cheap", "always-media": "always-media", "always-expensive": "always-expensive",
           "oracle-regra": "oracle-regra", "oracle-empirico": "oracle-empirico"}
    for var, b in best.items(): est[f"msd1-{var}"] = (var, b["params"])
    M = {k: metricas(tst, escolhas(tst, v)) for k, v in est.items()}
    comps = [(f"msd1-{v}", base) for v in best for base in ("always-media", "always-expensive")]
    P = {f"{a} vs {b}": pareado(tst, M[a], M[b]) for a, b in comps}
    adj = holm([x["p_perm_nota"] for x in P.values()])
    for (k, x), h in zip(P.items(), adj): x["p_perm_nota_holm"] = h
    for (k, x), h in zip(P.items(), holm([x["mcnemar_p"] for x in P.values()])): x["mcnemar_p_holm"] = h
    # subgrupo exploratório (post hoc): cauda complexa (tier da regra = complexa) — msd1 vs always-media
    sub = [k for k, it in enumerate(tst) if it["tier_regra"] == "complexa"]; tsub = [tst[k] for k in sub]
    Ms = {k: {kk: [M[k][kk][i] for i in sub] for kk in ("_q", "_c", "_p")} for k in M}
    Psub = {f"{a} vs {b} [complexa]": pareado(tsub, Ms[a], Ms[b]) for a, b in comps if b == "always-media"}
    # acerto de tier da C2 (todas as conversas roteadas do teste) vs regra, nos parâmetros congelados
    acc = {}
    for var, b in best.items():
        z = [(V.politica(c2[i][var], var, b["params"]), ds[i]["tier_regra"]) for i in c2 if ds[i]["split"] == "teste" and ds[i]["tier_regra"] and var in c2[i]]
        acc[var] = {"n": len(z), "acerto_vs_regra": sum(a == b_ for a, b_ in z) / len(z) if z else None}
    por_tier = {k: {t: (sum(it["peso"] * q for it, q in zip(tst, M[k]["_q"]) if it["tier_regra"] == t) / max(1e-9, sum(it["peso"] for it in tst if it["tier_regra"] == t))) for t in ORD} for k in M}
    res = {"n_calib": len(cal), "n_teste": len(tst), "tau1": tau1, "tau1_fase2": tau1_fase2, "tau1_ajustado": tau1_ajustado, "curva_tau1_calib": curva_t1, "c1": c1_tab, "ajuste": best, "ref_calib_always_media": {k: ref_cal[k] for k in ("nota", "custo")},
           "teste": {k: {kk: vv for kk, vv in m.items() if not kk.startswith("_")} for k, m in M.items()}, "pareado": P, "pareado_complexa": Psub, "c2_acerto": acc, "nota_por_tier_regra": por_tier,
           "truncamento": {t: sum(it["trunc"][t] for it in tst) / max(1, len(tst)) for t in ORD}}
    o = pathlib.Path(out); o.mkdir(parents=True, exist_ok=True)
    (o / "replay_resultado.json").write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    L = ["# Resultados da Fase 3 (replay)", "", f"Grid: `{grid}` · itens avaliáveis: calib {len(cal)}, teste {len(tst)} · τ1={tau1}. Médias ponderadas pelo peso de amostragem.", "",
         "## Camada 1 — τ1", "", "| configuração | split | acurácia (claras) | clarificação | clarif. desnecessária | erro entre aceitas | ambíguas ok | utilidade |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for k, d in c1_tab.items():
        for sp, m in d.items(): L.append(f"| {k} | {sp} | {100*m['acuracia_bruta_claras']:.1f}% | {100*m['taxa_clarificacao']:.1f}% | {100*m['clarificacao_desnecessaria']:.1f}% | {100*m['erro_entre_aceitas']:.1f}% | {100*m['ambiguas_ok']:.1f}% | {m['utilidade']:.3f} |")
    L += ["",
         "## Parâmetros da Camada 2 escolhidos no calib", "", "| variante | parâmetros | atinge critério | nota calib | US$/msg calib |", "|---|---|---|---:|---:|"]
    for v, b in best.items(): L.append(f"| {v} | `{b['params']}` | {b['atinge_criterio']} | {b['calib_nota']:.3f} | {b['calib_custo']:.6f} |")
    L += ["", f"Referência no calib — always-media: nota {ref_cal['nota']:.3f}, US${ref_cal['custo']:.6f}/msg.", "", "## Teste", "",
          "| estratégia | nota | % passa | US$/msg | sub-roteamento vs empírico | lat P50/P95 (s) | simples/media/complexa |", "|---|---:|---:|---:|---:|---:|---|"]
    for k, m in M.items():
        L.append(f"| {k} | {m['nota']:.3f} | {100*m['passa']:.1f}% | {m['custo']:.6f} | {100*m['sub_vs_empirico']:.1f}% | {m['lat_p50']/1000:.2f}/{m['lat_p95']/1000:.2f} | {m['dist'].get('simples',0)}/{m['dist'].get('media',0)}/{m['dist'].get('complexa',0)} |")
    L += ["", "## Comparações pareadas (teste)", "", "| comparação | Δ nota (IC95%) | p perm. | p Holm | Δ US$/msg (IC95%) | McNemar p (passa) | McNemar p Holm | passa só A / só B |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for k, x in P.items():
        L.append(f"| {k} | {x['d_nota']:+.3f} ({x['d_nota_ic'][0]:+.3f}; {x['d_nota_ic'][1]:+.3f}) | {x['p_perm_nota']:.4f} | {x['p_perm_nota_holm']:.4f} | {x['d_custo']:+.6f} ({x['d_custo_ic'][0]:+.6f}; {x['d_custo_ic'][1]:+.6f}) | {x['mcnemar_p']:.4f} | {x['mcnemar_p_holm']:.4f} | {x['a_passa_b_nao']} / {x['b_passa_a_nao']} |")
    L += ["", f"Análise exploratória (post hoc, decidida depois de ver a quebra por tier; não estava no plano) — cauda complexa (n={len(tsub)}, sem correção adicional):", "", "| comparação | Δ nota (IC95%) | p perm. | Δ US$/msg (IC95%) | McNemar p |", "|---|---:|---:|---:|---:|"]
    for k, x in Psub.items():
        L.append(f"| {k} | {x['d_nota']:+.3f} ({x['d_nota_ic'][0]:+.3f}; {x['d_nota_ic'][1]:+.3f}) | {x['p_perm_nota']:.4f} | {x['d_custo']:+.6f} ({x['d_custo_ic'][0]:+.6f}; {x['d_custo_ic'][1]:+.6f}) | {x['mcnemar_p']:.4f} |")
    L += ["", "## Nota por tier da regra (teste)", "", "| estratégia | simples | media | complexa |", "|---|---:|---:|---:|"]
    for k, d in por_tier.items(): L.append(f"| {k} | " + " | ".join(f"{d[t]:.2f}" for t in ORD) + " |")
    L += ["", "## Acerto da C2 vs regra (todas as conversas roteadas do teste)", ""] + [f"- {v}: {a['acerto_vs_regra']:.3f} (n={a['n']})" if a["acerto_vs_regra"] is not None else f"- {v}: —" for v, a in acc.items()]
    L += ["", f"Truncamento (teste): {res['truncamento']}"]
    (o / "RESULTADOS_FASE3.md").write_text("\n".join(L) + "\n"); print("\n".join(L)); return res


def congelar(grid):
    """Só calib: escolhe τ1 e parâmetros da C2 e grava config/fase3_congelado.json (antes de qualquer métrica de teste)."""
    import time
    ds, c1, c2, ger = carregar(grid)
    t1, curva = ajustar_tau1(ds, c1)
    cal = itens_avaliaveis(ds, c1, c2, ger, "calib", t1)
    best, ref = ajustar(cal)
    cg = {"_nota": "Congelado usando SÓ o split calib da Fase 3, antes de calcular qualquer métrica no teste.", "congelado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
          "grid": str(grid), "n_calib_avaliaveis": len(cal), "tau1": t1, "curva_tau1_calib": curva, "c2": best,
          "ref_calib_always_media": {k: ref[k] for k in ("nota", "custo")}}
    (ROOT / "config/fase3_congelado.json").write_text(json.dumps(cg, indent=2, ensure_ascii=False)); print(json.dumps(cg, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--congelar" in a: congelar(a[0]); sys.exit()
    main(a[0], float(a[a.index("--tau1") + 1]) if "--tau1" in a else None, a[a.index("--out") + 1] if "--out" in a else "report/fase3")
