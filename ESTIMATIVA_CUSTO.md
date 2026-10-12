# Estimativa de custo — POC modelos de decisão (Fase 1)

Gerado por `python -m harness.estimate`. Preços: `config/prices.json` (OpenRouter /api/v1/models, 2026-10-12 08:46 -03) + MSD1 de `config/prices_extra.json`.
Orçamento: **teto rígido US$20; o harness aborta ao atingir US$18** (`config/budget.json`). A chave também está com limite de US$20 no OpenRouter (GET /api/v1/key: `limit=20`).

## Preços ao vivo (US$ por 1M tokens)

| Papel | Modelo | Entrada | Saída |
|---|---|---|---|
| decisão (C1/C2) | `microsoft/microsoft-decision-1` | 0.042 | 0.000 |
| tier simples | `google/gemini-2.5-flash-lite` | 0.100 | 0.400 |
| tier média | `google/gemini-3.5-flash-lite` | 0.300 | 2.500 |
| tier complexa | `openai/gpt-6-sol` | 2.000 | 10.000 |
| juiz | `deepseek/deepseek-v4.1-flash` | 0.150 | 0.600 |

## Premissas

- Dataset: 130 mensagens; 108 chegam à geração (as 10 fora_de_escopo e 12 ambíguas param na resposta fixa; na prática o nº varia com a C1).
- Tiers rotulados: {'simples': 44, 'media': 38, 'complexa': 26}.
- Tokens por chamada (central ≈ smoke de 12/10/2026, arredondado para cima; pessimista ≈ teto de `max_tokens`):
  - **central**: geração 550 in / saída {'simples': 120, 'media': 160, 'complexa': 300} (GPT-6 Sol inclui tokens de raciocínio); C1 200 in; C2 150 in; juiz 900 in / 200 out.
  - **pessimista**: geração 900 in / saída {'simples': 400, 'media': 400, 'complexa': 400} (GPT-6 Sol inclui tokens de raciocínio); C1 300 in; C2 250 in; juiz 1400 in / 500 out.
- Medido no smoke: C1 ≈ 183–192 tokens, C2 ≈ 130–139 tokens (US$0,000006–0,000008 por decisão); geração ≈ 340–480 tokens in; saída Gemini 45–122, GPT-6 Sol 79–277 (39–187 de raciocínio).
- Mistura msd1 assumida 40% simples / 40% média / 20% complexa (fallback de baixa confiança sobe para complexa).
- Juiz avalia TODAS as respostas das 5 configurações (é barato); planilha de revisão humana cega numa amostra de 40.
- Cada mensagem é um turno único (sem conversas multi-turno nesta POC).

## Tabela

| Item | Central (US$) | Pessimista (US$) |
|---|---:|---:|
| MSD1 Camada 1 (130 msgs; reaproveitada nas estratégias) | 0.0011 | 0.0016 |
| MSD1 Camada 2 (msgs roteadas) | 0.0007 | 0.0011 |
| MSD1 calibração τ1/τ2 + 3 repetições de latência (4× C1+C2) | 0.0071 | 0.0111 |
| always-cheap (Gemini 2.5 Flash Lite) | 0.0111 | 0.0270 |
| always-media (Gemini 3.5 Flash Lite; p/ rótulo empírico de tier) | 0.0610 | 0.1372 |
| always-expensive (GPT-6 Sol) | 0.4428 | 0.6264 |
| msd1 (mistura 40/40/20) | 0.1174 | 0.1909 |
| oracle (tier do rótulo) | 0.1326 | 0.2101 |
| Juiz DeepSeek V4.1 Flash (todas as respostas: 5 configs) | 0.1377 | 0.2754 |
| Margem 50% (retries, re-rodadas) | 0.4558 | 0.7404 |
| **Total** | **1.37** | **2.22** |

## Por modelo (central, sem margem)

| Modelo | US$ |
|---|---:|
| `microsoft/microsoft-decision-1` | 0.0089 |
| `google/gemini-2.5-flash-lite` | 0.0201 |
| `google/gemini-3.5-flash-lite` | 0.1069 |
| `openai/gpt-6-sol` | 0.6380 |
| `deepseek/deepseek-v4.1-flash` | 0.1377 |

## Leitura

- Mesmo no cenário pessimista o experimento completo fica em ~US$2.22, bem abaixo da parada de US$18. Isso dá folga para: dobrar o dataset, rodar a variante de fallback "+1 tier", testar C1+C2 numa única chamada, e repetir a rodada.
- O item dominante é o GPT-6 Sol (always-expensive + parte de msd1/oracle). O MSD1 e o juiz custam centavos.
- Gasto já realizado na Fase 1 (smoke): ver `runs/ledger.json` e README.
- Conferir com o painel/fatura do OpenRouter depois da rodada (`Client.key_usage()`).
