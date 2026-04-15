# EKG_Simulator

Simulador visual de ECG/ECG vetorial em Python, com projeção em derivações, visualização 3D do espaço vetorial cardíaco e experimentos de padrões isquêmicos.

## O que existe hoje

- Geração de vetor cardíaco sintético ao longo do tempo
- Projeção nas 12 derivações do ECG
- Visualizações 3D com Plotly
- Explorações de STEMI, T hiperaguda e mapas vetoriais
- Elementos interativos com `ipywidgets`

## Estrutura atual

- `ekg_simulator.py`: arquivo principal do projeto

## Observação importante

O arquivo atual foi exportado de um ambiente tipo Colab/notebook e ainda contém comandos compatíveis com notebook, como `!pip install ...`. Isso significa que ele pode precisar de uma pequena limpeza antes de rodar como script Python puro no terminal.

## Dependências

As dependências principais estão em `requirements.txt`.

Instalação sugerida:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Próximos passos recomendados

- Remover comandos específicos de notebook do script
- Separar o código em módulos menores
- Adicionar exemplos de uso e imagens no README
- Incluir testes para partes matemáticas do modelo
