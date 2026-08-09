# 🗣️→🗄️ Voice-to-SQL Dashboard

Pregúntale a tu base de datos en **lenguaje natural** (por voz o texto). Un LLM (**Llama 3.3 70B** vía Groq) traduce tu pregunta a SQL, valida que sea de **solo lectura** y la ejecuta. Sin escribir una línea de SQL.

[![Probar demo](https://img.shields.io/badge/▶_Probar_demo-en_vivo-64ffda?style=for-the-badge)](https://adrianmoreno-dev.com/demo/voice-to-sql-dashboard)
[![Hugging Face](https://img.shields.io/badge/🤗_Space-Gradio-yellow?style=for-the-badge)](https://huggingface.co/spaces/Chupacharcos/voice-to-sql)

![preview](https://adrianmoreno-dev.com/og/proyecto/voice-to-sql-dashboard.png)

<!-- LOOP-MAP:START (generado por `php artisan project:loop readme` — no editar a mano) -->

## El bucle que cierra

<p align="center"><img src="https://adrianmoreno-dev.com/bucle/voice-to-sql-dashboard.svg" alt="Mapa del bucle de Voice-to-SQL Dashboard" width="900"></p>

**Para** alguien de negocio que necesita un dato y no sabe SQL · **En cada pregunta**

| Etapa | Qué pasa | Quién |
|---|---|---|
| **1. Disparador** | Necesito un dato de la base de datos y no sé escribir la consulta | persona |
| **2. Acción** | Traduce la pregunta (voz o texto) a SQL inyectando el esquema real y comprueba que sea de solo lectura | software |
| **3. Medición** | La tabla de resultados y el SQL generado, con tope de 100 filas | software |
| **4. Decisión** | Decido si el dato responde a mi duda o reformulo la pregunta | persona |

### Lo que no hace

- No modifica datos: bloquea INSERT, UPDATE, DELETE, DROP y las sentencias múltiples.
- No se conecta a bases de producción: la demo trae una SQLite de ejemplo generada por seed\_db.py.
- No dibuja gráficas ni informes: devuelve la tabla y el SQL que la ha producido.

### Por qué está construido así

- **Web Speech API del navegador** en vez de transcribir el audio en el servidor — La voz se convierte a texto en el propio navegador: el audio no sale del equipo y no hay coste por minuto de transcripción.
- **Solo SELECT y WITH** en vez de ejecutar el SQL del modelo tal cual — El modelo se equivoca; la validación rechaza escrituras y sentencias múltiples antes de tocar la base.

<!-- LOOP-MAP:END -->

## ✨ Qué hace
- **Voz → texto** en el navegador (Web Speech API, coste cero).
- **Texto → SQL** con Groq + Llama 3.3 70B, inyectando el esquema real de la BD.
- **Seguridad**: solo `SELECT`/`WITH`; bloquea INSERT/UPDATE/DELETE/DROP y sentencias múltiples. Tope de 100 filas.
- Muestra el **SQL generado** + la tabla de resultados.

## ⚡ Quickstart (30 s)
```bash
pip install -r requirements.txt
python seed_db.py            # genera la BD SaaS de ejemplo (200 clientes, 5000 ventas)
export GROQ_API_KEY=tu_key   # gratis en groq.com
uvicorn api:app --port 8007
```
O pruébalo sin instalar nada en el [🤗 Space](https://huggingface.co/spaces/Chupacharcos/voice-to-sql).

## 🧱 Stack
FastAPI · Groq (Llama 3.3 70B) · SQLite · Web Speech API · Vanilla JS

## 📝 Cómo lo construí
Artículo técnico: [Voice-to-SQL: hablarle a tu base de datos con un LLM](https://adrianmoreno-dev.com/blog/voice-to-sql-hablarle-a-tu-base-de-datos-con-un-llm)

---
Proyecto open source de [Adrián Moreno](https://adrianmoreno-dev.com). Úsalo libremente citando la fuente.
