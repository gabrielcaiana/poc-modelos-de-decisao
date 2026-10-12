# Análise do tier empírico — Fase 3 (calib + teste, rótulo = regra)

Neste arquivo eu investigo por que o rótulo de complexidade bate tão pouco com o tier que de fato foi necessário.

- Mensagens com resposta e nota nos 3 tiers: **416** (401 com rótulo de tier).
- Concordância rótulo × tier empírico **relativo** (≤0,25 da melhor nota): **55.6%**; × **absoluto** (média ≥4,5 e política ≥4): **58.4%**.
- Direção (relativo): {'igual': 223, 'empirico_mais_barato': 147, 'empirico_mais_caro': 31}. Direção (absoluto): {'igual': 234, 'empirico_mais_barato': 141, 'empirico_mais_caro': 26}.
- Nota média por tier: simples 4.33, media 4.54, complexa 4.66. O modelo barato já passa no critério absoluto em **71.6%** das mensagens; 9 mensagens não passam em nenhum tier.
- Distribuição — rótulo: {'simples': 191, 'media': 120, 'complexa': 90}; empírico relativo: {'simples': 293, 'media': 79, 'complexa': 44}; empírico absoluto: {'simples': 298, 'media': 65, 'complexa': 53}.

## Por presença de número de pedido (exige cruzar dados da ferramenta com a política)

| grupo | n | barato passa (absoluto) | rótulo = empírico | empírico mais caro que o rótulo | empírico mais barato que o rótulo |
|---|---:|---:|---:|---:|---:|
| com_pedido | 221 | 53.8% | 55/209 | 8 | 146 |
| sem_pedido | 195 | 91.8% | 168/192 | 23 | 1 |

## Matriz rótulo (linhas) × tier empírico relativo (colunas)

| rótulo | simples | media | complexa |
|---|---:|---:|---:|
| simples | 168 | 14 | 9 |
| media | 83 | 29 | 8 |
| complexa | 33 | 31 | 26 |

## Matriz rótulo × tier empírico absoluto

| rótulo | simples | media | complexa |
|---|---:|---:|---:|
| simples | 175 | 8 | 8 |
| media | 85 | 25 | 10 |
| complexa | 29 | 27 | 34 |

## Discordâncias (rótulo ≠ empírico relativo)

| id | mensagem | rótulo | relativo | absoluto | notas simples/media/complexa |
|---|---|---|---|---|---|
| c0000 | fui cobrado duas vezes no pedido 10435? obrigado | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0002 | por favor, três cobranças do pedido 10406 no meu cartão, vou abrir cha | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0007 | boa tarde! passou do prazo mas o notebook do pedido 10455 nunca funcio | complexa | media | media | 4.00 / 4.75 / 4.75 |
| c0005 | devolvi só o kit do pedido 10452, que tinha cupom, e o estorno veio me | complexa | media | media | 2.75 / 4.75 / 4.75 |
| c0009 | boa tarde! quando cai o reembolso do pedido 10418??? | media | simples | simples | 5.00 / 5.00 / 4.75 |
| c0013 | o fone parou de funcionar, tá na garantia? obrigado | media | simples | simples | 4.75 / 5.00 / 4.75 |
| c0017 | por favor, prazo conta da compra ou da entrega??? | simples | complexa | media | 3.25 / 4.50 / 5.00 |
| c0023 | olá, uma dúvida: três cobranças do pedido 10411 no meu cartão, vou abr | complexa | simples | simples | 4.50 / 4.50 / 4.75 |
| c0026 | oi, por favor, o estorno do pedido 10429 já foi feito? | media | simples | simples | 4.50 / 4.75 / 4.50 |
| c0030 | preciso saber: o caneca do pedido 10401 parou de funcionar, tá na gara | media | simples | simples | 4.50 / 2.50 / 4.75 |
| c0029 | oi, como excluo minha conta? obrigado | simples | media | media | 3.00 / 4.75 / 3.25 |
| c0033 | oi, como excluo minha conta? é urgente | simples | media | complexa | 2.50 / 4.25 / 4.00 |
| c0036 | olá, uma dúvida: passou do prazo mas o mochila do pedido 10421 nunca f | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0038 | três cobranças do pedido 10406 no meu cartão, vou abrir chargeback e i | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0039 | boa tarde! passou do prazo mas o notebook do pedido 10440 nunca funcio | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0041 | oi, oi, quanto vou receber de volta do pedido 10400? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0048 | boa tarde! quero devolver o camiseta do pedido 10454, ainda dá? | media | simples | simples | 5.00 / 5.00 / 5.00 |
| c0047 | preciso saber: o escova do pedido 10424 parou de funcionar, tá na gara | media | simples | simples | 4.75 / 4.25 / 4.75 |
| c0062 | preciso saber: cadê o pedido 10440? obrigado | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0065 | oi, paguei o meu pedido e aparece como não pago é urgente | media | complexa | complexa | 2.75 / 2.50 / 4.75 |
| c0063 | olá, uma dúvida: vocês cobram IOF? pfv | simples | media | media | 3.50 / 4.50 / 4.75 |
| c0069 | boa tarde! veio o liquidificador errado no pedido 10437 valeu | media | complexa | complexa | 2.25 / 4.00 / 4.75 |
| c0070 | oi, dá pra devolver o kit? é do pedido 10428 valeu pfv | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0071 | por favor, paguei o pedido 10447 e aparece como não pago | media | simples | complexa | 4.25 / 1.75 / 4.50 |
| c0073 | no pedido 10432 usei cupom, um item veio com defeito e quero devolver  | complexa | simples | simples | 4.50 / 4.75 / 4.75 |
| c0075 | preciso saber: qro devolver o notebook do pedido 10455, ainda dá? | media | simples | simples | 4.50 / 4.50 / 4.75 |
| c0076 | oi, dá pra devolver o kit? é do pedido 10423 obrigado pfv | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0077 | oi, o liquidificador do pedido 10437 parou de funcionar, tá na garanti | media | simples | simples | 4.50 / 4.25 / 4.75 |
| c0083 | prazo conta da compra ou da entrega? é urgente | simples | media | media | 4.25 / 4.50 / 4.75 |
| c0086 | o pedido 10421 tá atrasado? pfv | media | simples | simples | 5.00 / 4.75 / 4.75 |
| c0088 | olá, uma dúvida: vcs entregam no sábado? | simples | media | media | 4.25 / 4.75 / 4.50 |
| c0085 | oi, olá, uma dúvida: três cobranças do pedido 10428 no meu cartão, vou | complexa | media | media | 3.00 / 4.75 / 4.75 |
| c0091 | oi, preciso saber: dá pra devolver o mochila? é do pedido 10421 | media | simples | simples | 5.00 / 4.75 / 4.75 |
| c0092 | o estorno do pedido 10403 já foi feito? valeu | media | simples | simples | 4.50 / 4.75 / 4.50 |
| c0090 | o pedido 10410 tá atrasado? | media | simples | simples | 4.75 / 4.75 / 5.00 |
| c0100 | no meu pedido usei cupom, um item veio com defeito e qro devolver só e | complexa | media | complexa | 2.75 / 4.00 / 2.50 |
| c0099 | cadê o pedido 10433? obrigado | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0107 | preciso saber: como atualizo meu CPF? | simples | media | media | 3.50 / 4.50 / 3.75 |
| c0110 | preciso saber: o pedido 10400 consta entregue mas não recebi nada e já | complexa | media | media | 2.50 / 4.75 / 4.50 |
| c0105 | boa tarde! fui cobrado duas vezes no pedido 10424? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0114 | alguém fez o pedido 10448 na minha conta, não fui eu | complexa | simples | simples | 4.50 / 4.75 / 4.50 |
| c0115 | oi, quanto vou receber de volta do pedio 10456? | media | complexa | complexa | 4.00 / 4.25 / 4.75 |
| c0116 | preciso saber: paguei o pedido 10418 e aparece como não pago | media | complexa | complexa | 2.50 / 4.25 / 4.75 |
| c0118 | oi, por favor, é a segunda troca do mochila do pedido 10420 com defeit | complexa | media | media | 4.00 / 4.75 / 4.75 |
| c0129 | oi, quero devolver o notebook do pedido 10431 e trocar o outro item po | complexa | media | media | 2.75 / 5.00 / 4.75 |
| c0130 | vocês cobram IOF? pfv | simples | complexa | complexa | 3.75 / 4.25 / 4.75 |
| c0133 | dá pra receber o reembolso como crédito na loja? | simples | complexa | simples | 4.50 / 4.50 / 5.00 |
| c0132 | olá, uma dúvida: quando cai o reembolso do pedido 10452 obrigado | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0139 | boa tarde! quero devolver o camiseta do pedio 10430, ainda dá? | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0141 | boa tarde! dá pra cancelar o pedido 10430? obrigado pfv | media | simples | simples | 4.50 / 4.00 / 3.50 |
| c0154 | oi, paguei o pedido 10447 e aparece como não pago obrigado | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0150 | oi, o pedido 10420 tá atrasado? | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0157 | passou do prazo mas o smartwatch nunca funcionou direito, vocês têm qu | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0175 | preciso saber: três cobranças do pedido 10408 no meu cartão, vou abrir | complexa | simples | simples | 4.50 / 4.75 / 4.75 |
| c0182 | boa tarde! é a segunda troca do escova do pedido 10429 com defeito, qu | complexa | simples | simples | 4.50 / 4.75 / 4.75 |
| c0184 | olá, uma dúvida: devolvi só o mochila do pedido 10432, que tinha cupom | complexa | media | complexa | 3.25 / 4.25 / 4.50 |
| c0186 | oi, é a segunda troca do kit do pedido 10423 com defeito, quero meu di | complexa | simples | simples | 4.75 / 4.75 / 5.00 |
| c0188 | três cobranças do pedido 10418 no meu cartão, vou abrir chargeback e i | complexa | media | media | 4.25 / 4.75 / 4.75 |
| c0239 | preciso saber: alguém fez o pedido 10432 na minha conta, não fui eu é  | complexa | media | media | 3.50 / 4.75 / 4.75 |
| c0242 | boa tarde! qro devolver o smartwatch do pedido 10435 e trocar o outro  | complexa | media | media | 2.50 / 4.75 / 4.75 |
| c0238 | olá, uma dúvida: três cobranças do pedido 10456 no meu cartão, vou abr | complexa | media | media | 3.75 / 4.75 / 4.75 |
| c0246 | é a segunda troca do smartwatch do pedio 10453 com defeito, quero meu  | complexa | simples | simples | 4.75 / 4.75 / 4.25 |
| c0248 | boa tarde! devolvi só o liquidificador do pedido 10438, que tinha cupo | complexa | simples | complexa | 4.25 / 4.25 / 4.50 |
| c0401 | por favor, devolução vale pra loja física? obrigado | simples | complexa | complexa | 3.50 / 4.25 / 4.75 |
| c0407 | por favor, fui cobrado duas vezes no pedido 10417? é urgente | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0410 | oi, oi, o pedido 10417 consta entregue mas não recebi nada e já é a te | complexa | media | media | 3.25 / 4.75 / 4.50 |
| c0409 | cadê o pedido 10414??? | media | simples | media | 4.25 / 4.50 / 4.25 |
| c0411 | o notebook do pedio 10455 veio com defeito, como troco? | media | complexa | complexa | 3.50 / 3.25 / 4.75 |
| c0416 | olá, uma dúvida: o pedido 10430 já saiu pra entrega pfv | media | simples | simples | 5.00 / 5.00 / 4.75 |
| c0418 | boa tarde! como cadastro outro endereço? pfv | simples | media | media | 4.25 / 4.50 / 4.75 |
| c0428 | preciso saber: cadê o pedido 10428? | media | simples | simples | 4.75 / 4.75 / 4.25 |
| c0434 | boa tarde! quando cai o reembolso do pedido 10456? pfv | media | simples | simples | 5.00 / 5.00 / 4.75 |
| c0429 | o estorno do pedido 10458 já foi feito? obrigado pfv | media | simples | simples | 4.50 / 4.75 / 4.50 |
| c0440 | o notebook do pedido 10404 veio com defeito, como troco | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0441 | olá, uma dúvida: o pedio 10400 já saiu pra entrega? | media | simples | simples | 5.00 / 5.00 / 5.00 |
| c0446 | boa tarde! como gero a etiqueta de devolução valeu | simples | media | simples | 4.50 / 5.00 / 4.75 |
| c0447 | o frete da devolução é pago por mim? é urgente pfv | simples | media | simples | 4.50 / 4.75 / 5.00 |
| c0448 | boa tarde! quando cai o reembolso do pedido 10411? obrigado | media | simples | simples | 5.00 / 4.75 / 4.75 |
| c0449 | boa tarde! o pedido 10403 veio pela metade e o restante sumiu do rastr | complexa | simples | complexa | 4.00 / 2.50 / 4.25 |
| c0452 | oi, olá, uma dúvida: quando cai o reembolso do pedido 10419? pfv | media | simples | simples | 5.00 / 4.75 / 4.75 |
| c0455 | alguém fez o pedido 10405 na minha conta, não fui eu valeu | complexa | media | media | 3.25 / 4.75 / 4.75 |
| c0457 | dá pra receber o reembolso como crédito na loja? valeu | simples | complexa | simples | 4.50 / 4.50 / 5.00 |
| c0460 | preciso saber: dá pra cancelar o pedido 10457? pfv | media | simples | simples | 5.00 / 5.00 / 4.75 |
| c0468 | quero devolver o camiseta do pedido 10454 e trocar o outro item por um | complexa | media | media | 2.00 / 4.75 / 4.75 |
| c0471 | parcelei o pedido 10405, devolvi metade e a fatura continua cheia | complexa | media | media | 2.50 / 4.75 / 4.75 |
| c0472 | boa tarde! alguém fez o pedio 10431 na minha conta, não fui eu valeu | complexa | media | media | 4.25 / 4.75 / 4.50 |
| c0473 | olá, uma dúvida: o estorno do pedio 10425 já foi feito? é urgente | media | simples | simples | 4.75 / 4.75 / 4.50 |
| c0476 | olá, uma dúvida: dá pra cancelar o pedido 10432? | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0480 | preciso saber: quanto vou receber de volta do pedido 10407? valeu pfv | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0479 | boa tarde! o mochila parou de funcionar, tá na garantia? é urgente | media | simples | simples | 4.75 / 4.00 / 4.75 |
| c0483 | três cobranças do pedido 10423 no meu cartão, vou abrir chargeback e i | complexa | media | media | 2.00 / 4.75 / 4.75 |
| c0485 | devolução vale pra loja física? | simples | complexa | complexa | 3.50 / 3.50 / 4.75 |
| c0490 | oi, parcelei o pedido 10439, devolvi metade e a fatura continua cheia? | complexa | media | media | 1.50 / 4.75 / 4.75 |
| c0492 | preciso saber: fui cobrado duas vezes? | media | simples | simples | 4.75 / 5.00 / 4.75 |
| c0491 | boa tarde! o kit do pedido 10432 veio com defeito, como troco? pfv | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0494 | por favor, cadê o pedido 10410? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0495 | dá pra cancelar o pedido 10424? é urgente | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0496 | oi, olá, uma dúvida: fui cobrado duas vezes no pedido 10400? valeu | media | simples | simples | 5.00 / 4.75 / 4.75 |
| c0497 | preciso saber: três cobranças do pedido 10459 no meu cartão, vou abrir | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0501 | o escova do pedido 10443 veio com defeito, como troco? obrigado | media | simples | simples | 4.75 / 4.75 / 4.25 |
| c0507 | oi, o pedido 10429 já saiu pra entrega??? pfv | media | simples | simples | 5.00 / 5.00 / 4.75 |
| c0509 | oi, o liquidificador do pedio 10449 veio com defeito, como troco? pfv | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0516 | boa tarde! devolução vale pra loja física? | simples | complexa | complexa | 3.25 / 3.50 / 4.75 |
| c0522 | o estorno do pedio 10423 já foi feito? valeu | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0527 | olá, uma dúvida: alguém fez o pedido 10406 na minha conta, não fui eu | complexa | simples | simples | 4.50 / 4.25 / 4.50 |
| c0530 | oi, oi, quero devolver o liquidificador do pedido 10422, ainda dá? é u | media | simples | simples | 4.75 / 4.75 / 5.00 |
| c0531 | oi, boa tarde! veio o camiseta errado no pedido 10447 obrigado | media | simples | simples | 4.75 / 4.75 / 4.50 |
| c0534 | olá, uma dúvida: é a segunda troca do notebook do pedido 10413 com def | complexa | media | media | 3.75 / 4.50 / 4.75 |
| c0535 | preciso saber: quando cai o reembolso? pfv | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0538 | boa tarde! o meu pedido já saiu pra entrega? é urgente pfv | media | simples | simples | 4.50 / 4.00 / 4.75 |
| c0540 | oi, dá pra cancelar o pedido 10453 é urgente | media | complexa | complexa | 3.25 / 4.25 / 4.75 |
| c0542 | por favor, o estorno do pedido 10440 já foi feito valeu | media | simples | simples | 4.50 / 4.75 / 4.50 |
| c0543 | oi, o pedido 10440 consta entregue mas não recebi nada e já é a tercei | complexa | media | media | 4.00 / 4.50 / 4.75 |
| c0549 | preciso saber: o kit veio com defeito, como troco??? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0552 | o mochila do pedido 10421 veio com defeito, como troco? é urgente pfv | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0556 | preciso saber: dá pra retirar na loja obrigado | simples | media | simples | 4.50 / 5.00 / 4.75 |
| c0554 | oi, quanto vou receber de volta do pedido 10454? valeu pfv | media | simples | simples | 4.75 / 4.75 / 5.00 |
| c0559 | boa tarde! o caneca do pedido 10440 veio com defeito, como troco? vale | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0561 | por favor, qual o prazo pra devolver? | simples | media | simples | 4.50 / 4.75 / 5.00 |
| c0564 | oi, posso devolver sem a caixa original??? pfv | simples | media | media | 4.00 / 4.75 / 4.75 |
| c0566 | oi, dá pra cancelar o pedido 10449??? | media | simples | simples | 4.50 / 4.75 / 4.50 |
| c0568 | olá, uma dúvida: o frete da devolução é pago por mim? é urgente pfv | simples | complexa | simples | 4.50 / 4.50 / 5.00 |
| c0569 | cadê o pedido 10441? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0570 | olá, uma dúvida: dá pra devolver o tênis? é do pedido 10405?? | media | simples | simples | 4.75 / 4.75 / 5.00 |
| c0575 | posso devolver sem a caixa original? obrigado pfv | simples | complexa | complexa | 4.00 / 4.25 / 4.75 |
| c0580 | olá, uma dúvida: paguei o meu pedido e aparece como não pago pfv | media | complexa | complexa | 4.00 / 3.50 / 4.75 |
| c0581 | por favor, como excluo minha conta? valeu pfv | simples | media | complexa | 3.00 / 3.75 / 3.50 |
| c0583 | dá pra cancelar o pedio 10449? é urgente | media | simples | simples | 4.50 / 4.50 / 4.50 |
| c0586 | oi, cadê o pedido 10443? obrigado | media | simples | complexa | 4.00 / 4.25 / 4.25 |
| c0590 | oi, olá, uma dúvida: três cobranças do pedido 10434 no meu cartão, vou | complexa | media | media | 3.75 / 4.50 / 4.75 |
| c0592 | o estorno do pedido 10449 já foi feito? obrigado | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0596 | quanto vou receber de volta do pedio 10439? pfv | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0594 | olá, uma dúvida: três cobranças do pedido 10449 no meu cartão, vou abr | complexa | simples | simples | 4.50 / 3.50 / 4.75 |
| c0598 | quanto vou receber de volta do pedido 10449? valeu | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0600 | preciso saber: posso mudar o endereço? | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0624 | o pedido 10424 já saiu pra entrega??? pfv | media | simples | simples | 4.75 / 3.50 / 4.75 |
| c0625 | por favor, quando cai o reembolso do pedio 10412? é urgente | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0627 | no pedido 10456 usei cupom, um item veio com defeito e quero devolver  | complexa | media | media | 3.00 / 4.75 / 4.75 |
| c0630 | o caneca do pedido 10407 veio com defeito, como troco? é urgente | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0632 | por favor, parcelei o pedido 10423, devolvi metade e a fatura continua | complexa | media | media | 4.25 / 4.75 / 4.75 |
| c0636 | oi, boa tarde! o frete da devolução é pago por mim? pfv | simples | media | simples | 4.50 / 4.75 / 5.00 |
| c0643 | o estorno já foi feito? pfv | media | simples | simples | 4.50 / 4.75 / 4.50 |
| c0644 | olá, uma dúvida: quanto vou receber de volta do pedido 10433? | media | simples | simples | 4.75 / 4.75 / 5.00 |
| c0645 | preciso saber: o pedido 10420 já saiu pra entrega? pfv pfv | media | simples | simples | 4.75 / 5.00 / 4.75 |
| c0653 | é a segunda troca do escova do pedio 10403 com defeito, quero meu dinh | complexa | simples | simples | 4.75 / 4.25 / 5.00 |
| c0654 | oi, três cobranças do pedido 10409 no meu cartão, vou abrir chargeback | complexa | simples | simples | 4.50 / 4.50 / 4.75 |
| c0655 | posso mudar o endereço do pedido 10443? pfv | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0663 | preciso saber: dá pra cancelar o meu pedido? | media | complexa | complexa | 4.25 / 4.25 / 4.75 |
| c0669 | boa tarde! fui cobrado duas vezes? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0675 | oi, o estorno do pedido 10459 já foi feito? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0679 | o pedido 10440 consta entregue mas não recebi nada e já é a terceira v | complexa | simples | simples | 4.50 / 4.25 / 4.50 |
| c0680 | fui cobrado duas vezes no pedido 10413 pfv | media | simples | simples | 4.75 / 3.50 / 4.75 |
| c0685 | o estorno do pedido 10442 já foi feito? valeu | media | simples | simples | 4.75 / 5.00 / 4.75 |
| c0688 | preciso saber: no meu pedido usei cupom, um item veio com defeito e qu | complexa | media | media | 3.25 / 4.75 / 4.75 |
| c0689 | oi, fui cobrado duas vezes no pedido 10458 pfv | media | simples | simples | 5.00 / 4.75 / 4.75 |
| c0691 | o estorno já foi feito? pfv | media | simples | simples | 4.75 / 4.75 / 4.75 |
| c0698 | oi, fui cobrado duas vezes no pedido 10453? é urgente | media | simples | simples | 5.00 / 4.75 / 4.50 |
| c0697 | oi, o pedido 10454 tá atrasado? valeu | media | simples | simples | 4.50 / 4.75 / 4.75 |
| c0696 | o tênis do pedido 10425 veio com defeito, como troco? | media | simples | simples | 4.75 / 3.25 / 4.75 |
| c0702 | três cobranças no meu cartão, vou abrir chargeback e ir no procon se n | complexa | simples | simples | 4.50 / 4.50 / 4.75 |
| c0708 | passou do prazo mas o mochila do pedido 10410 nunca funcionou direito, | complexa | simples | complexa | 4.25 / 4.25 / 4.00 |
| c0736 | três cobranças do pedio 10448 no meu cartão, vou abrir chargeback e ir | complexa | simples | simples | 4.50 / 4.75 / 4.75 |
| c0751 | por favor, três cobranças do pedido 10430 no meu cartão, vou abrir cha | complexa | media | media | 3.25 / 4.75 / 4.75 |
| c0758 | oi, alguém fez o pedido 10435 na minha conta, não fui eu obrigado | complexa | simples | simples | 4.50 / 4.75 / 4.50 |
| c0762 | oi, quero devolver o liquidificador do pedido 10422 e trocar o outro i | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0765 | preciso saber: três cobranças do pedido 10443 no meu cartão, vou abrir | complexa | simples | simples | 4.50 / 4.50 / 4.75 |
| c0787 | preciso saber: devolvi só o liquidificador do pedido 10437, que tinha  | complexa | media | media | 3.25 / 4.75 / 4.75 |
| c0776 | por favor, o pedido 10458 veio pela metade e o restante sumiu do rastr | complexa | media | complexa | 2.25 / 4.25 / 4.50 |
| c0800 | o pedido 10447 veio pela metade e o restante sumiu do rastreio, e aind | complexa | simples | complexa | 4.25 / 3.25 / 4.50 |
| c0827 | olá, uma dúvida: o pedido 10416 consta entregue mas não recebi nada e  | complexa | simples | complexa | 4.25 / 3.50 / 4.50 |
| c0830 | por favor, o pedido 10439 veio pela metade e o restante sumiu do rastr | complexa | media | media | 2.75 / 4.50 / 4.50 |
| c0857 | olá, uma dúvida: três cobranças do pedido 10423 no meu cartão, vou abr | complexa | simples | simples | 4.50 / 4.75 / 4.75 |
| c0899 | parcelei o pedido 10415, devolvi metade e a fatura continua cheia | complexa | media | media | 2.75 / 4.75 / 4.75 |
| c0927 | olá, uma dúvida: três cobranças do pedido 10413 no meu cartão, vou abr | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0926 | passou do prazo mas o notebook do pedido 10446 nunca funcionou direito | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| c0938 | é a segunda troca do caneca do pedido 10445 com defeito, quero meu din | complexa | simples | simples | 4.75 / 4.75 / 5.00 |
| c0941 | preciso saber: o pedido 10414 veio pela metade e o restante sumiu do r | complexa | media | complexa | 2.50 / 4.25 / 4.50 |
| c0954 | oi, alguém fez o pedido 10438 na minha conta, não fui eu | complexa | simples | simples | 4.50 / 3.50 / 4.50 |
