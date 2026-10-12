"""Pipeline do chatbot pós-venda: Camada 1 (subagente) e Camada 2 (tier de modelo) com MSD1, depois geração."""
import json, pathlib
from mocks.dados import contexto_ferramentas

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODELS = json.loads((ROOT / "config/models.json").read_text())
TH = json.loads((ROOT / "config/thresholds.json").read_text())
TIER_ORDER = ["simples", "media", "complexa"]

Q_SUBAGENTE = {"type": "choice", "instructions": "Qual subagente do atendimento pós-venda deve tratar a última mensagem do cliente?",
               "criteria": {
                   "devolucao": "Devolução, troca, arrependimento, produto com defeito/errado que o cliente quer devolver ou trocar, etiqueta e coleta de devolução.",
                   "suporte": "Status e rastreio de pedido, entrega/atraso/extravio, endereço, cancelamento antes do envio, conta/cadastro, uso e configuração de produto.",
                   "financeiro": "Reembolso, cobrança (duplicada, indevida, juros, boleto), estorno no cartão ou Pix, valores pagos e devolvidos.",
                   "fora_de_escopo": "Assunto não relacionado a pedidos, produtos ou pagamentos da loja."}}
Q_COMPLEXIDADE = {"type": "score", "instructions": "Qual o nível mínimo de modelo necessário para responder bem a esta mensagem de pós-venda?",
                  "criteria": [
                      "simples: pergunta direta de FAQ ou uma consulta única; sem exceções de política",
                      "media: exige cruzar dados do pedido com a política, ou 2-3 passos de raciocínio",
                      "complexa: múltiplos problemas, exceções de política, cálculo de valores, cliente irritado ou risco legal/fraude"]}

CLARIFICACAO = "Para te ajudar melhor: sua dúvida é sobre devolução/troca, sobre o andamento do pedido/entrega, ou sobre reembolso/cobrança? Se tiver, me passa o número do pedido."
FORA = "Sou o assistente de pós-venda da LojaExemplo e só consigo ajudar com pedidos, devoluções, suporte e reembolsos."

PROMPTS = {
    "devolucao": "Você é o subagente de DEVOLUÇÃO/TROCA da LojaExemplo (fictícia).",
    "suporte": "Você é o subagente de SUPORTE (pedidos, entregas, conta, uso de produto) da LojaExemplo (fictícia).",
    "financeiro": "Você é o subagente FINANCEIRO (reembolso, cobrança, estorno) da LojaExemplo (fictícia).",
}
REGRAS = ("Responda em pt-BR, em no máximo 120 palavras, com tom cordial. Use SOMENTE os dados das ferramentas e a política abaixo; "
          "não invente prazos, valores ou exceções. Se faltar dado (ex.: número do pedido), peça.")


def state_of(msg, historico=None):
    return {"historico": historico or [], "mensagem_cliente": msg}


def camada1(client, state, tau1=None):
    tau1 = TH["tau1"] if tau1 is None else tau1
    d = client.decide(MODELS["msd1"], state, {"subagente": Q_SUBAGENTE})
    a = d["answers"]["subagente"]
    pmax = max(a["probabilities"].values())
    choice = a["choice"] if pmax >= tau1 else "clarificar"
    return choice, {**d, "camada": 1, "probs": a["probabilities"], "raw_choice": a["choice"], "p_max": pmax, "tau": tau1,
                    "fallback": pmax < tau1}


def camada2(client, state, subagente, tau2=None, fallback=None):
    tau2 = TH["tau2"] if tau2 is None else tau2
    fallback = fallback or TH["fallback_c2"]
    d = client.decide(MODELS["msd1"], {**state, "subagente": subagente}, {"complexidade": Q_COMPLEXIDADE})
    a = d["answers"]["complexidade"]
    probs = {TIER_ORDER[int(k)]: v for k, v in a["probabilities"].items()}
    raw = max(probs, key=probs.get); pmax = probs[raw]
    if pmax >= tau2:
        tier = raw
    elif fallback == "+1":
        tier = TIER_ORDER[min(TIER_ORDER.index(raw) + 1, 2)]
    else:
        tier = "complexa"
    return tier, {**d, "camada": 2, "probs": probs, "raw_choice": raw, "score": a.get("score"), "p_max": pmax, "tau": tau2,
                  "fallback": pmax < tau2, "tier_final": tier}


def gerar(client, subagente, tier, msg, historico=None):
    ctx = contexto_ferramentas(subagente, msg)
    sys = f"{PROMPTS[subagente]} {REGRAS}\n\n{ctx}"
    msgs = [{"role": "system", "content": sys}] + [{"role": h["role"], "content": h["content"]} for h in (historico or [])]
    msgs.append({"role": "user", "content": msg})
    return {**client.chat(MODELS["tiers"][tier], msgs), "contexto": ctx}


def turno(client, estrategia, item, cache_c1=None):
    """Executa um turno. Estratégias: msd1, always-cheap, always-media, always-expensive, oracle.
    cache_c1 permite reaproveitar a decisão da Camada 1 entre estratégias (é idêntica nelas)."""
    st = state_of(item["mensagem"], item.get("historico"))
    decs = []
    if estrategia == "oracle":
        sub = item["label"]
    else:
        if cache_c1 is not None and item["id"] in cache_c1:
            sub, d1 = cache_c1[item["id"]]; d1 = {**d1, "reuso_cache": True}
        else:
            sub, d1 = camada1(client, st)
            if cache_c1 is not None: cache_c1[item["id"]] = (sub, d1)
        decs.append(d1)
    if sub == "clarificar":
        return {"tipo": "clarificar", "subagente": sub, "tier": None, "resposta": CLARIFICACAO, "decisoes": decs, "geracao": None}
    if sub == "fora_de_escopo":
        return {"tipo": "fora_de_escopo", "subagente": sub, "tier": None, "resposta": FORA, "decisoes": decs, "geracao": None}
    if estrategia == "msd1":
        tier, d2 = camada2(client, st, sub); decs.append(d2)
    elif estrategia == "always-cheap":
        tier = "simples"
    elif estrategia == "always-media":
        tier = "media"
    elif estrategia == "always-expensive":
        tier = "complexa"
    elif estrategia == "oracle":
        tier = item.get("tier_minimo") or "simples"
    else:
        raise ValueError(estrategia)
    g = gerar(client, sub, tier, item["mensagem"], item.get("historico"))
    return {"tipo": "resposta", "subagente": sub, "tier": tier, "resposta": g["text"], "decisoes": decs, "geracao": g}
