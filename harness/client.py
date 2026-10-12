"""Cliente OpenRouter (stdlib apenas) para chat e para o endpoint de decisões (MSD1), com modo mock.
A chave vem SÓ de OPENROUTER_API_KEY e nunca é impressa/logada."""
import json, os, time, urllib.request, urllib.error, hashlib, random, pathlib
from .budget import Budget

BASE = "https://openrouter.ai/api"
ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_prices(cache=ROOT / "config/prices.json", refresh=False, ids=None):
    """Preços por token (US$) vindos de /api/v1/models; salva cópia datada em config/prices.json."""
    extra = {k: v for k, v in json.loads((ROOT / "config/prices_extra.json").read_text()).items() if not k.startswith("_")}
    if cache.exists() and not refresh:
        return {**extra, **json.loads(cache.read_text())["models"]}
    with urllib.request.urlopen(BASE + "/v1/models", timeout=30) as r:
        data = json.load(r)["data"]
    models = {m["id"]: {"in": float(m["pricing"]["prompt"]), "out": float(m["pricing"]["completion"])}
              for m in data if ids is None or m["id"] in ids}
    cache.write_text(json.dumps({"_fonte": BASE + "/v1/models", "_data": time.strftime("%Y-%m-%d %H:%M %Z"),
                                 "models": models}, indent=2))
    return {**extra, **models}


def est_tokens(text: str) -> int:
    return max(1, len(text) // 3)  # pt-BR ~3-4 chars/token; conservador


class Client:
    def __init__(self, budget: Budget, prices: dict, mock=False, timeout=60):
        self.budget, self.prices, self.mock, self.timeout = budget, prices, mock, timeout
        self.key = None if mock else os.environ.get("OPENROUTER_API_KEY")
        if not mock and not self.key:
            raise RuntimeError("OPENROUTER_API_KEY não definida")

    def _post(self, path, body):
        req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json",
                                              "X-Title": "poc-modelos-de-decisao"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < 2:
                    time.sleep(2 ** attempt); continue
                raise RuntimeError(f"HTTP {e.code} em {path}: {e.read()[:300]!r}") from None

    def _cost(self, model, usage, in_key, out_key):
        if usage.get("cost") is not None:
            return float(usage["cost"]), "openrouter_usage"
        p = self.prices.get(model) or {"in": 0, "out": 0}
        return usage.get(in_key, 0) * p["in"] + usage.get(out_key, 0) * p["out"], "tabela_precos"

    # ---------- decisões (MSD1) ----------
    def decide(self, model, state, questions):
        p = self.prices.get(model, {"in": 0.042e-6, "out": 0})
        reserve = (est_tokens(json.dumps(state, ensure_ascii=False) + json.dumps(questions, ensure_ascii=False)) + 400) * max(p["in"], 1e-7) * 2
        self.budget.check(reserve)
        t0 = time.perf_counter()
        if self.mock:
            r = mock_decision(model, state, questions)
        else:
            r = self._post("/alpha/decisions", {"model": model, "state": state, "questions": questions})
        lat = (time.perf_counter() - t0) * 1000
        cost, src = self._cost(model, r.get("usage", {}), "input_tokens", "output_tokens")
        self.budget.add(model, cost)
        return {"answers": r["answers"], "model": r.get("model"), "provider": r.get("provider"),
                "usage": r.get("usage", {}), "cost": cost, "cost_src": src, "lat_ms": lat}

    # ---------- chat ----------
    def chat(self, model, messages, max_tokens=400, temperature=0.2, extra=None):
        p = self.prices[model]
        reserve = est_tokens("".join(m["content"] for m in messages)) * p["in"] + max_tokens * p["out"]
        self.budget.check(reserve * 1.2)
        t0 = time.perf_counter()
        if self.mock:
            r = mock_chat(model, messages, max_tokens)
        else:
            r = self._post("/v1/chat/completions", {"model": model, "messages": messages, "max_tokens": max_tokens,
                                                    "temperature": temperature, "usage": {"include": True}, **(extra or {})})
        lat = (time.perf_counter() - t0) * 1000
        u = r.get("usage", {})
        cost, src = self._cost(model, u, "prompt_tokens", "completion_tokens")
        self.budget.add(model, cost)
        return {"text": r["choices"][0]["message"].get("content") or "", "finish": r["choices"][0].get("finish_reason"), "model": r.get("model"), "provider": r.get("provider"),
                "usage": u, "cost": cost, "cost_src": src, "lat_ms": lat}

    def key_usage(self):
        """Gasto da chave segundo o OpenRouter (GET /v1/key), para conferir o ledger local."""
        req = urllib.request.Request(BASE + "/v1/key", headers={"Authorization": f"Bearer {self.key}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)["data"]
        return {k: d.get(k) for k in ("usage", "limit", "limit_remaining")}


# ---------- mocks determinísticos (dry-run, custo zero) ----------
def _rng(*parts):
    return random.Random(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest())


def mock_decision(model, state, questions):
    ans = {}
    for name, q in questions.items():
        crit = q["criteria"]
        keys = list(crit) if isinstance(crit, dict) else [str(i) for i in range(len(crit))]
        rnd = _rng(model, json.dumps(state, sort_keys=True, ensure_ascii=False), name)
        w = [rnd.random() ** 3 for _ in keys]; s = sum(w); probs = {k: round(x / s, 4) for k, x in zip(keys, w)}
        best = max(probs, key=probs.get)
        a = {"type": q["type"], "probabilities": probs, "confidence": probs[best]}
        if q["type"] == "noul":
            ans[name] = {"type": "noul", "noul": round(rnd.random(), 4)}; continue
        if q["type"] == "choice":
            a["choice"] = best
        else:
            a["score"] = sum(int(k) * v for k, v in probs.items()); a["legend"] = {str(i): c for i, c in enumerate(crit)}
        ans[name] = a
    return {"answers": ans, "model": model + "-mock", "provider": "mock", "usage": {"input_tokens": 500, "output_tokens": 0}}


def mock_chat(model, messages, max_tokens):
    last = messages[-1]["content"]
    if "NOTA_JSON" in messages[0]["content"]:
        rnd = _rng(model, last)
        txt = json.dumps({"correcao": rnd.randint(2, 5), "resolucao": rnd.randint(2, 5), "politica": rnd.randint(3, 5),
                          "tom": rnd.randint(3, 5), "justificativa": "mock"})
    else:
        txt = f"[mock {model}] Resposta simulada para: {last[-80:]}"
    return {"choices": [{"message": {"content": txt}, "finish_reason": "stop"}], "model": model, "provider": "mock",
            "usage": {"prompt_tokens": est_tokens("".join(m["content"] for m in messages)), "completion_tokens": 120}}
