# 🗺️ Módulo 1 — Conceitos SIG e Geotecnologias

**Workshop: Geoprocessamento na Amazônia | Sessão 1 de 4**

---

## 1.1 O que é um SIG?

Um **Sistema de Informação Geográfica (SIG)** é um conjunto integrado de:

- **Software** para captura, armazenamento, análise e visualização de dados espaciais
- **Hardware** (computador, GPS, scanner)
- **Dados geoespaciais** (vetoriais e raster/matriciais)
- **Pessoas** que os interpretam e analisam
- **Métodos** e procedimentos de análise

> 📖 *"O SIG permite integrar, analisar e visualizar informações com referência geográfica, possibilitando a compreensão de padrões espaciais no território."* (Câmara et al., 2001)

---

## 1.2 Tipos de Dados Geoespaciais

### Dados Vetoriais
Representam feições discretas do mundo real.

| Tipo | Geometria | Exemplo Amazônico |
|---|---|---|
| Ponto | Coordenada XY | Estação meteorológica |
| Linha | Sequência de pontos | Rio Amazonas |
| Polígono | Área fechada | Área Protegida, Terra Indígena |

### Dados Raster / Matriciais
Representam superfícies contínuas em uma grade de células (pixels).

| Tipo | Resolução | Exemplo |
|---|---|---|
| Imagem de satélite | 10m - 30m | Sentinel-2, Landsat |
| Modelo Digital de Elevação | 30m | SRTM, ALOS |
| Mapa de uso da terra | variável | MapBiomas Amazonia |

---

## 1.3 Projeções e Sistemas de Referência

### Por que as projeções importam?
A Terra é esférica (esferoide), mas os mapas são planos. Toda projeção implica **distorção** em algum destes elementos:
- 📏 Distância
- 📐 Ângulos (forma)
- 🔲 Área
- 🧭 Direção

### Projeções comuns para a Amazônia

| Projeção | Sistema | Uso recomendado |
|---|---|---|
| SIRGAS 2000 | EPSG:4674 | Dados em toda a América do Sul |
| UTM 18S-22S | EPSG:32718-32722 | Análises locais em faixas específicas |
| WGS84 | EPSG:4326 | Dados de GPS, visualização web |

---

## 1.4 Geotecnologias: indo além do SIG

O ecossistema de ferramentas geoespaciais hoje inclui:

```
SIG de desktop:     QGIS, ArcGIS
Sensoriamento remoto: Google Earth Engine, ENVI
Programação:        Python (GeoPandas, Rasterio), R (sf, terra)
Plataformas web:     ArcGIS Online, Google Maps API
GPS/Campo:          ODK, KoBoToolbox, QField
```

---

## 1.5 O Geoprocessamento como Método Científico

O geoprocessamento segue uma lógica rigorosa:

```
1. PERGUNTA ESPACIAL
   Onde ocorre X? Como X muda no tempo?

2. DADOS
   Coleta de camadas vetoriais e raster relevantes

3. PROCESSAMENTO
   Sobreposição, buffer, recorte, cálculo de índices

4. ANÁLISE
   Estatística espacial, interpretação de padrões

5. VISUALIZAÇÃO
   Mapas, gráficos, relatórios

6. DECISÃO / CONHECIMENTO
   Interpretação geográfica do fenômeno
```

---

## 💻 Atividade Prática 1.1

**Exploração inicial do QGIS**

1. Abra o **QGIS** em seu computador
2. Vá em `Complementos → Gerenciar e Instalar Complementos`
3. Busque e instale **"QuickMapServices"** para usar mapas de fundo
4. Adicione uma camada de fundo: `Web → QuickMapServices → Google → Google Hybrid`
5. Navegue até a região amazônica (5°N, 70°O aproximadamente)
6. Anote 3 características que você possa identificar a partir da imagem de satélite

📝 **Reflexão:** Que informação a imagem lhe fornece que não está explícita em um mapa convencional?

---

## 🧩 Avaliação do Módulo 1

**Questionário breve (5 perguntas)**

1. Qual é a diferença fundamental entre dados vetoriais e raster/matriciais?
2. Por que é importante escolher corretamente o sistema de projeção?
3. Nomeie 2 geotecnologias de código aberto e seus principais usos.
4. Que tipo de geometria você usaria para representar uma bacia hidrográfica?
5. Por que a Amazônia é um território relevante para estudo com SIG?

---

## 📚 Referências do Módulo

- Câmara, G. et al. (2001). *Anatomia de Sistemas de Informação Geográfica*. INPE.
- QGIS Development Team (2023). *QGIS User Guide*. [qgis.org](https://qgis.org)
- Souza et al. (2021). *O uso das geotecnologias como ferramentas de ensino na educação básica*. DOI: 10.33448/rsd-v10i5.14856

---

[⬅️ Módulo anterior](00_presentacion.md) | [🏠 Índice](../README.md) | [➡️ Seguinte módulo](02_amazonia_territorial.md)
