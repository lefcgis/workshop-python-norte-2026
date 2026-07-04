# 🐍 Módulo 3 — Python para Geoprocessamento

**Workshop: Geoprocessamento na Amazônia | Sessão 3 de 4**

---

## 3.1 Por que Python para análise geoespacial?

O Python tornou-se a linguagem padrão para o geoprocessamento por ser:

- ✅ **Gratuito e de código aberto**
- ✅ **Enorme ecossistema de bibliotecas geoespaciais**
- ✅ **Integrado ao QGIS** (você tem o Python disponível no menu de Complementos)
- ✅ **Reprodutibilidade** da análise científica
- ✅ **Automatização** de tarefas repetitivas

---

## 3.2 O Ecossistema Geoespacial do Python

```
📦 BIBLIOTECAS FUNDAMENTAIS
│
├── GeoPandas     → Dados vetoriais (shapefiles, GeoJSON)
├── Shapely       → Operações geométricas
├── Rasterio      → Leitura e escrita de dados raster
├── Fiona         → E/S de formatos vetoriais
├── PyProj        → Projeções e sistemas de referência
│
📦 VISUALIZAÇÃO
│
├── Matplotlib    → Gráficos estáticos
├── Folium        → Mapas interativos (Leaflet.js)
├── Contextily    → Mapas de fundo (tiles)
│
📦 ANÁLISE AVANÇADA
│
├── PySAL         → Estatística espacial
├── EarthPy       → Sensoriamento remoto simplificado
└── ee (earthengine-api) → Google Earth Engine
```

---

## 3.3 Instalação do Ambiente

```bash
# Opção 1: conda (recomendado)
conda create -n geoproc python=3.11
conda activate geoproc
conda install -c conda-forge geopandas rasterio folium contextily earthpy

# Opção 2: pip
pip install geopandas rasterio folium contextily matplotlib
```

---

## 3.4 Código Base: Leitura de Dados Vetoriais

```python
import geopandas as gpd
import matplotlib.pyplot as plt

# Ler um shapefile de bacias hidrográficas amazônicas
cuencas = gpd.read_file("datos/cuencas_amazonia.shp")

# Informações básicas
print(cuencas.head())
print(f"CRS: {cuencas.crs}")
print(f"Número de polígonos: {len(cuencas)}")

# Visualização rápida
fig, ax = plt.subplots(figsize=(12, 8))
cuencas.plot(ax=ax, color='lightblue', edgecolor='navy', linewidth=0.5)
ax.set_title("Bacias Hidrográficas da Amazônia", fontsize=14)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
plt.tight_layout()
plt.savefig("salida/cuencas_amazonia.png", dpi=150)
plt.show()
```

---

## 3.5 Código: Análise de Áreas e Filtragem

```python
import geopandas as gpd

# Carregar camada de áreas protegidas da Amazônia
areas_prot = gpd.read_file("datos/areas_protegidas.shp")

# Reprojetar para calcular áreas em km²
# SIRGAS 2000 / Brazil Polyconic (EPSG: 5880)
areas_prot = areas_prot.to_crs(epsg=5880)

# Calcular área em km²
areas_prot['area_km2'] = areas_prot.geometry.area / 1e6

# Filtrar apenas as que superam 1000 km²
grandes = areas_prot[areas_prot['area_km2'] > 1000].copy()

# Ver as 10 maiores
print(grandes[['nombre', 'tipo', 'area_km2']].sort_values('area_km2', ascending=False).head(10))

# Exportar resultado
grandes.to_file("salida/grandes_areas_protegidas.shp")
```

---

## 3.6 Código: Mapa Interativo com Folium

```python
import folium
import geopandas as gpd

# Carregar dados
deforest = gpd.read_file("datos/deforestacion_2022.shp")
deforest = deforest.to_crs(epsg=4326)  # Folium precisa de WGS84

# Criar mapa centrado na Amazônia
mapa = folium.Map(
    location=[-4.5, -62.0],
    zoom_start=5,
    tiles='CartoDB dark_matter'
)

# Adicionar camada de desmatamento
folium.GeoJson(
    deforest,
    name='Desmatamento 2022',
    style_function=lambda x: {
        'fillColor': '#ff4500',
        'color': '#ff0000',
        'weight': 0.5,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(fields=['municipio', 'area_ha'])
).add_to(mapa)

folium.LayerControl().add_to(mapa)
mapa.save("salida/deforestacion_interactivo.html")
print("Mapa salvo. Abra-o no seu navegador.")
```

---

## 3.7 Código: Leitura de Dados Raster (Imagens de Satélite)

```python
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.plot import show

# Abrir imagem de satélite Landsat da Amazônia
with rasterio.open("datos/landsat_amazonia_B4.tif") as src:
    banda_roja = src.read(1)
    perfil = src.profile
    print(f"Resolução: {src.res} m")
    print(f"CRS: {src.crs}")
    print(f"Dimensões: {src.height} x {src.width} pixels")

with rasterio.open("datos/landsat_amazonia_B5.tif") as src:
    banda_nir = src.read(1)

# Calcular o NDVI (Índice de Vegetação por Diferença Normalizada)
# NDVI = (NIR - Vermelho) / (NIR + Vermelho)
ndvi = (banda_nir.astype(float) - banda_roja.astype(float)) / \
       (banda_nir.astype(float) + banda_roja.astype(float))

# Visualizar o NDVI
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
plt.colorbar(im, ax=ax, label='NDVI')
ax.set_title("NDVI - Vegetação Amazônica\n(verde = floresta densa, vermelho = sem vegetação)", fontsize=13)
plt.tight_layout()
plt.savefig("salida/ndvi_amazonia.png", dpi=150)
plt.show()
```

---

## 3.8 Python dentro do QGIS

O QGIS possui um console Python integrado (`Complementos → Console Python`):

```python
# A partir do console Python do QGIS
from qgis.core import QgsProject, QgsVectorLayer

# Listar todas as camadas do projeto atual
capas = QgsProject.instance().mapLayers()
for nombre, capa in capas.items():
    print(f"{capa.name()} — {capa.geometryType()}")

# Contar feições de uma camada ativa
capa_activa = iface.activeLayer()
print(f"Número de feições: {capa_activa.featureCount()}")
```

---

## 💻 Atividade Prática 3.1 — Sua primeira análise geoespacial

**Objetivo:** Calcular o NDVI de uma pequena área amazônica usando Python.

### Dados:
- Baixe imagens do **Copernicus Open Access Hub** (requer cadastro gratuito): [scihub.copernicus.eu](https://scihub.copernicus.eu)
- Ou utilize o script de download do **Google Earth Engine** (se tiver conta)

### Passos:
```
1. Crie um Jupyter Notebook chamado "pratica_ndvi.ipynb"
2. Importe o rasterio, numpy e matplotlib
3. Leia as bandas B4 (vermelha) e B8 (NIR) do Sentinel-2
4. Calcule o NDVI
5. Classifique o NDVI: floresta (>0.5), vegetação esparsa (0.2-0.5), sem vegetação (<0.2)
6. Visualize o resultado com uma paleta de cores adequada
7. Salve a imagem resultante como GeoTIFF
```

📝 **Entrega:** Notebook .ipynb com o código e a visualização do NDVI.

---

## 📚 Referências do Módulo

- Gillies, S. et al. (2023). *GeoPandas: Python tools for geographic data*. geopandas.org
- Kelsey, H. et al. (2019). *EarthPy: A Python package that makes it easier to explore and plot raster and vector data*.
- Google Earth Engine Team (2023). *Earth Engine Python API*. developers.google.com/earth-engine

---

[⬅️ Módulo anterior](02_amazonia_territorial.md) | [🏠 Índice](../README.md) | [➡️ Seguinte módulo](04_practica_qgis.md)
