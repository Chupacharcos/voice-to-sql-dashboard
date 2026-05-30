"""seed_db.py — genera artifacts/saas_demo.db con datos realistas.

Tres tablas tipo SaaS:
  - clientes: 200 empresas con plan + fecha alta + país
  - productos: 8 planes/módulos (precio, tier)
  - ventas: 5000 transacciones (cliente_id, producto_id, fecha, importe, MRR)

Dataset suficiente para consultas tipo:
  "ventas por país en los últimos 3 meses"
  "top 5 clientes por MRR"
  "evolución de churn por plan"
"""
from __future__ import annotations
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

DB_PATH = Path(__file__).parent / "artifacts" / "saas_demo.db"
DB_PATH.parent.mkdir(exist_ok=True)
if DB_PATH.exists():
    DB_PATH.unlink()

con = sqlite3.connect(DB_PATH)
con.executescript("""
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    pais TEXT NOT NULL,
    sector TEXT NOT NULL,
    plan TEXT NOT NULL CHECK(plan IN ('free','starter','pro','enterprise')),
    fecha_alta DATE NOT NULL,
    activo INTEGER DEFAULT 1
);

CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    tier TEXT NOT NULL CHECK(tier IN ('addon','core','premium')),
    precio_mensual REAL NOT NULL
);

CREATE TABLE ventas (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    importe REAL NOT NULL,
    mrr_aporte REAL NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_ventas_cliente ON ventas(cliente_id);
CREATE INDEX idx_clientes_plan ON clientes(plan);
CREATE INDEX idx_clientes_pais ON clientes(pais);
""")

PAISES = ["España", "Francia", "Italia", "Alemania", "Reino Unido",
          "Portugal", "México", "Argentina", "Chile", "Colombia"]
SECTORES = ["E-commerce", "SaaS", "FinTech", "EdTech", "HealthTech",
            "MarTech", "PropTech", "AgriTech"]
PLANES = [("free", 0), ("starter", 29), ("pro", 99), ("enterprise", 499)]

# Productos
PRODUCTOS = [
    ("Plan Free",        "core",    0),
    ("Plan Starter",     "core",    29),
    ("Plan Pro",         "core",    99),
    ("Plan Enterprise",  "core",    499),
    ("Add-on Analytics", "addon",   19),
    ("Add-on API Plus",  "addon",   39),
    ("Add-on White Label","premium", 149),
    ("Add-on Priority Support","premium", 79),
]
con.executemany(
    "INSERT INTO productos (nombre, tier, precio_mensual) VALUES (?, ?, ?)",
    PRODUCTOS,
)

# Clientes (200)
nombres_empresa = [
    "Acme", "Globex", "Initech", "Umbrella", "Stark", "Wayne", "Pied Piper",
    "Hooli", "Soylent", "Cyberdyne", "Massive", "Tyrell", "Weyland",
    "Aperture", "Black Mesa", "Oscorp", "LexCorp", "Wonka", "Vandelay",
    "Bluth", "Dunder Mifflin", "Sterling Cooper", "Buy n Large", "Octan",
]
sufijos = ["Tech", "Labs", "Group", "Solutions", "Systems", "Digital",
           "Innovations", "Studio", "Network", "Cloud"]
hoy = datetime.now().date()
for i in range(1, 201):
    nombre = f"{random.choice(nombres_empresa)} {random.choice(sufijos)} {i}"
    pais = random.choice(PAISES)
    sector = random.choice(SECTORES)
    plan = random.choices(PLANES, weights=[0.4, 0.3, 0.2, 0.1])[0][0]
    dias_atras = random.randint(7, 730)  # último 2 años
    fecha = (hoy - timedelta(days=dias_atras)).isoformat()
    activo = 1 if random.random() > 0.12 else 0  # ~12% churn
    con.execute(
        "INSERT INTO clientes (nombre, pais, sector, plan, fecha_alta, activo) VALUES (?,?,?,?,?,?)",
        (nombre, pais, sector, plan, fecha, activo),
    )

# Ventas (~5000)
producto_precios = {p[0]: p[2] for p in PRODUCTOS}
producto_ids = list(range(1, len(PRODUCTOS) + 1))
ventas = []
for _ in range(5000):
    cliente_id = random.randint(1, 200)
    producto_id = random.choice(producto_ids)
    precio_base = list(producto_precios.values())[producto_id - 1]
    # Variabilidad por descuentos
    importe = round(precio_base * random.uniform(0.85, 1.0), 2)
    mrr = importe  # asumimos suscripción mensual
    dias_atras = random.randint(1, 365)
    fecha = (hoy - timedelta(days=dias_atras)).isoformat()
    ventas.append((cliente_id, producto_id, fecha, importe, mrr))

con.executemany(
    "INSERT INTO ventas (cliente_id, producto_id, fecha, importe, mrr_aporte) VALUES (?,?,?,?,?)",
    ventas,
)
con.commit()

# Verificación
cur = con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
ven = con.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
print(f"Seed OK → {DB_PATH}")
print(f"  clientes: {cur}")
print(f"  ventas: {ven}")
print(f"  productos: {len(PRODUCTOS)}")
print(f"  tamaño: {DB_PATH.stat().st_size // 1024} KB")
con.close()
