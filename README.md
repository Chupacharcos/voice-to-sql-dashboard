# 🗣️→🗄️ Voice-to-SQL Dashboard

Pregúntale a tu base de datos en **lenguaje natural** (por voz o texto). Un LLM (**Llama 3.3 70B** vía Groq) traduce tu pregunta a SQL, valida que sea de **solo lectura** y la ejecuta. Sin escribir una línea de SQL.

[![Probar demo](https://img.shields.io/badge/▶_Probar_demo-en_vivo-64ffda?style=for-the-badge)](https://adrianmoreno-dev.com/demo/voice-to-sql-dashboard)
[![Hugging Face](https://img.shields.io/badge/🤗_Space-Gradio-yellow?style=for-the-badge)](https://huggingface.co/spaces/Chupacharcos/voice-to-sql)

![preview](https://adrianmoreno-dev.com/og/proyecto/voice-to-sql-dashboard.png)

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
