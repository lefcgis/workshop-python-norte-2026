# Dados — Workshop MCP: servidor Python para análise geoespacial da Amazônia

Dados de exemplo usados pelo `server.py` do workshop (`workshop_mcp_python_norte.md`).
Baixados em 2026-07-02.

| Arquivo | Origem | Situação |
|---|---|---|
| `terras_indigenas.geojson` | **FUNAI** — GeoServer, camada `Funai:tis_amazonia_legal_poligonais` (WFS) | ✅ **Dado oficial real** (401 terras indígenas da Amazônia Legal). Geometria simplificada (~500 m) para reduzir o tamanho. Adicionada a coluna `nome_ti` (cópia de `terrai_nome`) porque o código de exemplo do workshop a utiliza. |
| `municipios_amazonia.geojson` | **IBGE** — Malha Municipal 2022 (`BR_Municipios_2022`), filtrada à Amazônia Legal | ✅ **Dado oficial real** (760 municípios: 8 estados integrais + MA a oeste de 44°O). Colunas: `cd_mun`, `municipio`, `sigla_uf`, `area_km2`. Geometria simplificada (~500 m). |
| `desmatamento_2020_2024.csv` | **PRODES/INPE** — camada `prodes-legal-amz:yearly_deforestation` (GeoServer WFS), agregada por município | ✅ **Dado oficial real** (599 municípios, 2020–2024). Colunas: `municipio`, `sigla_uf`, `ano`, `area_km2`. Ver metodologia abaixo. |
| `mineracao.geojson` | **ANM/SIGMINE** — processos minerários por UF (dados abertos), 9 estados da Amazônia Legal | ✅ **Dado oficial real** (8.303 processos de mineração ativa/titulada). Colunas: `processo`, `titular`, `substancia`, `fase`, `area_ha`, `ano`, `uf`. Ver metodologia abaixo. |

## Metodologia do `desmatamento_2020_2024.csv` (dado real)

Os polígonos anuais de incremento de desmatamento do PRODES (Amazônia Legal) foram baixados via
WFS do GeoServer do TerraBrasilis (camada `prodes-legal-amz:yearly_deforestation`, ~262 mil
polígonos nos 5 anos, paginando de 50 mil em 50 mil). Cada polígono já traz `area_km` e `year`;
foi atribuído a um município pelo seu **ponto interior** (`representative_point`) via *spatial join*
com a malha municipal completa do IBGE 2022, e a área somada por município e por ano.

Totais obtidos (km²): 2020 ≈ 10.496 · 2021 ≈ 12.406 · 2022 ≈ 12.691 · 2023 ≈ 8.020 · 2024 ≈ 6.264.

> Observação: estes valores refletem o **incremento por ano-calendário** (`year`) da camada
> vetorial. Podem divergir ligeiramente da *taxa* oficial consolidada do PRODES (que usa o
> "ano PRODES" agosto–julho e filtros próprios). Os dados de 2024 podem estar preliminares
> (atualização BiomasBR de março/2026). Fonte: <https://terrabrasilis.dpi.inpe.br/>.

## Metodologia do `mineracao.geojson` (dado real)

Baixados os shapefiles de processos minerários por estado do portal de dados abertos da ANM
(<https://dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/>), para os 9 estados da Amazônia
Legal — **60.391 processos no total**. Geometrias corrigidas (2D + `make_valid`) e reprojetadas
para WGS84. Para manter o arquivo utilizável no workshop, foi mantido o subconjunto de
**mineração ativa/titulada** (extração e títulos concedidos), excluindo requerimentos e
autorizações de pesquisa:

| Fase mantida | Nº |
|---|---|
| LICENCIAMENTO | 4.351 |
| LAVRA GARIMPEIRA | 2.541 |
| CONCESSÃO DE LAVRA | 1.058 |
| REGISTRO DE EXTRAÇÃO | 353 |
| **Total no arquivo** | **8.303** |

> Sobreposição com terras indígenas (verificada): **84 processos minerários sobre 32 TIs**
> (ex.: Kayapó, Apyterewa, Sawré Muybu, Araraê). Substância predominante: minério de ouro.
> Para incluir **todos** os 60.391 processos (inclusive requerimentos e pesquisa), baixe
> novamente os ZIPs por UF e remova o filtro de `fase`. Fonte: ANM/SIGMINE, dados gerados
> diariamente. Alternativa pan-amazônica: RAISG <https://www.amazoniasocioambiental.org/pt-br/mapas/>.

## Verificação

As três ferramentas do `server.py` foram testadas contra estes dados e funcionam
(`consultar_desmatamento`, `verificar_sobreposicao`, `gerar_mapa_municipios`).
