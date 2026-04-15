# Frontend

Base planejada para o app web bonito.

## Componentes sugeridos

- `ControlPanel`: sliders de azimute, elevação, magnitude e ganho do supra de ST
- `VectorScene`: cena 3D em tempo real com vetor, leads e loop vetorial
- `DamageBars`: barplot dos 17 segmentos AHA
- `BullseyeMap`: mapa polar do dano
- `ECGPanel`: 12 derivações em grade

## Stack recomendada

- `Next.js` ou `Vite + React`
- `plotly.js` para os gráficos
- `zustand` ou estado local simples para sincronizar controles e gráficos
- CSS com tokens visuais próprios, evitando layout genérico de dashboard
