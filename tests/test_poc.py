import json, tempfile, pathlib, unittest
from harness.budget import Budget, BudgetExceeded
from harness.client import Client
from harness import pipeline as P, run as R, metrics as M, judge as J

PR = {m: {"in": 1e-6, "out": 1e-6} for m in [P.MODELS["msd1"], P.MODELS["judge"], *P.MODELS["tiers"].values()]}


class TestBudget(unittest.TestCase):
    def test_aborta_antes_do_teto(self):
        with tempfile.TemporaryDirectory() as d:
            b = Budget(pathlib.Path(d) / "l.json", stop_at=0.01)
            b.add("x", 0.009)
            with self.assertRaises(BudgetExceeded): b.check(0.002)
            b.check(0.0005)

    def test_ledger_persiste(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "l.json"; Budget(p).add("x", 0.5)
            self.assertAlmostEqual(Budget(p).spent, 0.5)

    def test_session_cap(self):
        with tempfile.TemporaryDirectory() as d:
            b = Budget(pathlib.Path(d) / "l.json", session_cap=0.1); b.add("x", 0.099)
            with self.assertRaises(BudgetExceeded): b.check(0.01)

    def test_stop_abaixo_do_hard_cap(self):
        with self.assertRaises(AssertionError): Budget("/tmp/nao-usado.json", stop_at=25)

    def test_chat_mock_aborta(self):
        with tempfile.TemporaryDirectory() as d:
            c = Client(Budget(pathlib.Path(d) / "l.json", stop_at=1e-9), PR, mock=True)
            with self.assertRaises(BudgetExceeded): c.chat(P.MODELS["tiers"]["complexa"], [{"role": "user", "content": "oi"}])


class FakeClient:
    def __init__(self, probs1, probs2): self.p1, self.p2 = probs1, probs2
    def decide(self, model, state, q):
        if "subagente" in q:
            ch = max(self.p1, key=self.p1.get)
            return {"answers": {"subagente": {"choice": ch, "probabilities": self.p1}}, "cost": 0, "lat_ms": 1}
        return {"answers": {"complexidade": {"probabilities": self.p2, "score": 0}}, "cost": 0, "lat_ms": 1}


class TestPipeline(unittest.TestCase):
    def test_c1_threshold_clarifica(self):
        c = FakeClient({"devolucao": .5, "suporte": .3, "financeiro": .2, "fora_de_escopo": 0}, {})
        ch, d = P.camada1(c, P.state_of("x"), tau1=0.6); self.assertEqual(ch, "clarificar"); self.assertTrue(d["fallback"])
        ch, _ = P.camada1(c, P.state_of("x"), tau1=0.4); self.assertEqual(ch, "devolucao")

    def test_c2_fallback(self):
        c = FakeClient({}, {"0": .45, "1": .35, "2": .2})
        self.assertEqual(P.camada2(c, {}, "suporte", tau2=0.5, fallback="complexa")[0], "complexa")
        self.assertEqual(P.camada2(c, {}, "suporte", tau2=0.5, fallback="+1")[0], "media")
        self.assertEqual(P.camada2(c, {}, "suporte", tau2=0.4)[0], "simples")

    def test_criteria_cobre_subagentes(self):
        self.assertEqual(set(P.Q_SUBAGENTE["criteria"]), {"devolucao", "suporte", "financeiro", "fora_de_escopo"})


class TestDataset(unittest.TestCase):
    def test_dataset(self):
        rows = R.load_items()
        self.assertTrue(250 <= len(rows) <= 350)
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        for r in rows:
            self.assertIn(r["label"], {"devolucao", "suporte", "financeiro", "fora_de_escopo", "clarificar"})
            if r["label"] in ("devolucao", "suporte", "financeiro"): self.assertIn(r["tier_minimo"], P.TIER_ORDER)


class TestDryRunEndToEnd(unittest.TestCase):
    def test_mock_run_metrics_judge(self):
        with tempfile.TemporaryDirectory() as d:
            out = R.main(["--mock", "--limit", "20", "--estrategias", "msd1,always-cheap,always-expensive,oracle", "--out", d])
            m = json.loads((out / "manifest.json").read_text()); self.assertEqual(m["status"], "ok")
            J.main([str(out), "--mock", "--amostra", "5"])
            r = M.compute(out)
            self.assertIn("c1", r); self.assertIn("always-expensive", r["estrategias"])
            self.assertTrue((out / "revisao_humana_juiz.csv").exists())


if __name__ == "__main__":
    unittest.main()
