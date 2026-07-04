# 🌿 Módulo 2 — A Amazônia como Território Geográfico

**Workshop: Geoprocessamento na Amazônia | Sessão 2 de 4**

---

## 2.1 A Amazônia: Que território estamos analisando?

A **Pan-amazônia** é a maior região biogeográfica do planeta. Ela compreende nove países e abrange aproximadamente **7,8 milhões de km²**:

| País | Superfície Amazônica (km²) | % do território nacional |
|---|---|---|
| Brasil | 5.217.423 | ~61% do território |
| Peru | 782.000 | ~60% do território |
| Colômbia | 477.274 | ~41% do território |
| Venezuela | 433.000 | ~47% do território |
| Bolívia | 275.000 | ~25% do território |
| Equador | 116.000 | ~45% do território |
| Suriname | 163.000 | ~97% do território |
| Guiana | 214.000 | ~99% do território |
| Guiana Francesa | 82.000 | ~97% do território |

---

## 2.2 Estrutura Física do Território Amazônico

### Relevo
A planície amazônica é predominantemente **plana** (altitudes < 200 m), com algumas exceções:
- **Escudo das Guianas** ao norte (tepui, planaltos)
- **Escudo Brasileiro** ao sul
- **Cordilheira dos Andes** a oeste (nascente do rio Amazonas)

### Hidrografia
O sistema hidrográfico amazônico é o maior do mundo:
- O **Rio Amazonas** possui ~6.992 km de extensão
- Contribui com **20% da água doce** que deságua nos oceanos do planeta
- Mais de **1.100 afluentes** documentados

### Coberturas Vegetais (MapBiomas 2022)
| Cobertura | Área (milhões ha) | % Amazônia |
|---|---|---|
| Floresta nativa | 529 | 68% |
| Área agropecuária | 103 | 13% |
| Formação savânica (Cerrado) | 57 | 7% |
| Áreas desmatadas | 40 | 5% |
| Água | 22 | 3% |
| Outros | 30 | 4% |

---

## 2.3 Tensões Territoriais na Amazônia

O território amazônico é marcado por tensões que são objeto de estudo geográfico:

```
🌲 CONSERVAÇÃO vs 🚜 AGRONEGÓCIO
   Desmatamento para soja, cana, pecuária

🏛️ ESTADOS NACIONAIS vs 🏕️ TERRITORIALIDADES INDÍGENAS
   Sobreposição de terras indígenas e concessões

⛏️ GARIMPO ILEGAL vs 💧 BACIAS HIDROGRÁFICAS
   Mercúrio nos rios, impacto em comunidades ribeirinhas

🌡️ MUDANÇAS CLIMÁTICAS vs 🌧️ CICLO HÍDRICO AMAZÔNICO
   Pontos de inflexão ("tipping points") do sistema
```

---

## 2.4 Fontes de Dados Geoespaciais para a Amazônia

### Dados Gratuitos e Acessíveis

| Fonte | Tipo de dado | URL |
|---|---|---|
| **MapBiomas** | Uso da terra anual (1985–presente) | mapbiomas.org |
| **PRODES/INPE** | Desmatamento na Amazônia | terrabrasilis.dpi.inpe.br |
| **RAISG** | Áreas protegidas e terras indígenas | amazoniasocioambiental.org |
| **Global Forest Watch** | Perda de florestas interativa | globalforestwatch.org |
| **IBGE** | Dados censitários e limites do Brasil | ibge.gov.br |
| **MINAM** | Dados ambientais do Peru | geoservidor.minam.gob.pe |
| **Copernicus/Sentinel** | Imagens de satélite 10m | scihub.copernicus.eu |

---

## 2.5 O Geoprocessamento para Problemas Amazônicos

### Casos de uso reais:

**1. Monitoramento de desmatamento**
- Comparação multitemporal de imagens Landsat/Sentinel
- Detecção de mudanças na cobertura florestal
- Ferramentas: QGIS + Python (rasterio)

**2. Mapeamento de risco de inundação**
- Análise de modelos digitais de elevação (SRTM)
- Identificação de áreas suscetíveis em cidades ribeirinhas
- Exemplo: Inundações em Anajás-PA (Amazônia brasileira)

**3. Análise de acessibilidade em territórios indígenas**
- Redes viárias, rios navegáveis
- Distâncias para serviços de saúde e educação

---

## 💻 Atividade Prática 2.1 — Mapa Base da Amazônia no QGIS

### Download de dados:
1. Vá até [naturalearthdata.com](https://naturalearthdata.com) e baixe:
   - Limites de países (1:50m)
   - Rios principais (1:10m)

2. Baixe a camada da bacia amazônica da RAISG ou do Natural Earth

### No QGIS:
```
1. Carregue os shapefiles baixados no QGIS
2. Configure a projeção para SIRGAS 2000 (EPSG: 4674)
3. Recorte as camadas para a área amazônica em Vetor > Geoprocessamento > Recortar
4. Aplique a simbologia temática:
   - Rios: linha azul, espessura variável segundo Strahler
   - Países: preenchimento semitransparente com borda preta
5. Insira título, norte, escala e legenda
6. Exporte como PNG a 300 DPI
```

📝 **Entrega:** Imagem do mapa base da Amazônia com pelo menos 3 camadas e elementos cartográficos completos.

---

## 💻 Atividade Prática 2.2 — Análise de Desmatamento (Discussão)

Acesse o [Global Forest Watch](https://www.globalforestwatch.org/dashboards/country/BRA/) e responda:

1. Quantos milhões de hectares de floresta primária o Brasil perdeu no último ano disponível?
2. Qual Estado amazônico apresenta a maior perda de floresta?
3. Quais fatores explicariam esse padrão espacial?
4. Como o geoprocessamento poderia ajudar a monitorar isso localmente?

---

## 📚 Referências do Módulo

- RAISG (2022). *Amazonía bajo presión 2022*. Red Amazónica de Información Socioambiental Georeferenciada.
- MapBiomas (2023). *Colección 8 - Uso y cobertura del suelo 1985–2022*. mapbiomas.org- INPE/PRODES (2023). *Monitoramento do Desmatamento na Amazônia Brasileira por Satélite*.

---

[⬅️ Módulo anterior](01_conceptos_sig.md) | [🏠 Índice](../README.md) | [➡️ Seguinte módulo](03_python_sig.md)
