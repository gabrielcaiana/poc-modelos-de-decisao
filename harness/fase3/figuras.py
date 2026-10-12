"""Gráficos da Fase 3 a partir do grid + parâmetros congelados. Uso: .venv/bin/python -m harness.fase3.figuras runs/fase3-grid"""
import json, sys, random, pathlib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from . import replay as R
from .tier_empirico import tier_relativo

ROOT = pathlib.Path(__file__).resolve().parents[2]; G = ROOT / "report/graficos/fase3"; G.mkdir(parents=True, exist_ok=True)
ORD = R.ORD


def main(grid):
    cg = json.loads((ROOT / "config/fase3_congelado.json").read_text()); res = json.loads((ROOT / "report/fase3/replay_resultado.json").read_text())
    ds, c1, c2, ger = R.carregar(grid); tst = R.itens_avaliaveis(ds, c1, c2, ger, "teste", cg["tau1"])
    est = {"always-cheap": "always-cheap", "always-media": "always-media", "always-expensive": "always-expensive", "oracle-regra": "oracle-regra", "oracle-empirico": "oracle-empirico"}
    for v, b in cg["c2"].items(): est[f"msd1-{v}"] = (v, b["params"])
    M = {k: R.metricas(tst, R.escolhas(tst, e)) for k, e in est.items()}
    rnd = random.Random(3); w = [it["peso"] for it in tst]; N = len(tst)
    def ci(xs):
        v = sorted(sum(w[i] * xs[i] for i in idx) / sum(w[i] for i in idx) for idx in ([rnd.randrange(N) for _ in range(N)] for _ in range(2000)))
        return v[50], v[1950]
    # 1) custo × nota com IC
    plt.figure(figsize=(8, 5.5))
    for k, m in M.items():
        lo, hi = ci(m["_q"]); clo, chi = ci(m["_c"])
        plt.errorbar(m["custo"] * 1000, m["nota"], yerr=[[m["nota"] - lo], [hi - m["nota"]]], xerr=[[1000 * (m["custo"] - clo)], [1000 * (chi - m["custo"])]], fmt="o" if k.startswith("msd1") else "s", capsize=3)
        plt.annotate(k, (m["custo"] * 1000, m["nota"]), textcoords="offset points", xytext=(5, 5), fontsize=8)
    plt.xlabel("US$ por mensagem (× 10⁻³), IC95%"); plt.ylabel("nota média do juiz (ponderada), IC95%")
    plt.title(f"Fase 3 — custo × qualidade no teste (n={N}, pareado)"); plt.grid(alpha=.3); plt.tight_layout(); plt.savefig(G / "custo_vs_qualidade_fase3.png", dpi=130); plt.close()
    # 2) forest: Δ nota vs always-media
    P = res["pareado"]; ks = [k for k in P if k.endswith("always-media")]
    plt.figure(figsize=(7, 3)); 
    for y, k in enumerate(ks):
        x = P[k]; plt.errorbar(x["d_nota"], y, xerr=[[x["d_nota"] - x["d_nota_ic"][0]], [x["d_nota_ic"][1] - x["d_nota"]]], fmt="o", capsize=4)
        plt.annotate(f"p Holm={x['p_perm_nota_holm']:.3f}", (x["d_nota_ic"][1], y), textcoords="offset points", xytext=(6, -3), fontsize=8)
    plt.axvline(0, color="gray", ls="--"); plt.yticks(range(len(ks)), [k.replace(" vs always-media", "") for k in ks]); plt.xlabel("Δ nota vs always-media (IC95% bootstrap pareado)")
    plt.title("Fase 3 — variantes da Camada 2 contra always-media"); plt.tight_layout(); plt.savefig(G / "delta_vs_always_media.png", dpi=130); plt.close()
    # 3) nota por tier da regra
    pt = res["nota_por_tier_regra"]; ks = ["always-cheap", "always-media", "always-expensive"] + [f"msd1-{v}" for v in cg["c2"]]
    plt.figure(figsize=(9, 4)); wdt = 0.13
    for j, k in enumerate(ks): plt.bar([x + j * wdt for x in range(3)], [pt[k][t] for t in ORD], wdt, label=k)
    plt.xticks([x + 2.5 * wdt for x in range(3)], ORD); plt.ylim(3, 5); plt.ylabel("nota média"); plt.legend(fontsize=7, ncol=3); plt.title("Fase 3 — nota por tier da regra (teste)")
    plt.tight_layout(); plt.savefig(G / "nota_por_tier.png", dpi=130); plt.close()
    # 4) curva τ1 no calib
    cv = {float(k): v for k, v in cg["curva_tau1_calib"].items()}; xs = sorted(cv)
    plt.figure(figsize=(6, 3.5)); plt.plot(xs, [cv[x] for x in xs], "o-"); plt.axvline(cg["tau1"], color="g", ls="--", label=f"τ1 escolhido = {cg['tau1']}")
    plt.axvline(0.9, color="r", ls=":", label="τ1 da Fase 2 = 0.9"); plt.xlabel("τ1"); plt.ylabel("utilidade média (calib)"); plt.legend(); plt.title("Fase 3 — reajuste do τ1 no calib")
    plt.grid(alpha=.3); plt.tight_layout(); plt.savefig(G / "tau1_calib.png", dpi=130); plt.close()
    # 5) matriz regra × tier empírico (teste)
    import collections; cnt = collections.Counter((it["tier_regra"], it["emp"]) for it in tst if it["tier_regra"])
    Mx = [[cnt.get((a, b), 0) for b in ORD] for a in ORD]
    fig, ax = plt.subplots(figsize=(5, 4.2)); ax.imshow(Mx, cmap="Oranges")
    for i in range(3):
        for j in range(3): ax.text(j, i, Mx[i][j], ha="center", va="center")
    ax.set_xticks(range(3), ORD); ax.set_yticks(range(3), ORD); ax.set_xlabel("tier empírico (juiz)"); ax.set_ylabel("tier da regra")
    ax.set_title("Fase 3 — regra × tier empírico (teste)"); plt.tight_layout(); plt.savefig(G / "regra_vs_empirico.png", dpi=130); plt.close()
    print("ok", [p.name for p in G.iterdir()])


if __name__ == "__main__":
    main(sys.argv[1])
