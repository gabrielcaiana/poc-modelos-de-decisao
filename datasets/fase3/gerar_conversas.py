"""Fase 3: gera datasets/fase3/conversas.jsonl — conversas multi-turno fictícias (pt-BR) com contexto de pedido.
Gerado por templates combinatórios determinísticos (seed fixa), escritos com apoio de um LLM; rótulos derivados por REGRA
a partir de atributos explícitos de cada cenário, e ainda não revisados por humano.
Regra de tier (tier_regra):
  simples  = pergunta de política/FAQ ou consulta direta, sem cruzar dados do pedido com a política;
  media    = exige cruzar dados do pedido (status, dias, itens, pagamento) com a política, um problema só;
  complexa = 2+ problemas, exceção de política, cálculo de valor (cupom/parcial), fraude/risco, ou cliente irritado com histórico de falhas.
Uso: python3 datasets/fase3/gerar_conversas.py [--n 1000]"""
import json, random, hashlib, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from mocks.dados import PEDIDOS

R = random.Random(3)
IDS = sorted(PEDIDOS)
# (subagente, tier, atributos, [paráfrases da mensagem final]) — {p} = nº do pedido, {item} = item do pedido
CEN = [
 # ---- devolução
 ("devolucao", "simples", {}, ["qual o prazo pra devolver?", "o frete da devolução é pago por mim?", "como gero a etiqueta de devolução?", "posso devolver produto em promoção?", "onde deixo o pacote da devolução?", "devolução vale pra loja física?", "prazo conta da compra ou da entrega?", "posso devolver sem a caixa original?", "vocês buscam o produto em casa?", "troca de tamanho tem custo?", "aceita devolução de item de higiene aberto?", "como embalo o produto pra devolver?", "quanto tempo vocês levam pra analisar a devolução?", "posso trocar por outro modelo?"]),
 ("devolucao", "media", {"pedido": 1}, ["quero devolver o {item} do pedido {p}, ainda dá?", "o {item} do pedido {p} veio com defeito, como troco?", "veio o {item} errado no pedido {p}", "o {item} do pedido {p} parou de funcionar, tá na garantia?", "dá pra devolver o {item}? é do pedido {p}"]),
 ("devolucao", "complexa", {"pedido": 1, "multi": 1, "calculo": 1}, ["no pedido {p} usei cupom, um item veio com defeito e quero devolver só ele. quanto volta?", "quero devolver o {item} do pedido {p} e trocar o outro item por um maior, como fica o valor?"]),
 ("devolucao", "complexa", {"pedido": 1, "excecao": 1, "irritado": 1}, ["é a segunda troca do {item} do pedido {p} com defeito, quero meu dinheiro e não outro, isso é um absurdo", "passou do prazo mas o {item} do pedido {p} nunca funcionou direito, vocês têm que aceitar"]),
 # ---- suporte
 ("suporte", "simples", {}, ["vocês entregam no sábado?", "como mudo minha senha?", "como cadastro outro endereço?", "qual o telefone do atendimento?", "como rastreio meu pedido?", "entregam em zona rural?", "como pareio o fone bluetooth?", "como atualizo meu CPF?", "dá pra retirar na loja?", "como excluo minha conta?", "o app mostra o rastreio?", "como configuro o smartwatch?", "qual o prazo de entrega pra Recife?", "vocês avisam por whatsapp?"]),
 ("suporte", "media", {"pedido": 1}, ["cadê o pedido {p}?", "o pedido {p} tá atrasado?", "dá pra cancelar o pedido {p}?", "o pedido {p} já saiu pra entrega?", "posso mudar o endereço do pedido {p}?"]),
 ("suporte", "complexa", {"pedido": 1, "risco": 1}, ["o pedido {p} consta entregue mas não recebi nada e já é a terceira vez que reclamo", "alguém fez o pedido {p} na minha conta, não fui eu"]),
 ("suporte", "complexa", {"pedido": 1, "multi": 1}, ["o pedido {p} veio pela metade e o restante sumiu do rastreio, e ainda querem cobrar frete de novo"]),
 # ---- financeiro
 ("financeiro", "simples", {}, ["quanto tempo leva o reembolso no pix?", "o estorno sai em qual fatura?", "vocês cobram taxa de reembolso?", "como peço segunda via do boleto?", "dá pra receber o reembolso como crédito na loja?", "reembolso cai em dia útil?", "vocês estornam o frete?", "o boleto venceu, gero outro?", "dá pra antecipar o reembolso?", "como vejo o comprovante do estorno?", "parcelado, o estorno volta parcelado?", "vocês cobram IOF?"]),
 ("financeiro", "media", {"pedido": 1}, ["quando cai o reembolso do pedido {p}?", "fui cobrado duas vezes no pedido {p}?", "o estorno do pedido {p} já foi feito?", "quanto vou receber de volta do pedido {p}?", "paguei o pedido {p} e aparece como não pago"]),
 ("financeiro", "complexa", {"pedido": 1, "calculo": 1, "multi": 1}, ["devolvi só o {item} do pedido {p}, que tinha cupom, e o estorno veio menor. quero o cálculo", "parcelei o pedido {p}, devolvi metade e a fatura continua cheia"]),
 ("financeiro", "complexa", {"pedido": 1, "risco": 1, "irritado": 1}, ["três cobranças do pedido {p} no meu cartão, vou abrir chargeback e ir no procon se não resolverem hoje"]),
]
FORA = ["qual a previsão do tempo?", "me conta uma piada", "quem ganhou o jogo?", "como faço bolo de cenoura?", "vocês contratam?", "me ajuda com meu currículo"]
AMB = [("deu problema de novo", ["suporte", "devolucao", "financeiro"]), ("quero meu dinheiro de volta", ["financeiro", "devolucao"]),
       ("cancela tudo", ["suporte", "financeiro", "devolucao"]), ("ainda não resolveram", ["suporte", "devolucao", "financeiro"]),
       ("e agora?", ["suporte", "devolucao", "financeiro"]), ("veio diferente e mais caro", ["devolucao", "financeiro"])]
# Peso de cada tier na amostragem (alvo: ~60/28/12 entre as mensagens roteáveis)
PESO_TIER = {"simples": 0.60, "media": 0.28, "complexa": 0.12}
PREF = ["", "", "", "oi, ", "boa tarde! ", "olá, uma dúvida: ", "preciso saber: ", "por favor, "]
SUF = ["", "", "", " obrigado", " pfv", "??", " é urgente", " valeu"]
RUIDO = [lambda s: s, lambda s: s, lambda s: s, lambda s: s.replace("você", "vc").replace("que", "q"),
         lambda s: s.lower().replace("?", ""), lambda s: "oi, " + s, lambda s: s + " pfv", lambda s: s.replace("pedido", "pedio")]


def historico(cen_attrs, pid):
    """0–3 turnos anteriores: saudação, pedido do número do pedido, cliente informa o pedido."""
    h = []
    k = R.choice([0, 0, 1, 2, 3]) if not cen_attrs.get("pedido") else R.choice([0, 2, 2, 3])
    if k >= 1: h += [{"role": "user", "content": R.choice(["oi", "olá, boa tarde", "bom dia, preciso de ajuda"])},
                     {"role": "assistant", "content": "Olá! Como posso ajudar?"}]
    if k >= 2 and cen_attrs.get("pedido"):
        h += [{"role": "user", "content": R.choice(["é sobre uma compra", "tenho um problema com um pedido"])},
              {"role": "assistant", "content": "Claro! Qual o número do pedido?"}]
    if k >= 3 and cen_attrs.get("pedido"):
        h += [{"role": "user", "content": f"é o {pid}"}, {"role": "assistant", "content": "Obrigado, já localizei. O que aconteceu?"}]
    return h


def build(n=1000):
    rows = []
    n_fora, n_amb = round(n * 0.04), round(n * 0.06); n_rot = n - n_fora - n_amb
    por_tier = {t: [c for c in CEN if c[1] == t] for t in PESO_TIER}
    vistos = set()
    while len(rows) < n_rot:
        t = R.choices(list(PESO_TIER), weights=list(PESO_TIER.values()))[0]
        sub, tier, attrs, msgs = R.choice(por_tier[t])
        pid = R.choice(IDS); ped = PEDIDOS[pid]; item = R.choice(ped["itens"])["nome"].split()[0].lower()
        h = historico(attrs, pid)
        texto = R.choice(msgs).format(p=pid, item=item)
        if attrs.get("pedido") and h and any(pid in x["content"] for x in h) and R.random() < 0.5:
            texto = texto.replace(f" do pedido {pid}", "").replace(f" no pedido {pid}", "").replace(f"pedido {pid}", "meu pedido")  # pedido só no histórico
        texto = R.choice(RUIDO)(R.choice(PREF) + texto + R.choice(SUF))
        chave = (texto, json.dumps(h, ensure_ascii=False))
        if chave in vistos: continue  # sem duplicatas exatas (evita vazamento calib → teste)
        vistos.add(chave)
        rows.append({"historico": h, "mensagem": texto, "label": sub, "tier_regra": tier, "atributos": attrs,
                     "pedido_contexto": pid if attrs.get("pedido") else None, "ambigua": False})
    fora = set()
    while len(fora) < n_fora: fora.add(R.choice(PREF) + R.choice(FORA) + R.choice(SUF))
    for m in sorted(fora): rows.append({"historico": [], "mensagem": m, "label": "fora_de_escopo", "tier_regra": None, "atributos": {}, "pedido_contexto": None, "ambigua": False})
    amb = 0
    while amb < n_amb:
        m, ac = R.choice(AMB); pid = R.choice(IDS); m = R.choice(RUIDO)(R.choice(PREF) + m + R.choice(SUF))
        h = [{"role": "user", "content": f"meu pedido é o {pid}"}, {"role": "assistant", "content": "Obrigado! Em que posso ajudar?"}] if R.random() < .5 else []
        if (m, json.dumps(h, ensure_ascii=False)) in vistos: continue
        vistos.add((m, json.dumps(h, ensure_ascii=False))); amb += 1
        rows.append({"historico": h, "mensagem": m, "label": "clarificar", "aceitos": ac, "tier_regra": None, "atributos": {}, "pedido_contexto": pid if h else None, "ambigua": True})
    R.shuffle(rows)
    for k, r in enumerate(rows):
        r["id"] = f"c{k:04d}"; r["split"] = "calib" if k < int(n * 0.4) else "teste"
        r["status_rotulo"] = "regra-sem-revisao-humana"
    # Subconjunto com geração nos 3 tiers, estratificado por tier_regra com SOBREAMOSTRAGEM da cauda complexa
    # (para ter poder estatístico nos casos difíceis). Cada item recebe "peso" = fração na população do split /
    # fração na amostra, para que as médias ponderadas reflitam a distribuição realista (~60/28/12).
    COTA = {"calib": {"simples": 70, "media": 40, "complexa": 30, None: 10}, "teste": {"simples": 140, "media": 80, "complexa": 60, None: 20}}
    for sp, cota in COTA.items():
        pop = [r for r in rows if r["split"] == sp]
        for t, m in cota.items():
            grupo = [r for r in pop if r["tier_regra"] == t]
            for r in grupo[:m]:
                r["gerar"] = True; r["peso"] = round((len(grupo) / len(pop)) / (m / sum(cota.values())), 4)
    return rows


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 1000
    rows = build(n); p = pathlib.Path(__file__).with_name("conversas.jsonl")
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(len(rows), "conversas; sha256", hashlib.sha256(p.read_bytes()).hexdigest()[:16])
