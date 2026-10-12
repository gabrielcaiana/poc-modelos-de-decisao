"""Figuras extras para o README, a partir dos logs reais. Uso: .venv/bin/python -m harness.figuras_extra"""
import json, csv, io, contextlib, pathlib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from . import show

ROOT = pathlib.Path(__file__).resolve().parents[1]; G = ROOT / "report/graficos"; RUN = ROOT / "runs/20261012-holdout-live"
TH = json.loads((ROOT / "config/thresholds.json").read_text())
ds = {r["id"]: r for r in map(json.loads, (ROOT / "datasets/mensagens.jsonl").read_text().splitlines())}
D = [json.loads(l) for l in (RUN / "decisions.jsonl").read_text().splitlines()]

# 1) matriz de confusão C1 (holdout, com τ1)
L = ["devolucao", "suporte", "financeiro", "fora_de_escopo", "clarificar"]; M = [[0] * 5 for _ in L]
seen = set()
for d in D:
    if d["camada"] != 1 or d.get("reuso_cache") or d["id"] in seen: continue
    seen.add(d["id"]); c = "clarificar" if d["p_max"] < TH["tau1"] else d["raw_choice"]
    M[L.index(ds[d["id"]]["label"])][L.index(c)] += 1
fig, ax = plt.subplots(figsize=(6.5, 5.5)); ax.imshow(M, cmap="Blues")
for i in range(5):
    for j in range(5): ax.text(j, i, M[i][j], ha="center", va="center", color="white" if M[i][j] > 10 else "black")
ax.set_xticks(range(5), L, rotation=30, ha="right"); ax.set_yticks(range(5), L)
ax.set_xlabel("decisão (MSD1 + τ1)"); ax.set_ylabel("rótulo"); ax.set_title(f"Camada 1 — matriz de confusão (holdout, τ1={TH['tau1']})")
plt.tight_layout(); plt.savefig(G / "matriz_confusao_c1.png", dpi=130); plt.close()

# 2) economia vs nota (barras)
rows = list(csv.DictReader(open(ROOT / "report/tabelas/estrategias.csv")))
fig, ax1 = plt.subplots(figsize=(8, 4)); x = range(len(rows))
ax1.bar(x, [float(r["custo_msg_usd"]) * 1000 for r in rows], color="#8fb3d9"); ax1.set_ylabel("US$ por mensagem (× 10⁻³)")
ax1.set_xticks(list(x), [r["estrategia"] for r in rows], rotation=15)
ax2 = ax1.twinx(); ax2.plot(list(x), [float(r["nota"]) for r in rows], "o-", color="#c0392b"); ax2.set_ylabel("nota média do juiz", color="#c0392b"); ax2.set_ylim(3.8, 5)
ax1.set_title("Custo por mensagem (barras) × nota do juiz (linha) — holdout"); plt.tight_layout(); plt.savefig(G / "custo_e_nota_por_estrategia.png", dpi=130); plt.close()

# 3) "print" de terminal com o rastro real de duas mensagens
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    show.main(str(RUN.relative_to(ROOT)), "m246", "msd1"); print(); show.main(str(RUN.relative_to(ROOT)), "m283", "msd1")
lines = buf.getvalue().rstrip().splitlines()
fig = plt.figure(figsize=(13, 0.26 * len(lines) + 0.6)); fig.patch.set_facecolor("#1e1e1e")
for k, ln in enumerate(lines):
    col = "#6a9955" if ln.startswith("$") else ("#dcdcaa" if "MSD1" in ln else ("#9cdcfe" if "GERAÇÃO" in ln or "juiz" in ln else "#d4d4d4"))
    fig.text(0.01, 1 - (k + 1) / (len(lines) + 1), ln[:165], family="monospace", fontsize=8.5, color=col)
plt.savefig(G / "terminal_rastro_msd1.png", dpi=130, facecolor=fig.get_facecolor()); plt.close()
print("ok")
