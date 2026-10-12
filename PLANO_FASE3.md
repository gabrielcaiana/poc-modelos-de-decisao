# Plano da Fase 3 — a Camada 2 perdeu para always-media por causa do teste pequeno?

**Status: preparação concluída; a rodada completa ainda NÃO foi executada.** Só rodei um smoke test de 6 conversas (US$0,018).

## Pergunta

Na Fase 2, o msd1 (MSD1 escolhendo entre 3 modelos) ficou dominado por always-media: custou mais e teve nota menor (4,48 vs 4,60). O teste tinha só 60 mensagens de turno único. Quero saber se isso se mantém com:

1. um conjunto muito maior;
2. uma distribuição de complexidade realista (maioria simples, cauda longa de casos difíceis);
3. conversas multi-turno com contexto de pedido;
4. estatística pareada de verdade;
5. uma Camada 2 melhor desenhada, ajustada só no split de calibração.

## O que a Fase 2 já me mostrou (sem gastar nada)

Rodei `python3 -m harness.fase3.tier_empirico fase2 runs/20261012-holdout-live` sobre os logs da Fase 2 (resultado em [`report/fase3/analise_tier_empirico.md`](report/fase3/analise_tier_empirico.md)):

| grupo | n | barato passa | rótulo = empírico | empírico mais caro que o rótulo | empírico mais barato que o rótulo |
|---|---:|---:|---:|---:|---:|
| mensagem **com** nº de pedido | 22 | 22,7% | 7/20 | 9 | 4 |
| mensagem **sem** nº de pedido | 30 | 93,3% | 16/28 | 0 | 12 |

O rótulo de complexidade media o quanto o pedido **parece** grave ("fui cobrado por um pedido que não fiz" = complexa). Mas o que derruba o modelo barato é ter que **cruzar os dados do pedido com a política** (status, dias desde a entrega, itens, categoria). Sem nº de pedido, o modelo barato passa em 93% dos casos. Além disso, na Fase 2 o MSD1 decidia a complexidade **sem ver o resultado da ferramenta**. Daí vêm as variantes v2 e v3 abaixo.

Definição do tier empírico mínimo (a mesma mensagem respondida pelos 3 modelos e avaliada pelo juiz):

- **relativo**: o tier mais barato cuja nota fica a ≤ 0,25 da melhor das três;
- **absoluto**: o tier mais barato com média ≥ 4,5 e nota de política ≥ 4; se nenhum passa, vale complexa.

## Desenho

### Dataset (`datasets/fase3/gerar_conversas.py` → `conversas.jsonl`)

| | |
|---|---|
| Tamanho | **1000 conversas** fictícias, sem duplicatas exatas (mensagem + histórico) |
| Subagente | devolução 290 · suporte 331 · financeiro 279 · fora de escopo 40 (4%) · ambíguas 60 (6%) |
| Complexidade (regra) | simples 525 (58%) · média 265 (29%) · complexa 110 (12%) entre as roteáveis |
| Multi-turno | 0 turnos anteriores: 354 · 1: 359 · 2: 183 · 3: 104; em 79 conversas o nº do pedido aparece **só no histórico** |
| Split | calibração 400 · teste 600 |
| Subconjunto com geração | 450 (calib 150 + teste 300), estratificado e com a **cauda complexa sobreamostrada** (calib 70/40/30, teste 140/80/60, mais 10/20 ambíguas ou fora de escopo); cada item tem `peso` para que as médias reflitam a distribuição realista |

As conversas foram geradas por templates combinatórios (seed fixa), escritos com apoio de um LLM. O tier é **derivado por regra** a partir de atributos explícitos de cada cenário (precisa de pedido, vários problemas, exceção de política, cálculo de valor, risco, cliente irritado). Os rótulos foram gerados com apoio de um LLM e ainda não passaram por revisão humana.

### Coleta em grade + replay (o que torna 1000 conversas baratas)

Em vez de rodar cada estratégia separadamente, `harness/fase3/run_grid.py` faz, por conversa:

1. **C1** (MSD1 `choice`, com histórico): uma vez.
2. **C2 nas 3 variantes**: só as probabilidades cruas, em todas as 960 conversas roteáveis.
3. Nas 450 marcadas `gerar`: **resposta nos 3 tiers** com o subagente escolhido pela C1, mais **juiz em cada resposta**.

Depois, `harness/fase3/replay.py` avalia qualquer política sem novas chamadas: always-cheap/media/expensive, msd1 com qualquer τ ou variante, oracle pela regra e oracle pelo tier empírico. Como todas as estratégias usam **as mesmas mensagens e as mesmas respostas**, a comparação é perfeitamente pareada. A coleta é **retomável**: ao relançar, nada que já está em `grid.jsonl` é pago de novo.

### Variantes da Camada 2 (`harness/fase3/variantes.py`)

| variante | pergunta ao MSD1 | contexto da ferramenta no estado |
|---|---|---|
| `v1_score` | a da Fase 2 (score 0–2 por "gravidade") | não |
| `v2_ctx` | score 0–2 focado em **cruzar dados do pedido com a política** | sim |
| `v3_noul` | duas perguntas sim/não na mesma chamada: "o modelo simples basta?" e "precisa do modelo forte?" | sim |

Grades varridas no replay: τ2 ∈ {0; 0,4; 0,5; 0,6; 0,7; 0,8; 0,9; 0,95; 0,98} × fallback {complexa, +1 tier} para v1/v2, e ta × tb ∈ {0,3…0,9}² para v3.

**Critério de ajuste (pré-registrado, só no calib):** entre os parâmetros cuja nota média ponderada no calib ≥ nota(always-media) − 0,05, escolho o de **menor custo**; se nenhum atingir, o de maior nota. Congelo antes de olhar o teste.

### Estatística no teste

- Médias ponderadas pelo `peso`; IC95% por **bootstrap pareado** (5000 reamostragens) para Δnota e Δcusto.
- **Teste de permutação** por troca de sinal (Δnota pareado) e **McNemar** na taxa de "passa".
- **Correção de Holm** nas 6 comparações principais (cada variante msd1 vs always-media e vs always-expensive).
- Quebra por tier da regra, acerto da C2 vs regra (em todas as conversas roteadas) e sub-roteamento vs tier empírico.

## Como vou rodar (quando autorizar)

```bash
python3 -m harness.fase3.estimate --refresh                                       # reconfere preços
python3 -m harness.fase3.run_grid --live --split calib --session-cap 3 --out runs/fase3-grid
# confiro o gasto real do calib contra o central; se ok:
python3 -m harness.fase3.run_grid --live --split teste --session-cap 5 --out runs/fase3-grid
python3 -m harness.fase3.replay runs/fase3-grid --out report/fase3
python3 -m harness.fase3.tier_empirico ...                                         # análise do tier na Fase 3
```

## Custo

Veja [`ESTIMATIVA_CUSTO_FASE3.md`](ESTIMATIVA_CUSTO_FASE3.md): **central US$2,56, pessimista US$7,68**. Com os US$0,32 já gastos, o acumulado fica em no máximo ~US$8, abaixo da parada de US$18.

## Riscos

- **Dataset por templates**: mais fácil e homogêneo que conversas reais. A C1 pode parecer melhor do que seria em produção, e a C2 pode aprender o "estilo" do template.
- **Rótulos por regra, sem revisão humana**; o tier empírico depende de um único juiz barato, ainda não calibrado contra notas humanas.
- **Juiz com teto**: na Fase 2 muitas notas saturaram em 4,75. Se isso se repetir, as diferenças entre estratégias ficam comprimidas.
- **Replay assume que a resposta de um tier independe da estratégia**. Vale aqui porque a geração depende só de (mensagem, subagente, tier), mas cada resposta é uma amostra única (temperatura 0,2).
- **C1 usa τ1 = 0,9, calibrado na Fase 2**. No smoke, "qual o telefone do atendimento?" foi para fora_de_escopo com p = 0,923. Posso recalibrar o τ1 no calib da Fase 3 offline (os registros de C1 já ficam no grid).
- **Sobreamostragem da cauda**: os pesos corrigem as médias, mas a variância das estimativas ponderadas aumenta.
- **Preço e versão do MSD1 podem mudar** (API alpha, modelo lançado em 09/10/2026). Registro versão e preço em cada manifest.
