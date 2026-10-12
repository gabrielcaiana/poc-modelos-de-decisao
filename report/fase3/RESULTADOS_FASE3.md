# Resultados da Fase 3 (replay)

Grid: `runs/fase3-grid` · itens avaliáveis: calib 140, teste 265 · τ1=0.8. Médias ponderadas pelo peso de amostragem.

## Camada 1 — τ1

| configuração | split | acurácia (claras) | clarificação | clarif. desnecessária | erro entre aceitas | ambíguas ok | utilidade |
|---|---|---:|---:|---:|---:|---:|---:|
| τ1=0.9 (Fase 2) | calib | 94.7% | 5.5% | 4.5% | 4.2% | 86.4% | 0.850 |
| τ1=0.9 (Fase 2) | teste | 94.1% | 5.2% | 3.7% | 4.6% | 89.5% | 0.848 |
| τ1=0.8 (reajustado no calib Fase 3) | calib | 94.7% | 2.8% | 2.1% | 4.3% | 77.3% | 0.858 |
| τ1=0.8 (reajustado no calib Fase 3) | teste | 94.1% | 2.8% | 2.1% | 4.7% | 81.6% | 0.848 |
| τ1=0.0 (sem threshold) | calib | 94.7% | 0.0% | 0.0% | 5.3% | 68.2% | 0.846 |
| τ1=0.0 (sem threshold) | teste | 94.1% | 0.0% | 0.0% | 5.9% | 81.6% | 0.841 |

## Parâmetros da Camada 2 escolhidos no calib

| variante | parâmetros | atinge critério | nota calib | US$/msg calib |
|---|---|---|---:|---:|
| v1_score | `{'tau': 0.0, 'fallback': 'complexa'}` | True | 4.542 | 0.000458 |
| v2_ctx | `{'tau': 0.8, 'fallback': '+1'}` | True | 4.531 | 0.000543 |
| v3_noul | `{'ta': 0.7, 'tb': 0.3}` | True | 4.528 | 0.000438 |

Referência no calib — always-media: nota 4.566, US$0.000349/msg.

## Teste

| estratégia | nota | % passa | US$/msg | sub-roteamento vs empírico | lat P50/P95 (s) | simples/media/complexa |
|---|---:|---:|---:|---:|---:|---|
| always-cheap | 4.457 | 79.8% | 0.000072 | 22.7% | 0.94/1.77 | 265/0/0 |
| always-media | 4.588 | 85.9% | 0.000335 | 8.0% | 1.33/1.92 | 0/265/0 |
| always-expensive | 4.652 | 89.2% | 0.002238 | 0.0% | 3.50/5.63 | 0/0/265 |
| oracle-regra | 4.650 | 91.8% | 0.000540 | 7.8% | 1.29/5.31 | 123/85/57 |
| oracle-empirico | 4.706 | 96.7% | 0.000345 | 0.0% | 1.02/4.47 | 191/45/29 |
| msd1-v1_score | 4.614 | 88.5% | 0.000427 | 12.2% | 1.40/5.04 | 160/61/44 |
| msd1-v2_ctx | 4.629 | 88.7% | 0.000512 | 11.5% | 1.47/4.98 | 149/64/52 |
| msd1-v3_noul | 4.605 | 87.2% | 0.000401 | 12.3% | 1.41/4.82 | 158/66/41 |

## Comparações pareadas (teste)

| comparação | Δ nota (IC95%) | p perm. | p Holm | Δ US$/msg (IC95%) | McNemar p (passa) | McNemar p Holm | passa só A / só B |
|---|---:|---:|---:|---:|---:|---:|---:|
| msd1-v1_score vs always-media | +0.026 (-0.018; +0.075) | 0.2801 | 0.8404 | +0.000092 (+0.000016; +0.000173) | 0.0113 | 0.0567 | 26 / 10 |
| msd1-v1_score vs always-expensive | -0.038 (-0.091; +0.013) | 0.1570 | 0.6279 | -0.001811 (-0.001903; -0.001718) | 0.4614 | 0.9228 | 20 / 26 |
| msd1-v2_ctx vs always-media | +0.041 (-0.004; +0.091) | 0.0846 | 0.5075 | +0.000177 (+0.000090; +0.000270) | 0.0090 | 0.0542 | 25 / 9 |
| msd1-v2_ctx vs always-expensive | -0.023 (-0.074; +0.028) | 0.3819 | 0.8404 | -0.001726 (-0.001824; -0.001628) | 0.4614 | 0.9228 | 20 / 26 |
| msd1-v3_noul vs always-media | +0.016 (-0.032; +0.068) | 0.5215 | 0.8404 | +0.000066 (-0.000001; +0.000140) | 0.1081 | 0.4325 | 25 / 14 |
| msd1-v3_noul vs always-expensive | -0.047 (-0.102; +0.005) | 0.0890 | 0.5075 | -0.001837 (-0.001931; -0.001743) | 0.1524 | 0.4572 | 19 / 30 |

Análise exploratória (post hoc, decidida depois de ver a quebra por tier; não estava no plano) — cauda complexa (n=57, sem correção adicional):

| comparação | Δ nota (IC95%) | p perm. | Δ US$/msg (IC95%) | McNemar p |
|---|---:|---:|---:|---:|
| msd1-v1_score vs always-media [complexa] | +0.404 (+0.259; +0.557) | 0.0002 | +0.002018 (+0.001686; +0.002339) | 0.0000 |
| msd1-v2_ctx vs always-media [complexa] | +0.425 (+0.268; +0.588) | 0.0002 | +0.001943 (+0.001610; +0.002238) | 0.0000 |
| msd1-v3_noul vs always-media [complexa] | +0.329 (+0.158; +0.500) | 0.0006 | +0.001724 (+0.001371; +0.002063) | 0.0004 |

## Nota por tier da regra (teste)

| estratégia | simples | media | complexa |
|---|---:|---:|---:|
| always-cheap | 4.64 | 4.45 | 3.56 |
| always-media | 4.64 | 4.66 | 4.15 |
| always-expensive | 4.62 | 4.70 | 4.66 |
| oracle-regra | 4.64 | 4.66 | 4.66 |
| oracle-empirico | 4.72 | 4.73 | 4.61 |
| msd1-v1_score | 4.64 | 4.58 | 4.55 |
| msd1-v2_ctx | 4.64 | 4.63 | 4.57 |
| msd1-v3_noul | 4.65 | 4.58 | 4.48 |

## Acerto da C2 vs regra (todas as conversas roteadas do teste)

- v1_score: 0.847 (n=518)
- v2_ctx: 0.880 (n=518)
- v3_noul: 0.699 (n=518)

Truncamento (teste): {'simples': 0.0, 'media': 0.0, 'complexa': 0.0}
