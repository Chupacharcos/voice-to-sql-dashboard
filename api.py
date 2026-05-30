"""api.py — backend FastAPI para Voice-to-SQL Dashboard.
Generado por _stub_backend (fallback determinista) cuando el LLM
no logró producir un backend completo. Implementa los endpoints
declarados en la spec con respuestas demo realistas.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router

app = FastAPI(title="Voice-to-SQL Dashboard", description='Este proyecto es un panel analítico inteligente que elimina por completo la fricción del usuario a la hora de consultar e interpretar datos complejos. El sistema permite interactuar mediante lenguaje ')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "voice-to-sql-dashboard", "port": 8007}
