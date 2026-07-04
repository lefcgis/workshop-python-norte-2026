# 🔗 Módulo 5 — Recursos Adicionais e Referências

**Workshop Docentes: Geoprocessamento na Amazônia**

---

## 5.1 Repositórios de Dados Geoespaciais

### Dados Amazônicos (acesso gratuito)

| Instituição | Dataset | URL | Formato |
|---|---|---|---|
| RAISG | Áreas protegidas, territórios indígenas, pressões | [amazoniasocioambiental.org](https://amazoniasocioambiental.org) | SHP, PDF |
| MapBiomas | Uso e cobertura da terra 1985–2022 | [mapbiomas.org](https://mapbiomas.org) | TIFF, GEE |
| PRODES/INPE | Desmatamento amazônico anual | [terrabrasilis.dpi.inpe.br](https://terrabrasilis.dpi.inpe.br) | SHP, WFS |
| Global Forest Watch | Perda de floresta por país/região | [globalforestwatch.org](https://globalforestwatch.org) | TIFF, SHP |
| IBGE | Dados censitários e limites do Brasil | [ibge.gov.br/geociencias](https://ibge.gov.br/geociencias) | SHP |
| MINAM Peru | Camadas ambientais do Peru | [geoservidor.minam.gob.pe](https://geoservidor.minam.gob.pe) | WMS/SHP |
| IDEAM Colômbia | Dados ambientais da Colômbia | [ideam.gov.co](https://ideam.gov.co) | Vários |
| Natural Earth | Limites, rios, cidades mundiais | [naturalearthdata.com](https://naturalearthdata.com) | SHP |
| SRTM/ALOS | Modelos Digitais de Elevação 30m | [earthexplorer.usgs.gov](https://earthexplorer.usgs.gov) | TIFF |
| Copernicus/ESA | Imagens Sentinel-2 (10m) | [scihub.copernicus.eu](https://scihub.copernicus.eu) | SAFE |
| USGS | Imagens Landsat (30m) | [earthexplorer.usgs.gov](https://earthexplorer.usgs.gov) | TIFF |

---

## 5.2 Software e Ferramentas

### SIG de Desktop (Gratuitos)

| Software | Versão Recomendada | URL | Notas |
|---|---|---|---|
| **QGIS** | 3.34 LTR | [qgis.org](https://qgis.org) | Principal ferramenta do workshop |
| Google Earth Pro | Qualquer uma | [google.com/earth](https://google.com/earth) | Complementar, visualização |
| GRASS GIS | 8.x | [grass.osgeo.org](https://grass.osgeo.org) | Avançado, análise hidrológica |

### Ambientes Python

```bash
# Opção 1: Miniforge (recomendada - multiplataforma)
# Baixar de: [github.com/conda-forge/miniforge](https://github.com/conda-forge/miniforge)

conda create -n geoproc python=3.11
conda activate geoproc
conda install -c conda-forge \
    geopandas rasterio fiona shapely \
    folium contextily matplotlib \
    jupyterlab earthpy

# Opção 2: pip (se não tiver conda)
pip install geopandas rasterio folium contextily matplotlib jupyterlab

# Verificar instalação
python -c "import geopandas; print(geopandas.__version__)"
```

---

## 5.3 Recursos de Formação Docente

### Cursos Gratuitos Online

| Curso | Plataforma | Idioma | URL |
|---|---|---|---|
| QGIS Training Manual | [qgis.org](https://qgis.org) | ES/PT/EN | [docs.qgis.org/training_manual](https://docs.qgis.org/training_manual) |
| MapBiomas Academy | [MapBiomas](https://mapbiomas.org) | PT | [academy.mapbiomas.org](https://academy.mapbiomas.org) |
| Intro to GIS – ESRI | [Coursera](https://www.coursera.org/learn/gis) | EN | [coursera.org/learn/gis](https://coursera.org/learn/gis) |
| Python for Geospatial | [YouTube](https://www.youtube.com/watch?v=2v6202L04zM) | EN/ES | Vários canais |
| Geographic Data Science | [Online Book](https://geographicdata.science) | EN | [geographicdata.science](https://geographicdata.science) |

### Comunidades e Redes

| Rede | Descrição | Contato |
|---|---|---|
| SELPER | Soc. Latino-americana de Sensoriamento Remoto | [selper.info](https://selper.info) |
| OSGeo Latinoamérica | Capítulo regional da OSGeo | [osgeo.org](https://osgeo.org) |
| GEOLATAM | Comunidade de SIG em espanhol | Twitter/X: #GEOLATAM |
| Geoforos.es | Fórum de GIS em espanhol | [geoforos.es](https://geoforos.es) |
| QGIS Brasil | Lista de discussão do QGIS em português | [qgis.org/community](https://qgis.org/community) |
| QGIS Perú | Lista de discussão do QGIS em espanhol | [qgis.org/community](https://qgis.org/community) |

---

## 5.4 Bibliografia Completa do Workshop

### Artigos Acadêmicos

```
Ito, M. H.; Fonseca Filho, H.; Conti, L. A. (2017). Uso do software livre
QGIS (Quantum GIS) para ensino de Geoprocessamento em nível superior. Revista Cartográfica,
94, IPGH. Disponível: bibliotecadigital.inah.gob.mx/...REVCAR_00_0094_2017_P127.pdf

Souza, M.B. et al. (2021). O uso das geotecnologias como ferramentas
de ensino na educação básica da escola Prof.º Virgílio Libonati, Belém,
Pará, Brasil. Research, Society and Development, 10(5), e4410514856.
DOI: 10.33448/rsd-v10i5.14856

Câmara, G. et al. (2001). Anatomia de Sistemas de Informação Geográfica.
Instituto Nacional de Pesquisas Espaciais (INPE). São José dos Campos, Brasil.
Disponível: dpi.inpe.br/gilberto/tutoriais/sig_intro/anatomia.pdf
```

### Livros

```
Porto-Gonçalves, C.W. (2001). Amazonía, Amazonías. Edições Unesp, São Paulo.

Haesbaert, R. (2004). O mito da desterritorialização: do "fim dos territórios"
à multiterritorialidade. Bertrand Brasil, Rio de Janeiro.

Sherman, G. (2018). The PyQGIS Programmer's Guide. Locate Press.

Longley, P.A. et al. (2015). Geographic Information Science and Systems.
Wiley, 4ª ed.

Bivand, R. et al. (2013). Applied Spatial Data Analysis with R. Springer.
```

### Relatórios Institucionais

```
RAISG (2022). Amazonía bajo presión 2022. Rede Amazônica de Informação
Socioambiental Georreferenciada. amazoniasocioambiental.org

MapBiomas (2023). Relatório Anual do Desmatamento no Brasil 2022.
Disponível: mapbiomas.org/en

IPCC (2022). Climate Change 2022: Impacts, Adaptation and Vulnerability.
Capítulo sobre ecossistemas tropicais. ipcc.ch
```

---

## 5.5 Modelos Reutilizáveis

### Modelo de Projeto QGIS (.qgz)

Para cada workshop, prepare um projeto QGIS base com:
- CRS configurado (SIRGAS 2000 / EPSG:4674)
- Grupo de camadas: "Dados amazônicos base"
- Estilos .qml predefinidos para: territórios indígenas, ANPs, desmatamento
- Layout de mapa base com elementos cartográficos vazios

### Modelo de Jupyter Notebook

```python
# WORKSHOP: Geoprocessamento na Amazônia
# Módulo 3 - Análise Python
# Autor: [Nome] | Data: [Data]

# ============================
# IMPORTAR BIBLIOTECAS
# ============================
import geopandas as gpd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import folium

# ============================
# CAMINHOS DE DADOS
# ============================
CAMINHO_DADOS = "./dados/"
CAMINHO_SAIDA = "./saida/"

# ============================
# AQUI COMEÇA A SUA ANÁLISE
# ============================
```

---

## 5.6 Cronograma de Atualização do Material

Recomenda-se revisar e atualizar este workshop **anualmente**:

| Elemento | Frequência de atualização | Motivo |
|---|---|---|
| Dados de desmatamento | Anual | MapBiomas publica novas coleções |
| Versão do QGIS referenciada | A cada LTR (~1 ano) | Modificações na interface |
| Dados de territórios indígenas | Bienal | A RAISG atualiza seus mapas |
| Bibliografia | Bienal | Novas publicações |
| Scripts de Python | Anual | Atualizações de bibliotecas |

---

[⬅️ Avaliação](04_evaluacion.md) | [🏠 Voltar ao Índice](../README.md)

---

*Este workshop foi desenvolvido com base em pesquisas acadêmicas sobre ensino do geoprocessamento na Amazônia. Autoriza-se seu uso e adaptação com fins educativos não comerciais, citando a fonte.*
