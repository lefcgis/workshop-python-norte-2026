# 🖥️ Módulo 4 — Prática com QGIS: Análise Territorial da Amazônia

**Workshop: Geoprocessamento na Amazônia | Sessão 4 de 4 (Parte 1)**

---

## 4.1 Objetivo da Sessão

Nesta sessão prática, você criará uma **análise territorial completa da Amazônia** usando o QGIS, combinando múltiplas camadas de dados para responder a uma pergunta geográfica concreta:

> **Qual proporção dos territórios indígenas amazônicos se sobrepõe a áreas de alta pressão de desmatamento?**

---

## 4.2 Dados Necessários

Baixe os seguintes dados antes de começar:

| Camada | Fonte | Formato |
|---|---|---|
| Limite amazônico | RAISG | SHP |
| Territórios indígenas | RAISG / SIRTD | SHP |
| Áreas naturais protegidas | RAISG | SHP |
| Perda de floresta 2010–2022 | Global Forest Watch | TIFF |
| Rios principais amazônicos | Natural Earth | SHP |
| Limites de países | Natural Earth | SHP |

🔗 **Links diretos:**
- [RAISG Geospatial Data](https://www.amazoniasocioambiental.org/es/mapas/)
- [Global Forest Watch Data](https://data.globalforestwatch.org/)
- [Natural Earth](https://www.naturalearthdata.com/downloads/)

---

## 4.3 Fluxo de Trabalho no QGIS

### PASSO 1: Configuração do Projeto

```
1. Abra o QGIS → Novo Projeto
2. Vá em Projeto → Propriedades → SRC
3. Selecione EPSG:5880 (SIRGAS 2000 / Cônica de Gauss para o Brasil)
   Ou use EPSG:4674 (SIRGAS 2000 geográfico) se preferir graus
4. Salve o projeto como: "analise_amazonia.qgz"
```

### PASSO 2: Carga e Organização de Camadas

```
1. Arraste os SHP para a janela de camadas (painel esquerdo)
2. Organize a ordem das camadas (de cima para baixo):
   ✓ Limite Amazônico
   ✓ Territórios Indígenas
   ✓ Áreas Protegidas
   ✓ Rios principais
   ✓ Desmatamento (raster)
   ✓ Limites de países (ao fundo)
3. Aplique uma simbologia inicial a cada camada
```

### PASSO 3: Simbologia Temática

```
TERRITÓRIOS INDÍGENAS:
→ Preenchimento: #90EE90 (verde claro), opacidade 60%
→ Borda: #228B22 (verde floresta), 0.7px

ÁREAS PROTEGIDAS:
→ Preenchimento: #87CEEB (celeste), opacidade 50%
→ Borda: #1E90FF (azul), 0.7px

PERDA DE FLORESTA (RASTER):
→ Propriedades → Simbologia → Banda simples falsa cor
→ Paleta: "Reds" (de amarelo a vermelho intenso)
→ Classificar com 5 classes

RIOS:
→ Linha: #4169E1 (azul), 1px
→ Se houver campo "STRAHLER", use espessura variável por ordem
```

### PASSO 4: Geoprocessamento — Sobreposição Territorial

```
Vetor → Geoprocessamento → Interseção

ANÁLISE 1: Territórios Indígenas em perigo
- Camada de entrada: Territórios Indígenas
- Camada de sobreposição: Polígonos de desmatamento > 2020
- Salvar como: "territindige_desmatados.shp"

ANÁLISE 2: Buffer de rios principais
- Vetor → Geoprocessamento → Buffer (Zona de amortecimento)
- Camada: Rios principais
- Distância: 10 km
- Segmentos: 20
- Salvar como: "buffer_rios_10km.shp"
```

### PASSO 5: Cálculo de Estatísticas

```
Vetor → Análise → Estatísticas básicas

1. Abra a tabela de atributos de "territindige_desmatados.shp"
2. Abra a calculadora de campos (Ctrl+I ou botão do ábaco)
3. Crie um novo campo: area_intersect_km2
   Expressão: $area / 1000000
4. Analise a proporção: area_intersect / area_total × 100
```

### PASSO 6: Composição do Mapa Final

```
Projeto → Novo Layout de Impressão

ELEMENTOS OBRIGATÓRIOS:
✓ Mapa principal (escala 1:5.000.000 aprox.)
✓ Mapa de localização (pequeno, no canto inferior)
✓ Título: "Pressão de Desmatamento sobre Territórios Indígenas Amazônicos"
✓ Legenda com todos os elementos
✓ Escala gráfica e numérica
✓ Rosa dos ventos (indicador de norte)
✓ Sistema de coordenadas e fontes de dados
✓ Autor e data

CONFIGURAÇÃO DE EXPORTAÇÃO:
→ Exportar como imagem → PNG → 300 DPI (impressão)
→ Também exportar como PDF vetorial
```

---

## 4.4 Checklist de Qualidade do Mapa

Antes de entregar, verifique:

- [ ] O mapa possui título descritivo e apropriado
- [ ] A legenda é clara e completa
- [ ] A escala é apropriada para a área representada
- [ ] As cores são legíveis (contraste adequado)
- [ ] As fontes de dados estão citadas
- [ ] A projeção é adequada para a análise realizada
- [ ] Todos os elementos cartográficos estão presentes

---

## 4.5 Extensão: Automatización com PyQGIS

Se você tiver tempo extra, automatize a análise anterior com este script no Console Python do QGIS:

```python
from qgis.core import *
import processing

# Caminho dos dados
ruta = "C:/mi_proyecto/datos/"

# Carrega as camadas
terr_indigenas = QgsVectorLayer(ruta + "territorios_indigenas.shp", "TI", "ogr")
deforestacion = QgsVectorLayer(ruta + "deforest_2020_2022.shp", "Deforest", "ogr")

# Adiciona ao projeto
QgsProject.instance().addMapLayer(terr_indigenas)
QgsProject.instance().addMapLayer(deforestacion)

# Interseção automática
result = processing.run("native:intersection", {
    'INPUT': terr_indigenas,
    'OVERLAY': deforestacion,
    'OUTPUT': ruta + "salida/interseccion_ti_deforest.shp"
})

print("✅ Interseção concluída")
print(f"Resultado salvo em: {result['OUTPUT']}")
```

---

## 📚 Referências do Módulo

- QGIS Documentation Team (2023). *QGIS Training Manual*. docs.qgis.org
- Sherman, G. (2018). *The PyQGIS Programmer's Guide*. Locate Press.
- RAISG (2022). *Amazonía bajo presión: Deforestación y territorios indígenas*.

---

[⬅️ Módulo anterior](03_python_sig.md) | [🏠 Índice](../README.md) | [➡️ Projeto Final](05_proyecto_final.md)
