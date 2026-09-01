"""router.py — Voice-to-SQL Dashboard.

Flujo:
  1. Frontend captura voz (Web Speech API nativa del browser) → texto
  2. POST /demo/voice-to-sql-dashboard/query con {"question": str}
  3. Backend usa Groq LLaMA 3.3 70b para generar SQL a partir del texto
  4. Safety: solo SELECT permitido; cualquier otra cosa rechazada (400)
  5. Ejecuta SQL contra SQLite local + devuelve columnas + filas
"""
from __future__ import annotations
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ── Config ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
DB_PATH = ROOT / "artifacts" / "saas_demo.db"

# Carga GROQ_API_KEY desde /var/www/neuralops/.env si no está en el env del proceso
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    try:
        env_path = Path("/var/www/neuralops/.env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("GROQ_API_KEY="):
                    GROQ_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except Exception:
        pass

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# 2026-09-01: Groq retiró la familia Llama (404 model_not_found). Modelos
# DISTINTOS a los de los agentes de NeuralOps (openai/gpt-oss-*): el límite de
# tokens/minuto es por modelo, así que separarlos evita que una tarea de fondo
# deje sin cuota a un visitante.
# Cadena: qwen3.8 primero (mejor SQL), si 429 cae a compound-mini. Si el
# segundo también está saturado, devolvemos 503 al frontend con mensaje claro.
GROQ_MODELS = ["qwen/qwen3.8-27b", "groq/compound-mini"]
MAX_ROWS = 100  # cap absoluto al resultado para que el frontend lo renderice bien

# Esquema fijo inyectado en el prompt del LLM
SCHEMA_DESC = """
TABLAS DISPONIBLES (esquema exacto, NO inventar columnas):

clientes (200 filas)
  - id INTEGER PRIMARY KEY
  - nombre TEXT                  -- nombre comercial
  - pais TEXT                    -- "España"|"Francia"|"Italia"|"Alemania"|"Reino Unido"|"Portugal"|"México"|"Argentina"|"Chile"|"Colombia"
  - sector TEXT                  -- "E-commerce"|"SaaS"|"FinTech"|"EdTech"|"HealthTech"|"MarTech"|"PropTech"|"AgriTech"
  - plan TEXT                    -- "free"|"starter"|"pro"|"enterprise"
  - fecha_alta DATE              -- ISO YYYY-MM-DD
  - activo INTEGER               -- 1=activo, 0=churn

productos (8 filas)
  - id INTEGER PRIMARY KEY
  - nombre TEXT                  -- "Plan Free"|"Plan Starter"|"Plan Pro"|"Plan Enterprise"|"Add-on Analytics"|"Add-on API Plus"|"Add-on White Label"|"Add-on Priority Support"
  - tier TEXT                    -- "addon"|"core"|"premium"
  - precio_mensual REAL          -- en EUR

ventas (5000 filas, último año)
  - id INTEGER PRIMARY KEY
  - cliente_id INTEGER → clientes.id
  - producto_id INTEGER → productos.id
  - fecha DATE                   -- ISO YYYY-MM-DD
  - importe REAL                 -- EUR pagados
  - mrr_aporte REAL              -- contribución MRR

REGLAS:
- SQLite dialect (NOT PostgreSQL/MySQL).
- Para "últimos N meses" usa: date('now', '-N months')
- Para agrupar por mes: strftime('%Y-%m', fecha)
- Si la pregunta es ambigua, asume la interpretación más útil para un dashboard analítico.
""".strip()

SYSTEM_PROMPT = (
    "Eres un experto en SQLite que convierte preguntas en lenguaje natural "
    "en consultas SQL ejecutables. Responde ÚNICAMENTE con la consulta SQL, "
    "sin explicación, sin markdown, sin punto y coma final, sin prefijos.\n\n"
    f"{SCHEMA_DESC}\n\n"
    "REGLA CRÍTICA: solo SELECT. Nunca UPDATE/INSERT/DELETE/DROP."
)

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int
    truncated: bool
    duration_ms: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/demo/voice-to-sql-dashboard/schema")
def get_schema():
    """Esquema + datos de muestra para que el frontend sugiera ejemplos."""
    if not DB_PATH.exists():
        raise HTTPException(503, "Base de datos no inicializada. Ejecuta seed_db.py")
    sugerencias = [
        "Cuántos clientes activos tenemos por país",
        "Top 5 clientes por MRR total del último mes",
        "Ventas totales por sector ordenadas de mayor a menor",
        "Evolución mensual de ingresos en los últimos 6 meses",
        "Tasa de churn por plan",
        "Producto más vendido en los últimos 30 días",
    ]
    with sqlite3.connect(DB_PATH) as con:
        muestra = {}
        for tabla in ("clientes", "productos", "ventas"):
            cur = con.execute(f"SELECT * FROM {tabla} LIMIT 3")
            cols = [d[0] for d in cur.description]
            rows = [list(r) for r in cur.fetchall()]
            muestra[tabla] = {"columnas": cols, "filas": rows}
    return {
        "tablas": ["clientes", "productos", "ventas"],
        "esquema_humano": SCHEMA_DESC,
        "muestra": muestra,
        "ejemplos_preguntas": sugerencias,
    }


@router.post("/demo/voice-to-sql-dashboard/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """Recibe pregunta → genera SQL con Groq → ejecuta en SQLite → devuelve filas."""
    if not GROQ_API_KEY:
        raise HTTPException(503, "GROQ_API_KEY no configurada en el servidor")
    if not DB_PATH.exists():
        raise HTTPException(503, "Base de datos no inicializada")

    t0 = time.time()
    sql_raw = _generate_sql(req.question)
    sql_clean = _sanitize_sql(sql_raw)
    columns, rows, truncated = _execute_select(sql_clean)
    return QueryResponse(
        question=req.question,
        sql=sql_clean,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
        duration_ms=int((time.time() - t0) * 1000),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_sql(question: str) -> str:
    """Llama a Groq para generar SQL. Itera por GROQ_MODELS hasta encontrar
    uno con cuota. Si todos rate-limitan, devuelve 503 con mensaje claro
    (en vez de un 502 críptico)."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}",
               "Content-Type": "application/json"}
    last_err = ""
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            "temperature": 0.1,
            "max_tokens": 400,
        }
        try:
            r = httpx.post(GROQ_URL, json=payload, headers=headers, timeout=30)
            if r.status_code == 429:
                last_err = f"{model} rate-limited"
                continue  # probar el siguiente modelo
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
            # Limpiar markdown si lo metió
            text = re.sub(r"^```sql\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
            text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
            return text.strip().rstrip(";")
        except Exception as e:
            last_err = f"{model}: {type(e).__name__}"
            continue
    raise HTTPException(
        503,
        f"Groq sin cuota disponible ahora mismo. Intenta de nuevo en 1-2 min "
        f"(probados: {', '.join(GROQ_MODELS)}). Último: {last_err}"
    )


def _sanitize_sql(sql: str) -> str:
    """Safety guard: solo permitir SELECT (y CTEs WITH...SELECT).
    Rechaza statements múltiples o de escritura."""
    if ";" in sql.rstrip(";"):
        raise HTTPException(400, "Múltiples sentencias SQL no permitidas")
    head = sql.lstrip().lower()
    if not (head.startswith("select") or head.startswith("with")):
        raise HTTPException(400, f"Solo SELECT permitido. Recibido: {sql[:60]}...")
    forbidden = ("insert ", "update ", "delete ", "drop ", "alter ", "create ",
                 "pragma ", "attach ", "detach ", "vacuum ", "replace ")
    low = " " + sql.lower() + " "
    for kw in forbidden:
        if kw in low:
            raise HTTPException(400, f"Operación '{kw.strip()}' no permitida")
    return sql.strip()


def _execute_select(sql: str) -> tuple[list[str], list[list], bool]:
    """Ejecuta el SELECT contra la BD y trunca a MAX_ROWS."""
    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            all_rows = cur.fetchmany(MAX_ROWS + 1)
    except sqlite3.Error as e:
        raise HTTPException(400, f"SQL inválido: {str(e)[:150]}")
    truncated = len(all_rows) > MAX_ROWS
    rows = all_rows[:MAX_ROWS]
    def _norm(v):
        if isinstance(v, (bytes, bytearray)):
            return v.decode("utf-8", errors="replace")
        return v
    rows = [[_norm(c) for c in r] for r in rows]
    return columns, rows, truncated
