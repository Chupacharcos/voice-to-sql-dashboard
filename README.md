# Voice-to-SQL Dashboard

Demo de un dashboard donde haces preguntas en lenguaje natural (texto o voz) y
obtienes los resultados como tabla. El LLM convierte la pregunta a SQL, la API
lo ejecuta contra una base SQLite local y devuelve filas + columnas.

## Stack

- **Backend**: FastAPI + httpx
- **LLM**: Groq (`llama-3.3-70b-versatile` con fallback a `llama-3.1-8b-instant`)
- **BD**: SQLite (3 tablas: clientes, productos, ventas)
- **Voz**: Web Speech API nativa del navegador (no requiere backend STT)

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/demo/voice-to-sql-dashboard/schema` | Esquema + 6 ejemplos de preguntas |
| POST | `/demo/voice-to-sql-dashboard/query` | `{question}` → SQL + filas |

## Safety

`_sanitize_sql()` solo permite `SELECT` y CTEs `WITH ... SELECT`. Rechaza
`INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/PRAGMA/ATTACH/VACUUM/REPLACE` y
sentencias múltiples. Cap absoluto de 100 filas por respuesta.

## Setup local

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed_db.py           # genera artifacts/saas_demo.db
export GROQ_API_KEY=...
uvicorn api:app --host 127.0.0.1 --port 8007
```

## Producción

Corre como `voice-to-sql-dashboard.service` (systemd, puerto 8007). El portfolio
Laravel hace proxy desde `https://adrianmoreno-dev.com/demo/voice-to-sql-dashboard`.
