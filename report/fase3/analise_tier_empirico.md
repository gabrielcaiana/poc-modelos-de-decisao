# Análise do tier empírico — dados da Fase 2 (holdout)

Neste arquivo eu investigo por que o rótulo de complexidade bate tão pouco com o tier que de fato foi necessário.

- Mensagens com resposta e nota nos 3 tiers: **52** (48 com rótulo de tier).
- Concordância rótulo × tier empírico **relativo** (≤0,25 da melhor nota): **47.9%**; × **absoluto** (média ≥4,5 e política ≥4): **45.8%**.
- Direção (relativo): {'igual': 23, 'empirico_mais_caro': 9, 'empirico_mais_barato': 16}. Direção (absoluto): {'igual': 22, 'empirico_mais_caro': 10, 'empirico_mais_barato': 16}.
- Nota média por tier: simples 4.18, media 4.60, complexa 4.71. O modelo barato já passa no critério absoluto em **63.5%** das mensagens; 0 mensagens não passam em nenhum tier.
- Distribuição — rótulo: {'simples': 18, 'media': 24, 'complexa': 6}; empírico relativo: {'simples': 33, 'complexa': 7, 'media': 12}; empírico absoluto: {'simples': 33, 'complexa': 9, 'media': 10}.

## Por presença de número de pedido (exige cruzar dados da ferramenta com a política)

| grupo | n | barato passa (absoluto) | rótulo = empírico | empírico mais caro que o rótulo | empírico mais barato que o rótulo |
|---|---:|---:|---:|---:|---:|
| com_pedido | 22 | 22.7% | 7/20 | 9 | 4 |
| sem_pedido | 30 | 93.3% | 16/28 | 0 | 12 |

## Matriz rótulo (linhas) × tier empírico relativo (colunas)

| rótulo | simples | media | complexa |
|---|---:|---:|---:|
| simples | 14 | 3 | 1 |
| media | 11 | 8 | 5 |
| complexa | 4 | 1 | 1 |

## Matriz rótulo × tier empírico absoluto

| rótulo | simples | media | complexa |
|---|---:|---:|---:|
| simples | 14 | 3 | 1 |
| media | 12 | 6 | 6 |
| complexa | 3 | 1 | 2 |

## Discordâncias (rótulo ≠ empírico relativo)

| id | mensagem | rótulo | relativo | absoluto | notas simples/media/complexa |
|---|---|---|---|---|---|
| m241 | pedido 10437 veio faltando a tampa do liquidificador, troca só a peça  | media | complexa | complexa | 3.50 / 3.50 / 4.50 |
| m242 | fui cobrado por um pedido que não fiz | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| m245 | i want to return my order 10417, wrong color | simples | media | media | 4.25 / 4.75 / 4.75 |
| m248 | o código de postagem da devolução expirou | media | simples | simples | 4.50 / 4.75 / 4.75 |
| m249 | fui cobrado duas vezes no pedido 10405 | media | simples | simples | 4.75 / 5.00 / 5.00 |
| m250 | veio a camiseta no tamanho P e eu pedi M, pedido 10408, como troco? | media | complexa | complexa | 2.50 / 4.00 / 4.75 |
| m251 | comprei 3 itens com cupom no pedido 10412, um veio com defeito e quero | complexa | media | media | 2.50 / 4.75 / 4.75 |
| m255 | parcelei em 10x e devolvi, as parcelas param? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| m258 | posso pedir reembolso do pedido cancelado 10435? | simples | complexa | complexa | 3.25 / 4.00 / 4.75 |
| m262 | quero cancelar o pedido 10456, já foi enviado? | media | complexa | complexa | 3.75 / 4.25 / 4.75 |
| m264 | meu cartão foi cancelado, como recebo o estorno? | media | simples | simples | 4.50 / 4.75 / 4.75 |
| m266 | o reembolso caiu mas faltou o valor do frete | media | simples | simples | 4.50 / 4.50 / 4.75 |
| m270 | minha conta foi invadida e fizeram um pedido no meu nome | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| m271 | produto chegou molhado, pedido 10425 | media | complexa | complexa | 3.50 / 3.25 / 4.75 |
| m276 | quero devolver o tênis do pedido 10411, não serviu | simples | media | media | 2.75 / 4.75 / 4.75 |
| m277 | tracking number for order 10454? | simples | media | media | 2.50 / 4.50 / 4.25 |
| m278 | o boleto foi pago em duplicidade | media | simples | simples | 4.75 / 4.75 / 5.00 |
| m287 | chegou o produto de outra pessoa no pedido 10439 | media | complexa | complexa | 2.50 / 4.00 / 4.75 |
| m289 | recebi o pedido 10441 faz 8 dias e quero devolver por arrependimento,  | complexa | simples | simples | 4.75 / 4.75 / 4.75 |
| m290 | o valor do reembolso tá errado | media | simples | simples | 4.75 / 4.75 / 4.75 |
| m293 | o produto quebrou na primeira semana, troca? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| m294 | comprei de presente, a pessoa quer trocar sem me dizer o valor | media | simples | simples | 4.75 / 4.75 / 4.75 |
| m297 | o pedido 10419 diz entregue em outra cidade | complexa | simples | complexa | 4.25 / 4.25 / 4.50 |
| m298 | abri a escova elétrica e não gostei, devolvo? | media | simples | simples | 4.75 / 4.75 / 4.75 |
| m299 | me mandaram 2 unidades em vez de 1, devolvo a extra? | media | simples | simples | 4.50 / 4.75 / 4.75 |
