# Estimativa de custo — POC modelos de decisão (Fase 2)

Gerado por `python -m harness.estimate`. Preços: `config/prices.json` (OpenRouter /api/v1/models, 2026-10-12 08:57 -03) + MSD1 de `config/prices_extra.json`.
Orçamento: **teto rígido US$20; o harness aborta ao atingir US$18** (`config/budget.json`). Também configurei o limite de US$20 na própria chave do OpenRouter (GET /api/v1/key: `limit=20`).

## Preços ao vivo (US$ por 1M tokens)

| Papel | Modelo | Entrada | Saída |
|---|---|---|---|
| decisão (C1/C2) | `microsoft/microsoft-decision-1` | 0.042 | 0.000 |
| tier simples | `google/gemini-2.5-flash-lite` | 0.100 | 0.400 |
| tier média | `google/gemini-3.5-flash-lite` | 0.300 | 2.500 |
| tier complexa | `openai/gpt-6-sol` | 2.000 | 10.000 |
| juiz | `deepseek/deepseek-v4.1-flash` | 0.150 | 0.600 |

## Premissas que usei

- Dataset: 300 mensagens; decisões MSD1 em todas; geração só no holdout (60 msgs, 52 chegam à geração; fora_de_escopo/ambíguas param na resposta fixa).
- max_tokens: 400 (Gemini) e 800 (GPT-6 Sol, v2).
- Tiers rotulados: {'simples': 21, 'media': 25, 'complexa': 6}.
- Tokens por chamada (central ≈ smoke de 12/10/2026, arredondado para cima; pessimista ≈ teto de `max_tokens` (Sol 800)):
  - **central**: geração 550 in / saída {'simples': 120, 'media': 160, 'complexa': 300} (GPT-6 Sol inclui tokens de raciocínio); C1 200 in; C2 150 in; juiz 900 in / 200 out.
  - **pessimista**: geração 900 in / saída {'simples': 400, 'media': 400, 'complexa': 800} (GPT-6 Sol inclui tokens de raciocínio); C1 300 in; C2 250 in; juiz 1400 in / 500 out.
- O que medi no smoke: C1 ≈ 183–192 tokens, C2 ≈ 130–139 tokens (US$0,000006–0,000008 por decisão); geração ≈ 340–480 tokens in; saída Gemini 45–122, GPT-6 Sol 79–277 (39–187 de raciocínio).
- Assumi para msd1 a mistura 40% simples / 40% média / 20% complexa (fallback de baixa confiança sobe para complexa).
- O juiz avalia TODAS as respostas das 6 configurações (é barato); eu reviso manualmente uma amostra cega de 40.
- Cada mensagem é um turno único (sem conversas multi-turno nesta POC).

## Tabela

| Item | Central (US$) | Pessimista (US$) |
|---|---:|---:|
| MSD1 Camada 1 (holdout; reaproveitada nas estratégias) | 0.0005 | 0.0008 |
| MSD1 Camada 2 (msgs roteadas) | 0.0003 | 0.0005 |
| MSD1 calibração τ1/τ2 em todos os splits (C1+C2) + 3 repetições de latência | 0.0067 | 0.0104 |
| always-cheap (Gemini 2.5 Flash Lite) | 0.0054 | 0.0130 |
| always-media (Gemini 3.5 Flash Lite; p/ rótulo empírico de tier) | 0.0294 | 0.0660 |
| always-expensive (GPT-6 Sol) | 0.2132 | 0.5096 |
| msd1 (mistura 40/40/20) | 0.0565 | 0.1335 |
| msd1-up1 (variante fallback +1 tier; ~ msd1) | 0.0565 | 0.1335 |
| oracle (tier do rótulo) | 0.0409 | 0.0958 |
| Juiz DeepSeek V4.1 Flash (todas as respostas: 6 configs) | 0.0796 | 0.1591 |
| Margem 50% (retries, re-rodadas) | 0.2445 | 0.5612 |
| **Total** | **0.73** | **1.68** |

## Por modelo (central, sem margem)

| Modelo | US$ |
|---|---:|
| `microsoft/microsoft-decision-1` | 0.0075 |
| `google/gemini-2.5-flash-lite` | 0.0118 |
| `google/gemini-3.5-flash-lite` | 0.0670 |
| `openai/gpt-6-sol` | 0.3231 |
| `deepseek/deepseek-v4.1-flash` | 0.0796 |

## Minha leitura

- Mesmo no cenário pessimista o experimento completo fica em ~US$1.68, bem abaixo da parada de US$18. Isso dá folga para: dobrar o dataset, rodar a variante de fallback "+1 tier", testar C1+C2 numa única chamada, e repetir a rodada.
- O item dominante é o GPT-6 Sol (always-expensive + parte de msd1/oracle). O MSD1 e o juiz custam centavos.
- O gasto real que tive está em `runs/ledger.json` e no README.
- Depois da rodada eu confiro com o painel do OpenRouter (`Client.key_usage()`).
