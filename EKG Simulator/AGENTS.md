# AGENTS.md

## Projeto

`EKG Simulator` e um simulador vetorial de ECG com backend em `FastAPI` e frontend estatico servido pelo proprio backend.

O estado atual do projeto e:
- backend funcional em Python
- frontend funcional em HTML/CSS/JS com Plotly
- script legado `ekg_simulator.py` mantido como referencia de notebook/Colab

## Objetivo Atual

A aplicacao permite:
- configurar um vetor de injuria em 3D
- aplicar esse vetor ao segmento ST no backend
- visualizar:
  - vetor 3D
  - zona cega do ECG de 12 derivacoes
  - bullseye AHA
  - barplot de lesao segmentar
  - polaridade/projecao nas derivacoes
  - ECG de 12 derivacoes

## Estrutura

- `backend/app/main.py`
  Entrada FastAPI. Serve a API e tambem monta `frontend/` em `/app`.

- `backend/app/api/routes/simulation.py`
  Endpoint principal:
  - `GET /simulation/health`
  - `GET /simulation/meta`
  - `POST /simulation`

- `backend/app/domain/geometry.py`
  Funcoes geometricas basicas.

- `backend/app/domain/leads.py`
  Vetores das derivacoes e metadados AHA.

- `backend/app/domain/waves.py`
  Gera componentes de onda (P, QRS, ST, T).

- `backend/app/domain/simulator.py`
  Nucleo do simulador.
  Faz:
  - vetor basal
  - aplicacao do vetor de injuria
  - projecao nas derivacoes
  - dano segmentar

- `backend/app/services/simulation_service.py`
  Camada fina de servico sobre o simulador.

- `backend/app/schemas/simulation.py`
  Schemas Pydantic de entrada e saida.

- `frontend/index.html`
  Estrutura dos paineis da UI.

- `frontend/styles.css`
  Layout em duas colunas:
  - esquerda: controles do vetor
  - direita: graficos

- `frontend/app.js`
  Toda a logica do frontend:
  - controles angulares
  - presets
  - modelos OMI
  - chamadas `fetch` para a API
  - renderizacao Plotly
  - calculo da zona cega no frontend

- `backend/references/omi_sem_supra_principais_padroes.txt`
  Referencia textual usada para derivar os modelos OMI do frontend.

- `backend/legacy/ekg_simulator.py`
  Script legado exportado de notebook.
  Nao e a fonte principal da aplicacao atual, mas ainda serve como referencia de experimentos antigos.

## Fluxo de Dados

1. O frontend calcula `x, y, z` a partir de:
   - angulo frontal
   - angulo horizontal
   - magnitude

2. O frontend envia `POST /simulation` com:
   - `x`
   - `y`
   - `z`
   - `st_gain`

3. O backend responde com:
   - `input_vector`
   - `vector_loop`
   - `ecg`
   - `lead_projection`
   - `damage_segments`
   - outros dados auxiliares

4. O frontend usa isso para desenhar os graficos.

## Regras Importantes

- A API atual deve continuar estavel. Prefira mudar o frontend sem quebrar o contrato de `POST /simulation`.
- A "zona cega" atual significa:
  tudo que nao e visto pelo ECG padrao de 12 derivacoes.
- O grafico de polaridade das derivacoes foi travado como fixo, sem zoom/pan.
- Os modelos OMI sao heuristicas didaticas derivadas de `backend/references/omi_sem_supra_principais_padroes.txt`.

## Como Rodar

Na raiz de `EKG Simulator`:

```bash
source .venv/bin/activate
cd backend
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

UI local:

```text
http://127.0.0.1:8000/app/
```

## Verificacoes Uteis

Sintaxe do frontend:

```bash
node --check frontend/app.js
```

Teste rapido da API:

```bash
curl -s -X POST http://127.0.0.1:8000/simulation \
  -H 'Content-Type: application/json' \
  -d '{"x":0.3,"y":0.8,"z":-0.4,"st_gain":0.25}'
```

## O Que Nao Fazer Sem Necessidade

- Nao migrar para React/Next sem pedido explicito.
- Nao apagar `backend/legacy/ekg_simulator.py`; ele ainda e referencia util.
- Nao alterar os vetores dos modelos OMI sem atualizar a logica/preset correspondente no frontend.
