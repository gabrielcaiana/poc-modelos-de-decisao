# Estimativa de custo — Fase 3

Preços ao vivo do OpenRouter (`/api/v1/models`, 2026-10-12 09:49 -03); MSD1 em `config/prices_extra.json`. Gerado por `python3 -m harness.fase3.estimate`.

## Orçamento

- Teto rígido: US$20. Parada automática do harness: US$18 (`config/budget.json`, ledger acumulado).
- Já gasto (ledger, Fases 1–2 + smoke da Fase 3): **US$0.3150**. Disponível até a parada: **US$17.68**.
- Meta que eu me impus: cenário pessimista < US$8. Vou rodar com `--session-cap 8`.

## Preços (US$ por 1M tokens)

| Papel | Modelo | Entrada | Saída |
|---|---|---:|---:|
| decisão | `microsoft/microsoft-decision-1` | 0.042 | 0.000 |
| simples | `google/gemini-2.5-flash-lite` | 0.100 | 0.400 |
| média | `google/gemini-3.5-flash-lite` | 0.300 | 2.500 |
| complexa | `openai/gpt-6-sol` | 2.000 | 10.000 |
| juiz | `deepseek/deepseek-v4.1-flash` | 0.150 | 0.600 |

## Desenho que estou orçando

- 1000 conversas fictícias; decisões MSD1 (C1 + 3 variantes de C2) em todas as 960 roteáveis.
- Geração nos 3 tiers + juiz em cada resposta, só nas 450 conversas marcadas `gerar` (150 calib + 300 teste, cauda complexa sobreamostrada).
- Toda política (always-*, msd1 em qualquer τ/variante, oracles) é avaliada por replay, sem novas chamadas.
- max_tokens: 400 (Gemini) e 800 (GPT-6 Sol).

## Premissas de tokens

- **central**: C1 300 in; C2 {'v1_score': 220, 'v2_ctx': 380, 'v3_noul': 390}; geração 550 in / saída {'simples': 100, 'media': 140, 'complexa': 220}; juiz 1000 in / 150 out; margem 20%.
- **pessimista**: C1 450 in; C2 {'v1_score': 330, 'v2_ctx': 600, 'v3_noul': 620}; geração 900 in / saída {'simples': 400, 'media': 400, 'complexa': 800}; juiz 1600 in / 500 out; margem 30%.
- Medido no smoke (6 conversas, `runs/fase3-smoke-20261012`): simples: 479 in / 86 out (máx 155) → US$0.000082; media: 479 in / 109 out (máx 136) → US$0.000417; complexa: 463 in / 168 out (máx 246) → US$0.002605; juiz US$0.000144/avaliação; C2 in: v1_score 197, v2_ctx 337, v3_noul 344. Custo do smoke: US$0.0179.

## Tabela

| Item | Central (US$) | Pessimista (US$) |
|---|---:|---:|
| MSD1 Camada 1 (todas as conversas) | 0.0126 | 0.0189 |
| MSD1 Camada 2 — 3 variantes (todas as roteáveis) | 0.0399 | 0.0625 |
| Geração Gemini 2.5 Flash Lite (450 conversas) | 0.0427 | 0.1125 |
| Geração Gemini 3.5 Flash Lite (450 conversas) | 0.2318 | 0.5715 |
| Geração GPT-6 Sol (450 conversas) | 1.4850 | 4.4100 |
| Juiz DeepSeek V4.1 Flash (1350 avaliações) | 0.3240 | 0.7290 |
| Margem (central 20%, pessimista 30%): retries, 429/5xx, re-execuções | 0.4272 | 1.7713 |
| **Total** | **2.56** | **7.68** |

Gasto projetado acumulado (já gasto + Fase 3): central **US$2.88**, pessimista **US$7.99** — abaixo da parada de US$18.

## Minha leitura

- O GPT-6 Sol responde por 70% do custo central (sem margem); o pessimista assume que toda resposta dele usa as 800 saídas (no smoke, a maior teve 246).
- As decisões MSD1 custam centavos mesmo com 3 variantes em 1000 conversas: dá para varrer τ e variantes à vontade no replay.
- Se o gasto real do primeiro lote (calib) vier acima do central, eu reduzo o teste de 300 para 200 conversas antes de continuar.
