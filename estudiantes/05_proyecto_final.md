# 🏆 Módulo 5 — Projeto Final

**Workshop: Geoprocessamento na Amazônia | Encerramento do Curso**

---

## 5.1 Descrição do Projeto

O projeto final integra todos os conteúdos do workshop. Você trabalhará de forma **individual ou em duplas** para produzir uma **análise geográfico-espacial de um problema amazônico**, usando pelo menos duas das seguintes ferramentas: QGIS, Python, dados de satélite.

---

## 5.2 Opções de Temas

Escolha **um** dos seguintes temas (ou proponha um tema próprio ao docente):

### Opção A: Monitoramento de Desmatamento
> Analise a evolução da perda de floresta em um município ou região amazônica entre 2010 e 2022. Identifique padrões espaciais e proponha hipóteses explicativas.

### Opção B: Vulnerabilidade de Territórios Indígenas
> Avalie a pressão exercida por atividades humanas (mineração, agronegócio, rodovias) sobre territórios indígenas na Amazônia. Calcule índices de vulnerabilidade.

### Opção C: Risco de Inundação em Cidade Ribeirinha
> Identifique zonas suscetíveis a inundação em uma cidade amazônica (ex. Iquitos, Belém, Manaus) usando DEM e dados hidrológicos.

### Opção D: Conectividade de Ecossistemas
> Analise a fragmentação da floresta amazônica e avalie corredores de conectividade entre fragmentos florestais remanescentes.

### Opção E: Tema Livre (com aprovação do docente)
> Proponha sua própria análise geoespacial relacionada à Amazônia.

---

## 5.3 Estrutura do Projeto

O projeto deve ser entregue como um **repositório organizado** com a seguinte estrutura:

```
projeto_final_[sobrenome]/
│
├── README.md              ← Descrição e resultados principais
├── datos/
│   ├── originales/        ← Dados originais sem processamento
│   └── procesados/        ← Camadas geradas durante a análise
├── scripts/
│   └── analisis.py        ← (Ou notebook .ipynb)
├── mapas/
│   ├── mapa_final.png     ← Mapa de alta qualidade (≥300 DPI)
│   └── mapa_interactivo.html ← (opcional, com Folium)
└── informe/
    └── informe_final.pdf  ← Relatório (ver seção 5.4)
```

---

## 5.4 Relatório Final

O relatório terá uma extensão de **4 a 6 páginas** (sem contar mapas e referências) e deve incluir:

### Estrutura do relatório:

**1. Introdução (1 página)**
- Contexto do problema
- Pergunta geográfica ou hipótese de pesquisa
- Justificativa do uso do geoprocessamento

**2. Dados e Metodologia (1 página)**
- Fontes de dados utilizadas
- Software e bibliotecas empregados
- Fluxo de geoprocessamento (pode ser um diagrama)

**3. Resultados (2 páginas)**
- Descrição das principais descobertas
- Mapa(s) com elementos cartográficos completos
- Tabelas ou estatísticas relevantes

**4. Discussão e Conclusões (1 página)**
- Crítica e interpretação geográfica dos resultados
- Limitações da análise
- Aplicações práticas e recomendações

**5. Referências bibliográficas**
- Mínimo de 5 referências no formato APA

---

## 5.5 Critérios de Avaliação

| Critério | Peso |
|---|---|
| Qualidade da análise geoespacial | 30% |
| Qualidade cartográfica dos mapas | 25% |
| Rigor do relatório escrito | 20% |
| Uso correto de ferramentas (QGIS/Python) | 15% |
| Apresentação oral (5 min) | 10% |

### Rubrica de qualidade cartográfica:

| Elemento | Excelente (5) | Bom (3) | Suficiente (1) |
|---|---|---|---|
| Elementos cartográficos | Todos presentes e corretos | Maioria presente | Alguns ausentes |
| Simbologia | Clara, significativa, coerente | Adequada | Confusa |
| Projeção | Apropriada e justificada | Correta sem justificar | Incorreta |
| Fontes citadas | Completas e precisas | Parciais | Ausentes |

---

## 5.6 Apresentação Oral

A apresentação terá **5 minutos** por equipe (+ 3 min de perguntas):

```
⏱️ Minuto 1:   Introdução e problema
⏱️ Minutos 2-3: Metodologia e dados
⏱️ Minutos 4-5: Resultados e mapas
```

**Formato:** Você pode usar slides, o próprio QGIS ou qualquer ferramenta de apresentação.

---

## 5.7 Exemplo de Trabalho de Boa Qualidade

### README.md de referência:

```markdown
# Análise de Desmatamento no Município de Novo Progresso (PA) 2015–2022

## Pergunta de Pesquisa
Qual foi o padrão espacial da perda de floresta em Novo Progresso
entre 2015 e 2022, e que relação possui com os eixos rodoviários?

## Principais Resultados
- Detectou-se uma perda total de 128.450 ha (12,4% do município)
- 78% do desmatamento ocorre em um raio de 10 km da BR-163
- Identificam-se 3 focos de expansão agropecuária ao norte do município

## Ferramentas Utilizadas
- QGIS 3.28 (análise vetorial e composição cartográfica)
- Python 3.11 + rasterio (análise de mudança raster)
- Fontes: MapBiomas Col.8, INPE-PRODES, IBGE
```

---

## 📚 Recursos de apoio

- [Tutoriais do QGIS](https://docs.qgis.org/3.28/es/docs/training_manual/)
- [GeoPandas Documentation](https://geopandas.org/en/stable/)
- [MapBiomas Brasil](https://mapbiomas.org/)
- [Global Forest Watch](https://www.globalforestwatch.org/)
- [INPE TerraBrasilis](https://terrabrasilis.dpi.inpe.br/)

---

[⬅️ Módulo anterior](04_practica_qgis.md) | [🏠 Voltar ao índice](../README.md)

---

> *Muito sucesso no seu projeto! Lembre-se: um bom mapa conta uma história com dados.*
