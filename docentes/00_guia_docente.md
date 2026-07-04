# 📚 Guia Docente — Workshop: Geoprocessamento na Amazônia

**Itinerário para Docentes de Geografia**  
**Evento**: Python Norte 2026  
**Data**: 3, 4 e 5 de julho de 2026  
**Local**: UNAMA Ananindeua, Pará, Brasil.   
**Docente**: Luis Eduardo Ferrer Cruz  
**Contato**: luchofgis (LinkedIn) / lefcgis (GitHub)  

---

## Apresentação do Guia

Este guia é destinado a **professores universitários de Geografia** que desejam implementar o workshop de Geoprocessamento na Amazônia em seus próprios contextos educacionais. Ele fornece o marco pedagógico, as sequências didáticas, os recursos e os instrumentos de avaliação necessários.

---

## Fundamentos Pedagógicos

O design deste workshop baseia-se em três abordagens complementares:

### 1. Aprendizagem Baseada em Problemas (ABP)
Os estudantes não aprendem o SIG como um fim em si mesmo, mas como uma **ferramenta para resolver questões geográficas reais** sobre o território amazônico.

### 2. Aprendizagem Ativa com Tecnologia
Seguindo **Ito et al. (2017)**, o uso de software livre como o QGIS facilita a inclusão de ferramentas geoespaciais em contextos universitários com recursos limitados, democratizando o acesso ao geoprocessamento.

### 3. Contextualização Amazônica
Os problemas territoriais da Amazônia (desmatamento, territórios indígenas, riscos de inundação) são **altamente significativos** para estudantes latino-americanos de Geografia, favorecendo a motivação e a transferência de conhecimento.

---

## Perfil do Docente que utiliza este Workshop

Este material é adequado para docentes que:

- Ministram disciplinas de Cartografia, SIG, Sensoriamento Remoto ou Geografia Física
- Possuem conhecimentos básicos de QGIS (não requer Python avançado)
- Buscam incorporar ferramentas digitais à sua prática docente
- Trabalham com estudantes do 2º ao 4º ano de Geografia

---

## Estrutura Recomendada do Curso

| Modalidade | Duração | Sessões |
|---|---|---|
| **Workshop intensivo** | 2 dias (16h) | 4 sessões de 4h |
| **Módulo semestral** | 8 semanas | 1 sessão semanal (2h) |
| **Curso autônomo virtual** | Flexível | Módulos independentes |

---

## Organização das Sessões (Workshop Intensivo)

| Sessão | Horas | Módulo | Atividade-chave |
|---|---|---|---|
| 1 | 4h | Conceitos SIG | Exploração do QGIS + questionário |
| 2 | 4h | Amazônia territorial | Mapa base + análise GFW |
| 3 | 4h | Python | Cálculo de NDVI no Jupyter |
| 4 | 4h | Projeto Final | Análise e apresentação |

---

## Requisitos Técnicos para a Sala de Aula

**Hardware:**
- Computadores com no mínimo 8 GB de RAM e 50 GB livres em disco
- Conexão estável com a internet (para download de dados)

**Software a ser instalado previamente:**
```
✓ QGIS 3.x LTR (qgis.org)
✓ Python 3.11 (python.org)
✓ Anaconda/Miniforge (para ambientes conda)
✓ Jupyter Notebook
✓ GeoPandas, Rasterio, Folium (via conda ou pip)
```

**Recomendação:** Prepare um instalador portátil ou imagem de disco com tudo configurado para evitar problemas no início das sessões.

---

## Considerações Didáticas por Módulo

### Módulo 1 (SIG):
- Comece com uma **pergunta provocadora**: *Por que um mapa de papel não é suficiente para analisar o desmatamento?*
- Use comparações visuais entre mapas analógicos e SIG

### Módulo 2 (Amazônia):
- Projete notícias recentes sobre a Amazônia no início
- Fomente o debate sobre perspectivas indígenas vs. estatais

### Módulo 3 (Python):
- Os estudantes com menos experiência podem seguir o código passo a passo sem entender tudo
- Enfatize que **automatizar = reprodutibilidade científica**

### Módulo 4 (Prática QGIS):
- Trabalhe em duplas para reduzir a frustração técnica
- Prepare uma tela espelho para que os estudantes acompanhem em seus computadores

---

## Checklist do Docente — Preparação do Workshop

**48 horas antes:**
- [ ] Instalar e testar todo o software nos computadores da sala de aula
- [ ] Baixar previamente todos os dados geoespaciais (podem ser pesados)
- [ ] Preparar uma pasta compartilhada (USB ou rede local) com todos os dados
- [ ] Revisar os módulos dos estudantes para antecipar perguntas

**No início do Workshop:**
- [ ] Distribuir a pasta de dados para todos os estudantes
- [ ] Verificar se o QGIS abre corretamente em todas as máquinas
- [ ] Fazer um teste rápido de importação de um shapefile

---

[🏠 Voltar ao Índice](../README.md) | [➡️ Marco Teórico](01_marco_teorico.md)
