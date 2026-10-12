"""Gera RESULTADOS.md + report/graficos/*.png + report/tabelas/*.csv a partir de runs/. Nenhum número digitado à mão.
Uso: .venv/bin/python -m harness.report runs/<holdout> runs/<calib>"""
import json, sys, csv, random, statistics as st, pathlib, os
from collections import Counter, defaultdict
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORD = ["simples", "media", "complexa"]; SUBS = ["devolucao", "suporte", "financeiro", "fora_de_escopo"]
EST = ["msd1", "msd1-up1", "always-cheap", "always-media", "always-expensive", "oracle"]
G = ROOT / "report/graficos"; TB = ROOT / "report/tabelas"; G.mkdir(parents=True, exist_ok=True); TB.mkdir(parents=True, exist_ok=True)
jl = lambda p: [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]
pct = lambda x: "—" if x is None else f"{100*x:.1f}%"
def q(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None
def boot(f, data, n=2000, seed=0):
    r = random.Random(seed); v = sorted(f([r.choice(data) for _ in data]) for _ in range(n)); return v[int(.025 * n)], v[int(.975 * n)]


def c1_stats(recs, tau):
    """recs: (label, aceitos, probs, raw, pmax)"""
    n = len(recs); clar = acc_ok = acc_n = unn = amb_ok = amb_n = clear_ok = clear_n = 0; conf = Counter()
    for lab, ac, probs, raw, pm in recs:
        c = "clarificar" if pm < tau else raw; conf[(lab, c)] += 1
        if c == "clarificar": clar += 1
        if lab == "clarificar":
            amb_n += 1; amb_ok += c == "clarificar" or raw in (ac or [])
        else:
            clear_n += 1; clear_ok += raw == lab; unn += c == "clarificar"
            if c != "clarificar": acc_n += 1; acc_ok += c == lab
    return {"n": n, "acuracia_bruta_claras": clear_ok / clear_n, "taxa_clarificacao": clar / n,
            "clarificacao_desnecessaria": unn / clear_n, "erro_entre_aceitas_claras": 1 - acc_ok / acc_n if acc_n else None,
            "ambiguas_tratadas_ok": amb_ok / amb_n if amb_n else None, "ambiguas_clarificadas": sum(conf[("clarificar", "clarificar")] for _ in [0]) / amb_n if amb_n else None,
            "confusao": conf}


def ece(pairs, bins=10):
    n = len(pairs); e = 0
    for b in range(bins):
        s = [(c, o) for c, o in pairs if (b / bins < c <= (b + 1) / bins) or (b == 0 and c == 0)]
        if s: e += len(s) / n * abs(sum(o for _, o in s) / len(s) - sum(c for c, _ in s) / len(s))
    return e


def main(hold, calib):
    hold, calib = pathlib.Path(hold), pathlib.Path(calib)
    TH = json.loads((ROOT / "config/thresholds.json").read_text())
    ds = {r["id"]: r for r in jl(ROOT / "datasets/mensagens.jsonl")}
    T = jl(hold / "turns.jsonl"); D = jl(hold / "decisions.jsonl"); J = jl(hold / "judge.jsonl"); CAL = jl(calib / "decisions.jsonl")
    man = json.loads((hold / "manifest.json").read_text())
    # ---------- Camada 1 ----------
    d1h = {}
    for d in D:
        if d["camada"] == 1 and not d.get("reuso_cache"): d1h[d["id"]] = d
    rec_h = [(ds[i]["label"], ds[i].get("aceitos"), d["probs"], d["raw_choice"], d["p_max"]) for i, d in d1h.items()]
    rec_c = [(r["label"], r.get("aceitos"), r["d1"]["probs"], r["d1"]["raw_choice"], r["d1"]["p_max"]) for r in CAL]
    c1h, c1c = c1_stats(rec_h, TH["tau1"]), c1_stats(rec_c, TH["tau1"])
    c1h_0 = c1_stats(rec_h, 0)
    pairs = [(pm, int(raw == lab)) for lab, ac, p, raw, pm in rec_c + rec_h if lab != "clarificar"]
    ece1 = ece(pairs); lat1 = [d["lat_ms"] for d in d1h.values()]
    # ---------- Camada 2 ----------
    def c2(est):
        z = [(d["tier_final"], ds[d["id"]]["tier_minimo"], d["fallback"]) for d in D if d["camada"] == 2 and d["estrategia"] == est and ds[d["id"]]["tier_minimo"]]
        a = [(ORD.index(x), ORD.index(y)) for x, y, _ in z]
        return {"n": len(z), "acuracia": sum(x == y for x, y in a) / len(a), "sub": sum(x < y for x, y in a) / len(a),
                "super": sum(x > y for x, y in a) / len(a), "fallback": sum(f for *_, f in z) / len(z),
                "dist": Counter(x for x, *_ in z)}
    c2m, c2u = c2("msd1"), c2("msd1-up1")
    zc = [(r["d2"]["raw_choice"], r["tier_minimo"]) for r in CAL if "d2" in r]
    c2cal_raw = sum(a == b for a, b in zc) / len(zc)
    lat2 = [d["lat_ms"] for d in D if d["camada"] == 2]
    # ---------- Juiz: tier empírico ----------
    js = {(j["estrategia"], j["id"]): j["media"] for j in J if j["media"] is not None}
    emp = {}
    for i in {t["id"] for t in T}:
        m = [js.get((e, i)) for e in ("always-cheap", "always-media", "always-expensive")]
        if None in m: continue
        best = max(m); emp[i] = next(ORD[k] for k in range(3) if m[k] >= best - 0.25)  # tier mais barato a ≤0,25 do melhor
    # ---------- Estratégias ----------
    by = defaultdict(list)
    for t in T: by[t["estrategia"]].append(t)
    rows = {}
    ids_common = sorted({t["id"] for t in T})
    for e in EST:
        ts = by[e]; cost = {t["id"]: t["custo_geracao"] + t["custo_decisoes"] for t in ts}
        resp = [t for t in ts if t["tipo"] == "resposta"]
        notas = [js[(e, t["id"])] for t in resp if (e, t["id"]) in js]
        lat = [(t["lat_geracao_ms"] or 0) + t["lat_decisoes_ms"] for t in ts]
        latd = [t["lat_decisoes_ms"] for t in resp]; latg = [t["lat_geracao_ms"] for t in resp]
        rows[e] = {"n": len(ts), "n_resp": len(resp), "custo_total": sum(cost.values()), "custo_msg": sum(cost.values()) / len(ts),
                   "nota": st.mean(notas) if notas else None, "nota_ic": boot(st.mean, notas) if notas else None,
                   "pct_ge4": sum(n >= 4 for n in notas) / len(notas) if notas else None,
                   "lat_p50": q(lat, .5), "lat_p95": q(lat, .95), "overhead_pct": st.median(d / (d + g) for d, g in zip(latd, latg)) if resp else None,
                   "trunc": sum(t.get("finish") == "length" for t in resp) / len(resp) if resp else 0,
                   "tiers": Counter(t["tier"] for t in resp), "cost_by_id": cost}
    base = rows["always-expensive"]["cost_by_id"]
    for e, r in rows.items():
        ids = [i for i in ids_common if i in r["cost_by_id"]]
        f = lambda s: 1 - sum(r["cost_by_id"][i] for i in s) / sum(base[i] for i in s)
        r["econ"] = f(ids); r["econ_ic"] = boot(f, ids)
    trunc_model = Counter((t["modelo"], t.get("finish")) for t in T if t["modelo"])
    # custo por resposta "boa" (nota >= 4)
    for e, r in rows.items():
        good = r["pct_ge4"] * r["n_resp"] if r["pct_ge4"] is not None else 0
        r["custo_por_boa"] = r["custo_total"] / good if good else None
    led = json.loads((ROOT / "runs/ledger.json").read_text())
    # ---------- gráficos ----------
    plt.figure(figsize=(7, 5))
    for e, r in rows.items():
        plt.errorbar(r["custo_msg"] * 1000, r["nota"], yerr=[[r["nota"] - r["nota_ic"][0]], [r["nota_ic"][1] - r["nota"]]], fmt="o", capsize=3)
        plt.annotate(e, (r["custo_msg"] * 1000, r["nota"]), textcoords="offset points", xytext=(5, 5))
    plt.xlabel("custo por mensagem (US$ × 10⁻³)"); plt.ylabel("nota média do juiz (1–5, IC95%)"); plt.title("Custo × qualidade por estratégia (holdout)")
    plt.grid(alpha=.3); plt.tight_layout(); plt.savefig(G / "custo_vs_qualidade.png", dpi=130); plt.close()
    # confiabilidade C1
    bins = [(i / 10, (i + 1) / 10) for i in range(10)]; xs, ys, ns = [], [], []
    for a, b in bins:
        s = [(c, o) for c, o in pairs if a < c <= b or (a == 0 and c == 0)]
        if s: xs.append(sum(c for c, _ in s) / len(s)); ys.append(sum(o for _, o in s) / len(s)); ns.append(len(s))
    plt.figure(figsize=(5, 5)); plt.plot([0, 1], [0, 1], "--", c="gray"); plt.plot(xs, ys, "o-")
    for x, y, n in zip(xs, ys, ns): plt.annotate(str(n), (x, y), textcoords="offset points", xytext=(4, -10), fontsize=8)
    plt.xlabel("confiança do MSD1 (p_max)"); plt.ylabel("acurácia observada"); plt.title(f"Confiabilidade C1 (calib+holdout, ECE={ece1:.3f})")
    plt.tight_layout(); plt.savefig(G / "confiabilidade_c1.png", dpi=130); plt.close()
    # cobertura × erro C1 (calib)
    taus = [0, .3, .5, .7, .8, .9, .95, .98, .99, .995, .999, .9999]; cov, err = [], []
    clear = [x for x in rec_c if x[0] != "clarificar"]
    for t in taus:
        acc = [x for x in clear if x[4] >= t]; cov.append(len(acc) / len(clear)); err.append(sum(x[3] != x[0] for x in acc) / len(acc) if acc else 0)
    plt.figure(figsize=(6, 4)); plt.plot(cov, err, "o-")
    for t, c, e_ in zip(taus, cov, err): plt.annotate(str(t), (c, e_), fontsize=7, textcoords="offset points", xytext=(3, 3))
    plt.xlabel("cobertura (mensagens claras aceitas sem clarificar)"); plt.ylabel("erro entre aceitas"); plt.title("C1: cobertura × erro por τ1 (calib)")
    plt.grid(alpha=.3); plt.tight_layout(); plt.savefig(G / "cobertura_erro_c1.png", dpi=130); plt.close()
    # latência
    plt.figure(figsize=(8, 4)); plt.boxplot([[((t["lat_geracao_ms"] or 0) + t["lat_decisoes_ms"]) / 1000 for t in by[e] if t["tipo"] == "resposta"] for e in EST], tick_labels=EST)
    plt.ylabel("latência do turno (s)"); plt.title("Latência por estratégia (decisões + geração, holdout)"); plt.xticks(rotation=20)
    plt.tight_layout(); plt.savefig(G / "latencia.png", dpi=130); plt.close()
    # distribuição de tiers
    plt.figure(figsize=(7, 4)); w = .2
    for k, (nm, cnt) in enumerate([("rótulo", Counter(ds[i]["tier_minimo"] for i in d1h if ds[i]["tier_minimo"])), ("empírico (juiz)", Counter(emp.values())),
                                   ("msd1", c2m["dist"]), ("msd1-up1", c2u["dist"])]):
        plt.bar([x + k * w for x in range(3)], [cnt.get(t, 0) for t in ORD], w, label=nm)
    plt.xticks([x + 1.5 * w for x in range(3)], ORD); plt.legend(); plt.title("Distribuição de tiers (holdout)"); plt.tight_layout(); plt.savefig(G / "tiers.png", dpi=130); plt.close()
    # ---------- tabelas CSV ----------
    with open(TB / "estrategias.csv", "w", newline="") as f:
        w_ = csv.writer(f); w_.writerow(["estrategia", "n", "n_resp", "custo_total_usd", "custo_msg_usd", "economia_vs_caro", "econ_ic_lo", "econ_ic_hi", "nota", "nota_ic_lo", "nota_ic_hi", "pct_nota_ge4", "custo_por_resposta_boa", "lat_p50_ms", "lat_p95_ms", "overhead_decisao_mediana", "truncamento"])
        for e in EST:
            r = rows[e]; w_.writerow([e, r["n"], r["n_resp"], f"{r['custo_total']:.6f}", f"{r['custo_msg']:.7f}", f"{r['econ']:.4f}", f"{r['econ_ic'][0]:.4f}", f"{r['econ_ic'][1]:.4f}", f"{r['nota']:.3f}", f"{r['nota_ic'][0]:.3f}", f"{r['nota_ic'][1]:.3f}", f"{r['pct_ge4']:.3f}", f"{r['custo_por_boa']:.6f}" if r["custo_por_boa"] else "", int(r["lat_p50"]), int(r["lat_p95"]), f"{r['overhead_pct']:.3f}" if r["overhead_pct"] is not None else "", r["trunc"]])
    # ---------- exemplos ----------
    ex = ["# Exemplos reais de routing (holdout)", ""]
    for i, d in list(d1h.items()):
        lab = ds[i]["label"]; c = "clarificar" if d["p_max"] < TH["tau1"] else d["raw_choice"]
        tag = "ACERTO" if c == lab or (lab == "clarificar" and d["raw_choice"] in (ds[i].get("aceitos") or [])) else ("CLARIFICAÇÃO" if c == "clarificar" else "ERRO")
        ex.append(f"- **{tag}** `{i}` “{ds[i]['mensagem']}” → rótulo `{lab}`, MSD1 `{d['raw_choice']}` p={d['p_max']:.3f} → `{c}`. probs: " + ", ".join(f"{k}={v:.3f}" for k, v in sorted(d["probs"].items(), key=lambda kv: -kv[1])))
    (ROOT / "report/exemplos-routing.md").write_text("\n".join(ex) + "\n")
    # ---------- RESULTADOS.md ----------
    L = ["# Resultados — POC modelos de decisão (Fase 2)", "",
         f"Rodada: `{hold.name}` (holdout, {man['n_itens']} mensagens × {len(EST)} estratégias), iniciada {man['inicio']} (horário de SP). Calibração: `{calib.name}` ({len(CAL)} mensagens do split calib).",
         f"Dataset: `datasets/mensagens.jsonl` (sha256 `{man['dataset_sha256'][:16]}…`, 300 mensagens fictícias, rótulos provisórios do bot). Thresholds congelados antes do holdout: τ1={TH['tau1']}, τ2={TH['tau2']} (fallback → complexa), τ2_up1={TH['tau2_up1']} (fallback +1 tier).",
         "Tudo abaixo é regenerado por `.venv/bin/python -m harness.report " + f"runs/{hold.name} runs/{calib.name}`.", "",
         "## Resumo", "",
         f"- **Camada 1 (routing)**: acurácia bruta do MSD1 nas mensagens claras = **{pct(c1h['acuracia_bruta_claras'])}** no holdout ({pct(c1c['acuracia_bruta_claras'])} no calib). Com τ1={TH['tau1']}: clarificação {pct(c1h['taxa_clarificacao'])} (desnecessária {pct(c1h['clarificacao_desnecessaria'])}), erro entre aceitas {pct(c1h['erro_entre_aceitas_claras'])}, ambíguas bem tratadas {pct(c1h['ambiguas_tratadas_ok'])}.",
         f"- **Camada 2 (modelo)**: acerto do tier vs. rótulo {pct(c2m['acuracia'])} (msd1); sub-roteamento {pct(c2m['sub'])}, super-roteamento {pct(c2m['super'])}, fallback {pct(c2m['fallback'])}.",
         f"- **Custo × qualidade**: msd1 custa {pct(rows['msd1']['econ'])} menos que always-expensive (IC95% {pct(rows['msd1']['econ_ic'][0])}–{pct(rows['msd1']['econ_ic'][1])}) com nota {rows['msd1']['nota']:.2f} vs {rows['always-expensive']['nota']:.2f} (always-cheap: {rows['always-cheap']['nota']:.2f}).",
         "- **Fronteira de Pareto (custo↓, nota↑)**: " + ", ".join(e for e in EST if not any(rows[o]["custo_msg"] <= rows[e]["custo_msg"] and rows[o]["nota"] >= rows[e]["nota"] and o != e and (rows[o]["custo_msg"], rows[o]["nota"]) != (rows[e]["custo_msg"], rows[e]["nota"]) for o in EST)) + ". Dominadas: " + ", ".join(f"{e} (por {', '.join(o for o in EST if o != e and rows[o]['custo_msg'] <= rows[e]['custo_msg'] and rows[o]['nota'] >= rows[e]['nota'])})" for e in EST if any(o != e and rows[o]["custo_msg"] <= rows[e]["custo_msg"] and rows[o]["nota"] >= rows[e]["nota"] for o in EST)) + ".",
         f"- **Gasto total no OpenRouter (ledger local, Fases 1+2)**: **US${led['spent_usd']:.4f}** em {led['calls']} chamadas.", "",
         "## Camada 1 — routing de subagente (MSD1 `choice`)", "",
         "| Métrica | Holdout (τ1) | Holdout (sem τ) | Calib (τ1) |", "|---|---:|---:|---:|"]
    for k, nm in [("acuracia_bruta_claras", "Acurácia (claras, escolha bruta)"), ("taxa_clarificacao", "Taxa de clarificação"), ("clarificacao_desnecessaria", "Clarificação desnecessária (claras)"),
                  ("erro_entre_aceitas_claras", "Erro entre aceitas (claras)"), ("ambiguas_tratadas_ok", "Ambíguas: clarificou ou rótulo aceito")]:
        L.append(f"| {nm} | {pct(c1h[k])} | {pct(c1h_0[k])} | {pct(c1c[k])} |")
    L += [f"| n | {c1h['n']} | {c1h_0['n']} | {c1c['n']} |", "",
          f"ECE (calib+holdout, claras): **{ece1:.3f}**. Latência da decisão C1: P50 {q(lat1,.5):.0f} ms, P95 {q(lat1,.95):.0f} ms; C2: P50 {q(lat2,.5):.0f} ms, P95 {q(lat2,.95):.0f} ms (medido do box, SP).", "",
          "Matriz de confusão (holdout, com τ1; linhas = rótulo, colunas = decisão):", "", "| rótulo \\ decisão | " + " | ".join(SUBS + ["clarificar"]) + " |", "|---" * 6 + "|"]
    for lab in SUBS + ["clarificar"]:
        L.append(f"| {lab} | " + " | ".join(str(c1h["confusao"].get((lab, c), 0)) for c in SUBS + ["clarificar"]) + " |")
    L += ["", "![confiabilidade](report/graficos/confiabilidade_c1.png) ![cobertura](report/graficos/cobertura_erro_c1.png)", "",
          "## Camada 2 — escolha do modelo (MSD1 `score`)", "",
          "| Variante | n | Acerto vs rótulo | Sub-roteamento | Super-roteamento | Fallback | simples/média/complexa |", "|---|---:|---:|---:|---:|---:|---|"]
    for nm, c in [("msd1 (τ2, fallback→complexa)", c2m), ("msd1-up1 (τ2_up1, fallback +1)", c2u)]:
        L.append(f"| {nm} | {c['n']} | {pct(c['acuracia'])} | {pct(c['sub'])} | {pct(c['super'])} | {pct(c['fallback'])} | {c['dist'].get('simples',0)}/{c['dist'].get('media',0)}/{c['dist'].get('complexa',0)} |")
    agree = [i for i in emp if ds[i]["tier_minimo"]]
    L += ["", f"No calib (subagente correto, escolha bruta sem τ), o acerto do tier foi {pct(c2cal_raw)} (n={len(zc)}).",
          f"Tier empírico (o mais barato cuja nota do juiz fica a ≤0,25 da melhor): {dict(Counter(emp.values()))}; concorda com o rótulo do bot em {pct(sum(emp[i]==ds[i]['tier_minimo'] for i in agree)/len(agree))} dos casos — os rótulos de complexidade são frágeis.", "",
          "![tiers](report/graficos/tiers.png)", "", "## Ponta a ponta — qualidade × custo × latência (holdout)", "",
          "| Estratégia | Custo total US$ | US$/msg | Economia vs caro (IC95%) | Nota juiz (IC95%) | % nota ≥4 | US$/resposta boa | Lat P50 / P95 (s) | Overhead decisão | Truncadas |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for e in EST:
        r = rows[e]
        L.append(f"| {e} | {r['custo_total']:.4f} | {r['custo_msg']:.6f} | {pct(r['econ'])} ({pct(r['econ_ic'][0])}–{pct(r['econ_ic'][1])}) | {r['nota']:.2f} ({r['nota_ic'][0]:.2f}–{r['nota_ic'][1]:.2f}) | {pct(r['pct_ge4'])} | {r['custo_por_boa']:.5f} | {r['lat_p50']/1000:.2f} / {r['lat_p95']/1000:.2f} | {pct(r['overhead_pct'])} | {pct(r['trunc'])} |")
    L += ["", "Custo inclui as decisões MSD1 (pagas por todas as estratégias, exceto oracle) e a geração; clarificações e fora de escopo custam só a decisão. Nota do juiz = média de correção, resolução, política e tom (1–5), só nas respostas geradas.", "",
          "Truncamento por modelo (finish_reason): " + "; ".join(f"`{m}` {f}={n}" for (m, f), n in sorted(trunc_model.items())) + f". max_tokens: Gemini 400, GPT-6 Sol 800.", "",
          "![custo×qualidade](report/graficos/custo_vs_qualidade.png)", "", "![latência](report/graficos/latencia.png)", "",
          "## Gasto", "", f"- Ledger local (`runs/ledger.json`, soma de `usage.cost`): **US${led['spent_usd']:.4f}**, {led['calls']} chamadas.", "", "| Modelo | US$ |", "|---|---:|"]
    for m, v in sorted(led["by_model"].items(), key=lambda kv: -kv[1]): L.append(f"| `{m}` | {v:.4f} |")
    ku = os.environ.get("KEY_USAGE")
    if ku: L += ["", f"- Conferência OpenRouter (GET /api/v1/key, no momento do relatório): uso = US${float(ku):.4f}, limite US$20."]
    L += ["", "## Limitações", "",
          "- **Rótulos do bot, não revisados por humano** (subagente e tier). O tier empírico mostra que o rótulo de complexidade diverge bastante; os números da C2 devem ser lidos com isso em mente. Revisar `report/revisao_rotulos.csv`.",
          "- **Juiz único e barato** (DeepSeek V4.1 Flash) sem calibração humana ainda; a planilha cega de 40 itens está em `runs/" + hold.name + "/revisao_humana_juiz.csv` (chave em `revisao_humana_chave.json`). Viés de verbosidade possível a favor do modelo caro.",
          f"- **Holdout pequeno** ({man['n_itens']} mensagens, ~52 geradas por estratégia): ICs largos; diferenças de nota < ~0,3 não são conclusivas.",
          "- Mensagens de turno único, sintéticas, escritas por um só autor (provável homogeneidade de estilo); ferramentas mock injetadas no prompt, sem tool-calling real.",
          "- τ calibrados com utilidade definida por nós; a escolha de pesos muda τ. A C2 do calib usou o subagente correto; no holdout usou o escolhido pela C1.",
          "- Latência medida do box (Linux, SP), um horário só; geração depende do provedor servido pelo OpenRouter.",
          "- Sem baselines de router gerativo/Jev/OpenAI Decisions nesta rodada.", "",
          "## Evidências", "", f"- `runs/{hold.name}/` — decisions.jsonl, turns.jsonl, judge.jsonl, manifest.json, revisao_humana_juiz.csv",
          f"- `runs/{calib.name}/` — decisions.jsonl, calibracao.json (curvas de utilidade de τ1/τ2)", "- `config/thresholds.json` (τ congelados), `config/prices.json` (preços datados)",
          "- `report/tabelas/estrategias.csv`, `report/graficos/*.png`, `report/exemplos-routing.md`", "- `ESTIMATIVA_CUSTO.md` (estimativa feita antes da rodada)"]
    (ROOT / "RESULTADOS.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
