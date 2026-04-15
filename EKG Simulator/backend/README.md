# Backend

Estrutura inicial para transformar o simulador em app web.

## Rodar

```bash
uvicorn app.main:app --reload
```

Use o endpoint `POST /simulation` com payload:

```json
{
  "x": 0.3,
  "y": 0.8,
  "z": -0.4,
  "st_gain": 0.25
}
```

Resposta:
- `vector_loop`: trajetória 3D do vetor com injúria
- `baseline_vector_loop`: trajetória basal
- `ecg`: sinais das 12 derivações principais
- `lead_projection`: projeção estática do vetor nas derivações
- `damage_segments`: intensidade de dano nos 17 segmentos AHA
