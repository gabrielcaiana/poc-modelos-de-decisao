import json, tempfile, pathlib, unittest
from harness.fase3 import variantes as V, replay as RP, run_grid as RG, tier_empirico as TE

ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestDataset3(unittest.TestCase):
    def setUp(self): self.rows = [json.loads(l) for l in (ROOT / "datasets/fase3/conversas.jsonl").read_text().splitlines()]
    def test_tamanho_e_unicidade(self):
        self.assertTrue(800 <= len(self.rows) <= 1500)
        self.assertEqual(len({(r["mensagem"], json.dumps(r["historico"])) for r in self.rows}), len(self.rows))
    def test_distribuicao_realista(self):
        rot = [r for r in self.rows if r["tier_regra"]]; f = lambda t: sum(r["tier_regra"] == t for r in rot) / len(rot)
        self.assertGreater(f("simples"), .5); self.assertLess(f("complexa"), .2); self.assertGreater(f("complexa"), .05)
    def test_multiturno_e_contexto(self):
        self.assertGreater(sum(bool(r["historico"]) for r in self.rows) / len(self.rows), .5)
        self.assertTrue(any(r["pedido_contexto"] and r["pedido_contexto"] not in r["mensagem"] for r in self.rows))
    def test_pesos(self):
        g = [r for r in self.rows if r.get("gerar")]; self.assertEqual(len(g), 450)
        for sp in ("calib", "teste"):
            gs = [r for r in g if r["split"] == sp]; self.assertAlmostEqual(sum(r["peso"] for r in gs) / len(gs), 1.0, delta=0.02)


class TestPolitica(unittest.TestCase):
    def test_score(self):
        rec = {"probs": {"simples": .45, "media": .35, "complexa": .2}}
        self.assertEqual(V.politica(rec, "v2_ctx", {"tau": .4}), "simples")
        self.assertEqual(V.politica(rec, "v2_ctx", {"tau": .5, "fallback": "complexa"}), "complexa")
        self.assertEqual(V.politica(rec, "v2_ctx", {"tau": .5, "fallback": "+1"}), "media")
    def test_noul(self):
        rec = {"probs": {"p_basta_simples": .3, "p_precisa_forte": .8}}
        self.assertEqual(V.politica(rec, "v3_noul", {"ta": .5, "tb": .7}), "complexa")
        self.assertEqual(V.politica(rec, "v3_noul", {"ta": .5, "tb": .9}), "media")
        self.assertEqual(V.politica(rec, "v3_noul", {"ta": .2, "tb": .9}), "simples")


class TestEstatistica(unittest.TestCase):
    def test_holm(self):
        self.assertEqual(RP.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    def test_pareado_identico(self):
        itens = [{"peso": 1.0}] * 20; m = {"_q": [4.0] * 20, "_c": [0.001] * 20, "_p": [True] * 20}
        r = RP.pareado(itens, m, m, n=200); self.assertEqual(r["d_nota"], 0); self.assertEqual(r["mcnemar_p"], 1.0)
    def test_tier_empirico(self):
        n = {"simples": {"media": 4.0, "politica": 4}, "media": {"media": 4.75, "politica": 5}, "complexa": {"media": 4.8, "politica": 5}}
        self.assertEqual(TE.tier_relativo(n), "media"); self.assertEqual(TE.tier_absoluto(n), ("media", False))


class TestGridMock(unittest.TestCase):
    def test_grid_retomavel_e_replay(self):
        with tempfile.TemporaryDirectory() as d:
            rows = [json.loads(l) for l in (ROOT / "datasets/fase3/conversas.jsonl").read_text().splitlines()]
            ids = ",".join([r["id"] for r in rows if r.get("gerar") and r["split"] == "calib"][:40] + [r["id"] for r in rows if r.get("gerar") and r["split"] == "teste"][:40])
            RG.main(["--mock", "--ids", ids, "--out", d]); n1 = len((pathlib.Path(d) / "grid.jsonl").read_text().splitlines())
            RG.main(["--mock", "--ids", ids, "--out", d]); n2 = len((pathlib.Path(d) / "grid.jsonl").read_text().splitlines())
            self.assertEqual(n1, n2)  # retomada não repete chamadas
            res = RP.main(d, tau1=0.0, out=str(pathlib.Path(d) / "rep"))
            self.assertIn("always-media", res["teste"]); self.assertTrue((pathlib.Path(d) / "rep/RESULTADOS_FASE3.md").exists())


if __name__ == "__main__":
    unittest.main()
