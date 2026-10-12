"""Gera datasets/mensagens.jsonl (~300 mensagens fictícias rotuladas, pt-BR).
Rótulos: subagente (devolucao|suporte|financeiro|fora_de_escopo|clarificar) e tier_minimo (simples|media|complexa).
Rotulei manualmente; rótulos ainda pendentes de revisão cruzada (ver report/revisao_rotulos.csv)."""
import json, hashlib, random, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))

S, M, C = "simples", "media", "complexa"
D = [  # devolucao
 ("qual o prazo pra devolver um produto?", S), ("posso devolver se eu só abri a caixa?", S),
 ("como faço pra devolver o pedido 10403?", S), ("quero devolver o tênis do pedido 10411, não serviu", S),
 ("o frete da devolução é por minha conta?", S), ("onde eu deixo o pacote da devolução?", S),
 ("me arrependi da compra 10420, ainda dá tempo?", M), ("comprei uma caneca personalizada, posso devolver?", M),
 ("qro devolver o fone q veio, n gostei do som", S), ("pedido 10415 veio com o item errado, quero devolver", M),
 ("o liquidificador do pedido 10422 veio quebrado, quero trocar por outro", M),
 ("veio a camiseta no tamanho P e eu pedi M, pedido 10408, como troco?", M),
 ("abri a escova elétrica e não gostei, devolvo?", M), ("já mandei a devolução faz 10 dias, chegou aí?", S),
 ("posso devolver só um item do pedido 10430?", M), ("o smartwatch parou de funcionar depois de 20 dias, pedido 10433", M),
 ("recebi o pedido 10441 faz 8 dias e quero devolver por arrependimento, tem exceção?", C),
 ("comprei 3 itens com cupom no pedido 10412, um veio com defeito e quero devolver só ele, quanto volta?", C),
 ("o notebook do pedido 10404 esquenta muito, já passou 40 dias, ainda posso trocar?", C),
 ("devolvi e vocês dizem que o produto chegou usado, mas eu nem tirei da caixa! quero solução", C),
 ("i want to return my order 10417, wrong color", S), ("dá pra trocar por um modelo mais caro pagando a diferença?", M),
 ("como gero a etiqueta de devolução?", S), ("quanto tempo depois da devolução vocês analisam o produto?", S),
 ("o tênis descolou a sola, pedido 10426, quero devolver e não quero outro", M),
 ("pedido 10437 veio faltando a tampa do liquidificador, troca só a peça ou tudo?", M),
 ("tenho um pedido em trânsito, posso recusar na entrega pra devolver?", M),
 ("já é a segunda troca do mesmo produto com defeito, pedido 10445, quero devolução total e estou indignado", C),
 ("presente que recebi veio errado, não tenho nota, consigo trocar?", C),
 ("devolução do pedido 10450: a transportadora não veio buscar 2 vezes", C),
 ("dá pra devolver kit de panelas usado uma vez que manchou?", M), ("devolução por arrependimento vale pra compra na loja física?", S),
 ("quero devolver o pedido inteiro 10455 porque um item veio com defeito, o cupom volta?", C),
 ("mochila veio com zíper estragado", S), ("posso devolver produto comprado na black friday?", S),
 ("troquei o tamanho e o novo também não serviu, posso devolver agora pedido 10418?", C),
]
U = [  # suporte (pedido, entrega, uso de produto, conta)
 ("cadê meu pedido 10401?", S), ("qual o status do pedido 10414?", S), ("meu pedido ainda tá processando, normal?", S),
 ("como rastreio minha entrega?", S), ("o entregador disse que entregou mas não recebi, pedido 10409", C),
 ("como pareio o fone bluetooth X1 no celular?", S), ("o smartwatch não sincroniza com o app", M),
 ("esqueci minha senha da conta", S), ("como altero o endereço de entrega do pedido 10427?", M),
 ("o pedido 10432 aparece cancelado mas eu não cancelei", C), ("a entrega tá atrasada 5 dias, pedido 10436", M),
 ("meu pedido 10439 foi pra endereço errado", C), ("quero falar com um humano", S),
 ("ond ta meu pedio 10442", S), ("como configuro o liquidificador no modo pulsar?", S),
 ("o notebook não liga desde que chegou, o que faço antes de devolver?", M),
 ("meu pedido 10444 veio em 2 caixas e só chegou uma", M), ("dá pra agendar a entrega pra sábado?", S),
 ("where is my order 10446?", S), ("o app da loja fecha sozinho quando abro meus pedidos", M),
 ("como atualizo meu CPF no cadastro?", S), ("pedido 10448 está em trânsito há 15 dias sem atualização, estou perdendo a paciência", C),
 ("preciso da nota fiscal do pedido 10451", S), ("quero cancelar o pedido 10453 que ainda não saiu", M),
 ("como uso o modo corrida no smartwatch fit?", S), ("recebi um produto que não comprei", M),
 ("minha conta foi invadida e fizeram um pedido no meu nome", C), ("vocês entregam em zona rural?", S),
 ("o rastreio diz 'objeto aguardando retirada', onde retiro?", S),
 ("comprei 2 pedidos 10456 e 10457, um chegou e outro sumiu, e o atendimento não responde", C),
 ("como cadastro um segundo endereço?", S), ("a caixa chegou amassada, aceito ou recuso?", M),
 ("o fone só conecta de um lado", M), ("posso mudar o destinatário do pedido 10459?", M),
 ("pedido 10402 foi entregue no vizinho e ele não devolve, o que vocês fazem?", C),
 ("quanto tempo demora a entrega pra Recife?", S),
]
F = [  # financeiro (reembolso, cobrança, estorno)
 ("quando cai meu reembolso?", S), ("fui cobrado duas vezes no pedido 10405", M), ("o estorno aparece em qual fatura?", S),
 ("paguei por pix, como recebo o reembolso?", S), ("o reembolso do pedido 10410 ainda não caiu, já faz 10 dias", M),
 ("apareceu uma cobrança da loja que eu não reconheço", C), ("posso receber o reembolso em outra conta?", M),
 ("o valor do estorno veio menor do que paguei, pedido 10416", C), ("como peço segunda via do boleto?", S),
 ("paguei o boleto e o pedido 10419 diz não pago", M), ("cobrança duplicada no cartão, preciso do estorno urgente", M),
 ("quero reembolso parcial do pedido 10421, um item veio com defeito e usei cupom", C),
 ("vcs estornam o frete tbm?", S), ("estorno do pedido 10423 tá pendente, o banco disse que vocês não enviaram", C),
 ("dá pra converter o reembolso em crédito na loja?", S), ("meu cartão foi cancelado, como recebo o estorno?", M),
 ("refund for order 10428 please, it's been 2 weeks", M), ("parcelei em 10x e devolvi, as parcelas param?", M),
 ("fui cobrado pelo frete mas era frete grátis", M), ("quanto do cupom eu perco no reembolso?", M),
 ("cobraram juros no parcelamento que era sem juros, pedido 10431", C), ("quero a nota de estorno pra apresentar na empresa", S),
 ("o pix do reembolso foi pra uma chave errada", C), ("quando o estorno é processado depois que vocês recebem o item?", S),
 ("foram 3 cobranças do mesmo pedido 10434, vou no procon se não resolverem hoje", C),
 ("posso pedir reembolso do pedido cancelado 10435?", S), ("o reembolso caiu mas faltou o valor do frete", M),
 ("cobraram meu cartão antigo, não o novo", M), ("comprei, devolvi metade, e agora a fatura mostra valor cheio, pedido 10438", C),
 ("tem como antecipar o reembolso?", S), ("minha fatura veio com cobrança da loja depois do cancelamento", C),
 ("o boleto venceu, pago com juros ou gero outro?", S), ("estorno caiu em dobro, o que faço?", M),
 ("reembolso do pedido 10440 aprovado, quanto vou receber?", M), ("vcs cobram taxa pra reembolso?", S),
 ("me estornaram mas cobraram de novo no mês seguinte, absurdo, pedido 10443", C),
]
FORA = ["qual a previsão do tempo amanhã?", "me conta uma piada", "quem ganhou o jogo ontem?", "vocês contratam?",
        "qual a capital da Austrália?", "me ajuda com meu dever de matemática", "vocês vendem carros?",
        "qual o melhor celular do mercado?", "escreve um poema pra minha namorada", "como faço bolo de cenoura?"]
AMB = [  # ambíguas de propósito: label clarificar, com rótulos aceitos
 ("meu pedido deu problema", ["suporte", "devolucao", "financeiro"]),
 ("quero meu dinheiro de volta", ["financeiro", "devolucao"]),
 ("o produto veio errado e me cobraram a mais", ["devolucao", "financeiro"]),
 ("preciso resolver o pedido 10425", ["suporte", "devolucao", "financeiro"]),
 ("cancelei e ainda tá aparecendo", ["financeiro", "suporte"]),
 ("não chegou e já paguei", ["suporte", "financeiro"]),
 ("quero trocar", ["devolucao"]), ("isso é um absurdo, ninguém resolve", ["suporte", "devolucao", "financeiro"]),
 ("e o valor?", ["financeiro"]), ("tem como desfazer?", ["devolucao", "financeiro", "suporte"]),
 ("o pedido 10447 não tá certo", ["suporte", "devolucao"]), ("ajuda", ["suporte", "devolucao", "financeiro"]),
]


def build():
    from extra_v2 import D2, U2, F2, FORA2, AMB2
    rows = []
    for lab, lst in (("devolucao", D + D2), ("suporte", U + U2), ("financeiro", F + F2)):
        for t, tier in lst:
            rows.append({"mensagem": t, "label": lab, "tier_minimo": tier, "ambigua": False})
    for t in FORA + FORA2:
        rows.append({"mensagem": t, "label": "fora_de_escopo", "tier_minimo": None, "ambigua": False})
    for t, ac in AMB + AMB2:
        rows.append({"mensagem": t, "label": "clarificar", "aceitos": ac, "tier_minimo": None, "ambigua": True})
    rnd = random.Random(42); rnd.shuffle(rows)
    n = len(rows)
    for i, r in enumerate(rows):
        r["id"] = f"m{i:03d}"
        r["split"] = "calib" if i < int(n * .6) else ("valid" if i < int(n * .8) else "holdout")
        r["rotulo_status"] = "pendente-revisao-cruzada"
    return rows


if __name__ == "__main__":
    rows = build()
    p = pathlib.Path(__file__).with_name("mensagens.jsonl")
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(len(rows), "mensagens; sha256", hashlib.sha256(p.read_bytes()).hexdigest()[:16])
