# Churn Card

Componente visual para cards de churn em notebooks/Colab.

## Estrutura

```text
churn-card/
├── churn-card.css
├── churn-card.js
├── colab_churn_card.py
└── README.md
```

## O que fica no GitHub público

- `churn-card.css`
- `churn-card.js`

Não coloque CSV, IDs, bases de cliente ou estatísticas reais no repositório.

## O que fica no Colab

- leitura do CSV
- cálculo das estatísticas
- geração do payload JSON
- chamada do componente

## Publicação via jsDelivr

Depois de subir o repositório público no GitHub, troque `SEU_USUARIO` nas URLs:

```python
CSS_URL = "https://cdn.jsdelivr.net/gh/SEU_USUARIO/churn-card@main/churn-card.css"
JS_URL = "https://cdn.jsdelivr.net/gh/SEU_USUARIO/churn-card@main/churn-card.js"
```

## Uso no Colab

```python
import pandas as pd

df = pd.read_csv("/content/churnCLARO(1).csv")

payload = build_churn_payload(df)
render_churn_card(payload)
```

## Observação

O JS não calcula estatística. Ele só renderiza. O Python monta um JSON pequeno com métricas, rótulos e HTML do tooltip.

## Tooltip geral

O badge superior `Base geral` usa `data-ca-key="overall"` e exibe as estatísticas gerais do DataFrame.
