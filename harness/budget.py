"""Contador de custo com teto rígido. Persiste em runs/ledger.json (acumula entre execuções).
Antes de cada chamada reserva o custo MÁXIMO possível; se spent + reserva > stop_at, aborta (BudgetExceeded)."""
import json, pathlib, threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/budget.json").read_text())


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    def __init__(self, ledger_path=None, stop_at=None, session_cap=None):
        self.path = pathlib.Path(ledger_path or ROOT / "runs/ledger.json")
        self.stop_at = float(stop_at if stop_at is not None else CFG["stop_at_usd"])
        assert self.stop_at < CFG["hard_cap_usd"], "stop_at precisa ficar abaixo do teto rígido"
        self.session_cap = session_cap  # teto extra por execução (ex.: smoke = 0.10)
        self.session_spent = 0.0
        self._lock = threading.Lock()
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {"spent_usd": 0.0, "calls": 0, "by_model": {}}

    @property
    def spent(self):
        return self.data["spent_usd"]

    def check(self, reserve_usd: float):
        if self.spent + reserve_usd > self.stop_at:
            raise BudgetExceeded(f"gasto acumulado US${self.spent:.4f} + reserva US${reserve_usd:.4f} > parada US${self.stop_at}")
        if self.session_cap is not None and self.session_spent + reserve_usd > self.session_cap:
            raise BudgetExceeded(f"sessão US${self.session_spent:.4f} + reserva US${reserve_usd:.4f} > teto da sessão US${self.session_cap}")

    def add(self, model: str, cost_usd: float):
        with self._lock:
            self.data["spent_usd"] += cost_usd
            self.data["calls"] += 1
            self.data["by_model"][model] = self.data["by_model"].get(model, 0.0) + cost_usd
            self.session_spent += cost_usd
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=2))
