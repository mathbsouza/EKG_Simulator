# EKG_Simulator

Simulador visual de ECG/ECG vetorial em Python, com projeção em derivações, visualização 3D do espaço vetorial cardíaco e experimentos de padrões isquêmicos.

## O que existe hoje

- Geração de vetor cardíaco sintético ao longo do tempo
- Projeção nas 12 derivações do ECG
- Visualizações 3D com Plotly
- Explorações de STEMI, T hiperaguda e mapas vetoriais
- Elementos interativos com `ipywidgets`
- Backend modular inicial para futura interface web

## Estrutura

- `backend/app/domain`: núcleo matemático e vetorial separado em módulos
- `backend/app/services`: camada de serviço para a simulação
- `backend/app/api/routes`: endpoints da API web
- `backend/app/main.py`: entrada FastAPI
- `frontend`: interface web estática servida pelo backend
- `backend/references/omi_sem_supra_principais_padroes.txt`: referência dos modelos OMI
- `backend/legacy/ekg_simulator.py`: script original exportado de notebook, mantido só como legado

## Backend web

O backend novo já expõe a base para:

- receber um vetor 3D escolhido pelo usuário
- aplicar esse vetor como injúria no segmento ST sobre o vetor basal
- retornar loop vetorial, ECG em 12 derivações e barplot de dano por 17 segmentos AHA

Execução sugerida:

```bash
cd backend
uvicorn app.main:app --reload
```

Abra no navegador:

```text
http://127.0.0.1:8000/dev
```

Essa rota ativa recarga automática no browser quando você alterar arquivos `frontend/*.html`, `frontend/*.css`, `frontend/*.js` ou `backend/app/*.py`, o que permite ajustar as derivações e ver o resultado ao vivo.

Endpoint principal:

```text
POST /simulation
```

Payload de exemplo:

```json
{
  "x": 0.3,
  "y": 0.8,
  "z": -0.4,
  "st_gain": 0.25
}
```

## Observação importante

O arquivo legado agora está em `backend/legacy/ekg_simulator.py`. Ele ainda veio de um ambiente tipo Colab/notebook e contém comandos compatíveis com notebook, como `!pip install ...`. A lógica real do projeto está em `backend/app`.

## Dependências

As dependências principais estão em `requirements.txt`.

Instalação sugerida:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Próximos passos recomendados

- Implementar o frontend React/Next.js consumindo `POST /simulation`
- Migrar o bullseye visual para um componente web dedicado
- Adicionar testes para geometria, projeção e regra de injúria
- Remover do script legado os blocos já absorvidos pelo backend
