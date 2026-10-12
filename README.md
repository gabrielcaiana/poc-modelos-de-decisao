# POC — Modelos de decisão num chatbot de pós-venda (Fase 1)

POC derivada de `/workspace/artigos/modelos-de-decisao/plano-experimento.md` (v2), com os ajustes do Gabriel de 12/10/2026:
orçamento rígido de **US$20** no OpenRouter (parada automática em **US$18**), escopo **pós-venda** com 3 subagentes e dataset pequeno (130 mensagens fictícias).

**Status: Fase 1 concluída (código, dataset, harness, testes, dry-run com mocks, smoke test). A rodada completa NÃO foi executada.**

## Arquitetura

```
mensagem ──► Camada 1: MSD1 (choice) ─► p_max < τ1 ─► clarificação (texto fixo, custo zero)
                     │                 └► fora_de_escopo ─► resposta padrão
                     ▼ devolucao | suporte | financeiro
             Camada 2: MSD1 (score 0-2) ─► simples → google/gemini-2.5-flash-lite
                                         ├► media   → google/gemini-3.5-flash-lite
                                         ├► complexa→ openai/gpt-6-sol
                                         └► p_max < τ2 → complexa (ou "+1 tier", configurável)
             Geração no subagente com ferramentas mock (resultado injetado no prompt)
```

| Subagente | Cobre |
|---|---|
| `devolucao` | devolução, troca, arrependimento, defeito, etiqueta/coleta |
| `suporte` | status/rastreio, entrega, endereço, cancelamento antes do envio, conta, uso do produto |
| `financeiro` | reembolso, cobrança (duplicada/indevida/juros/boleto), estorno |

### Microsoft-Decision-1 (MSD1)
Existe e foi usado **sem substituto**: `microsoft/microsoft-decision-1` (versão retornada `microsoft-decision-1-20261009`, provedor Azure), lançado em 09/10/2026, pós-treino do Qwen3.5-9B que devolve **probabilidade calibrada por opção** (não gera texto). Endpoint do OpenRouter: `POST https://openrouter.ai/api/alpha/decisions` (API *alpha*; não é chat completions), corpo `{model, state, questions:{nome:{type: choice|score|noul, instructions, criteria}}}`. Preço: US$0,042/M tokens de entrada, saída grátis; contexto 32k. Ele **não aparece** em `/api/v1/models`, por isso o preço fica em `config/prices_extra.json`; o custo real de cada chamada vem de `usage.cost`.
- C1 usa `type: choice` (4 opções). C2 usa `type: score` (escala ordinal 0/1/2 = simples/média/complexa).
- Fontes: https://openrouter.ai/microsoft/microsoft-decision-1 · https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request · https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-microsoft-decision

### Modelos (verificados em `/api/v1/models` em 12/10/2026)
| Papel | Modelo | US$/1M in / out |
|---|---|---|
| decisão | `microsoft/microsoft-decision-1` | 0,042 / 0 |
| barato | `google/gemini-2.5-flash-lite` | 0,10 / 0,40 |
| médio | `google/gemini-3.5-flash-lite` | 0,30 / 2,50 |
| caro | `openai/gpt-6-sol` | 2,00 / 10,00 |
| juiz | `deepseek/deepseek-v4.1-flash` | 0,15 / 0,60 |

Os três do plano existem com os preços do plano; nenhuma substituição. O juiz é de outra família (evita auto-preferência) e barato. Obs.: existe também `openai/gpt-6.1-sol` (mesmo preço); mantivemos o `gpt-6-sol` do plano.

### Estratégias
`msd1` (C1+C2), `always-cheap`, `always-expensive` (baselines pedidos), `always-media` (necessária para rotular o tier mínimo empiricamente) e `oracle` (label humano, teto teórico). A C1 é idêntica em todas e é reaproveitada via cache dentro da execução (é paga uma vez; o custo é contabilizado em cada estratégia, como seria em produção; linhas reaproveitadas têm `reuso_cache: true`).

## Orçamento e segurança
- `harness/budget.py`: ledger persistente em `runs/ledger.json`. Antes de **cada** chamada reserva o custo máximo possível (tokens estimados × preço + `max_tokens` × preço de saída); se `gasto + reserva > 18`, levanta `BudgetExceeded` e a execução para, gravando `status: ABORTADO_ORCAMENTO` no `manifest.json`. `--session-cap` adiciona um teto por execução.
- Custo real por chamada: `usage.cost` do OpenRouter (fallback: tabela de preços). Conferência: `Client.key_usage()` (GET `/api/v1/key`). A chave já tem `limit = 20` no OpenRouter.
- A chave vem só de `OPENROUTER_API_KEY`; nunca é impressa/logada. `.env` está no `.gitignore`; use `.env.example`.
- Dados 100% fictícios (`mocks/dados.py`, loja "LojaExemplo").

## Como rodar
Requer só Python 3.11+ (stdlib; sem dependências).
```bash
python3 -m unittest -v tests.test_poc                       # testes (mock, custo zero)
python3 datasets/gerar_dataset.py                           # regenera o dataset (determinístico)
python3 -m harness.run --mock --estrategias msd1,always-cheap,always-media,always-expensive,oracle   # dry-run
python3 -m harness.judge runs/<dir> --mock --amostra 40     # juiz + planilha cega de revisão humana
python3 -m harness.metrics runs/<dir>                       # métricas -> runs/<dir>/report.md
python3 -m harness.estimate --refresh                       # atualiza preços e ESTIMATIVA_CUSTO.md
# LIVE (só com autorização): troque --mock por --live; use --split calib|valid|holdout e --session-cap
```

## Estrutura
```
config/   models.json, prices.json (datado), prices_extra.json (MSD1), thresholds.json (τ1=0,6 / τ2=0,5 provisórios), budget.json
datasets/ gerar_dataset.py, mensagens.jsonl (130: 36 devolução, 36 suporte, 36 financeiro, 10 fora, 12 ambíguas; split 78/26/26)
mocks/    dados.py (60 pedidos fictícios, política, ferramenta status_pedido)
harness/  budget.py, client.py (OpenRouter + mocks), pipeline.py, run.py, judge.py, metrics.py, estimate.py
tests/    test_poc.py (10 testes)
report/   revisao_rotulos.csv (planilha p/ revisão humana dos rótulos)
runs/     smoke-20261012/ (evidência do smoke real); ledger.json (gitignored)
```

## Smoke test (12/10/2026, ~08:50 PT/BRT)
4 mensagens (`m000, m002, m006, m008`) × 3 estratégias + juiz em 2 mensagens × 3 estratégias = 27 chamadas.
**Gasto: US$0,0120** (ledger local; o OpenRouter reportou US$0,0086 antes do juiz). Tudo funcionou: C1 acertou as 4 com p_max ≥ 0,999; C2 deu média/simples/simples/média (rótulos: média/simples/simples/complexa); latência de decisão ~220–500 ms; geração 0,7–1,9 s (Gemini) e 2,4–4,5 s (GPT-6 Sol).
Problemas encontrados e corrigidos: (1) juiz DeepSeek devolvia `content: null` (raciocínio consumia o `max_tokens`) → raciocínio desligado + `response_format: json_object`; (2) mock gerava pedido "cancelado" com dias desde a entrega → corrigido; (3) o juiz recalculava o contexto das ferramentas → agora o contexto usado na geração é salvo em `turns.jsonl` e reutilizado. Por isso as notas do juiz em `runs/smoke-20261012/judge.jsonl` foram dadas contra um contexto diferente do da geração e **não valem como resultado**.

## Desvios em relação ao plano v2
- Escopo pós-venda (devolução/suporte/financeiro) em vez de catálogo/carrinho/pós-venda.
- 130 mensagens de turno único em vez de 500+300+150 conversas multi-turno.
- Ferramentas mock injetadas no prompt (sem loop de tool-calling) para reduzir custo/complexidade.
- Python stdlib em vez de TypeScript/Node.
- Sem `llm-router`, Jev, OpenAI Decisions e Cloudflare auto (opcionais; cabem no orçamento se o Gabriel quiser).
- Rótulos feitos pelo bot (provisórios), precisam de revisão humana.

---
## Fase 2 (12/10/2026) — executada
- Dataset ampliado para **300** mensagens (84 por subagente, 24 fora de escopo, 24 ambíguas; split 180/60/60). `datasets/extra_v2.py` + `report/revisao_rotulos.csv` atualizado.
- GPT-6 Sol com `max_tokens=800` (Gemini 400); truncamento registrado por turno (`finish`): 0% em todos os modelos.
- Estimativa refeita antes de rodar (`ESTIMATIVA_CUSTO.md`: central US$0,73 / pessimista US$1,68 < limite de US$6).
- `harness/calibrate.py`: τ1/τ2 escolhidos no split calib e congelados em `config/thresholds.json` (τ1=0,9; τ2=0,5; τ2_up1=0,98).
- Holdout com 6 estratégias (msd1, msd1-up1, always-cheap, always-media, always-expensive, oracle), juiz em todas as respostas, planilha cega de 40 itens.
- Relatório: **`RESULTADOS.md`** (gerado por `.venv/bin/python -m harness.report runs/20261012-holdout-live runs/20261012-085619-calib-live`; precisa de `matplotlib` num venv: `python3 -m venv .venv && .venv/bin/pip install matplotlib`).
