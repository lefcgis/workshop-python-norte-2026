# 📝 Módulo 3 — Sequências Didáticas

**Workshop Docentes: Geoprocessamento na Amazônia**

---

## Sequência Didática 1 — Conceitos SIG (4 horas)

### Dados de identificação

| Campo | Detalhe |
|---|---|
| **Sessão** | 1 de 4 |
| **Duração** | 4 horas |
| **Audiência** | Estudantes universitários, 2º ao 4º ano |
| **Objetivo** | Compreender os fundamentos dos SIG e das geotecnologias |
| **Modalidade** | Presencial ou virtual síncrona |

---

### Desenvolvimento da Sessão 1

#### 🔵 Abertura (30 min)

**Atividade: O mapa que não diz tudo**

1. Mostre duas representações do mesmo espaço amazônico:
   - Um mapa político tradicional (recorte em papel ou PDF)
   - Uma imagem Sentinel-2 em composição de falsa cor no QGIS
2. Pergunte: *Que informação a imagem tem que o mapa não possui?*
3. Registro de ideias no quadro ou Jamboard colaborativo

**Materiais:** Projetor, QGIS aberto com a imagem de satélite pré-carregada.

---

#### 🟡 Desenvolvimento (2.5 horas)

**Bloco 1 (45 min): Fundamentos teóricos — apresentação interativa**

- Tipos de dados: vetorial vs. raster (com exemplos amazônicos)
- Sistemas de referência e projeções (analogia do mapa da casca de laranja)
- Ecossistema de geotecnologias: qual ferramenta para qual problema?

*Técnica: Cada conceito teórico é seguido por um exemplo visual no QGIS (modelagem do docente)*

**Bloco 2 (45 min): Exploração guiada do QGIS**

```
Guia passo a passo:
1. Instalar o QuickMapServices
2. Adicionar imagem Google Hybrid
3. Navegar até a Amazônia (coordenadas fornecidas)
4. Adicionar um shapefile de países (Natural Earth)
5. Alterar o SRC do projeto
6. Identificar atributos de feições
```

**Bloco 3 (60 min): Prática independente + encerramento**

- Cada estudante explora uma região amazônica de sua escolha
- Identifica 5 elementos geográficos e anota suas coordenadas
- Usa a ferramenta "Identificar feições" para explorar atributos

---

#### 🔴 Encerramento (30 min)

**Questionário de verificação (5 perguntas, ver Módulo 4 de avaliação)**

**Reflexão coletiva:**
> O que você poderia analisar na Amazônia com essas ferramentas?

**Tarefa para casa:**
> Baixe o shapefile de bacias hidrográficas do IBGE ou do MINAM e explore-o no QGIS. Escreva 3 observações.

---

## Sequência Didática 2 — Amazônia Territorial (4 horas)

### Objetivo
Analisar a Amazônia como território geográfico complexo usando dados geoespaciais reais.

### Desenvolvimento

| Tempo | Atividade | Tipo |
|---|---|---|
| 0:00–0:30 | Abertura: Notícias recentes sobre a Amazônia + debate inicial | Coletiva |
| 0:30–1:30 | Análise de dados quantitativos (tabelas de cobertura, desmatamento) | Coletiva |
| 1:30–2:30 | Prática 2.1: Mapa base da Amazônia no QGIS (guiada) | Individual |
| 2:30–3:30 | Prática 2.2: Análise no Global Forest Watch (exploração livre) | Duplas |
| 3:30–4:00 | Discussão + reflexão coletiva | Coletiva |

**Pergunta central da sessão:**
> *O que o mapa nos diz que as estatísticas sozinhas não podem nos dizer?*

---

## Sequência Didática 3 — Python para Geoprocessamento (4 horas)

### Objetivo
Introduzir o Python como ferramenta de automatização de análises geoespaciais.

### Estrutura

```
[0:00 – 0:30]  Por que Python? Demonstração motivacional
               → Mostre a mesma análise no QGIS (5 min manual)
                 vs. Python (30 segundos com script)

[0:30 – 1:30]  Configuração do ambiente e primeiro script
               → Instalar dependências, abrir Jupyter, ler um shapefile

[1:30 – 2:30]  Análise guiada: Cálculo de áreas com GeoPandas
               → Reprojetar, calcular campo, exportar resultados

[2:30 – 3:30]  Prática: Cálculo de NDVI com Rasterio
               → Código comentado, modificar parâmetros

[3:30 – 4:00]  Mapa interativo com Folium (demonstração opcional)
               → Gerar HTML, abrir no navegador
```

**Nota ao docente:** É normal que estudantes sem experiência em programação se sintam frustrados. Enfatize que o **objetivo não é dominar o Python**, mas sim ver seu potencial para a análise geoespacial.

---

## Sequência Didática 4 — QGIS Avançado + Projeto Final (4 horas)

### Objetivo
Integrar todos os aprendizados em uma análise geoespacial completa.

### Estrutura

```
[0:00 – 0:30]  Instruções do projeto final (ver módulo 5 estudantes)
               → Apresentar as 5 opções de temas
               → Formação de grupos ou trabalho individual

[0:30 – 2:30]  Trabalho autônomo na análise
               → O docente circula e oferece suporte
               → Consultas técnicas individuais

[2:30 – 3:00]  Composição do mapa no QGIS (Layout de Impressão)
               → Checklist de elementos cartográficos

[3:00 – 4:00]  Apresentações rápidas (5 min por grupo)
               → Feedback entre colegas
               → Encerramento do workshop
```

---

## Modelo de Planejamento de Aula (Para o Docente)

```markdown
## Aula: [Nome]
**Data:** [dd/mm/aaaa]
**Módulo:** [Nº]  
**Objetivo:** [...]

### Momentos
| Tempo | Atividade | Responsável | Recursos |
|---|---|---|---|
| 0:00–0:XX | Abertura | Docente | |
| 0:XX–0:XX | Desenvolvimento | Docente + Estudantes | |
| 0:XX–0:XX | Encerramento | Docente | |

### Indicadores de alcance
- [ ] [...indicador 1...]
- [ ] [...indicador 2...]

### Observações pós-aula
[Espaço para reflexão docente]
```

---

[⬅️ Didática](02_didactica_sig.md) | [🏠 Índice](../README.md) | [➡️ Avaliação](04_evaluacion.md)
