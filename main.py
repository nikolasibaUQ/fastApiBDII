from fastapi import FastAPI
from procedures import create_procedures_and_triggers
from endpoints.affiliates_ep import router as affiliates_router
from endpoints.inventory_ep import router as inventory_router
from endpoints.ventas_ep import router as ventas_router


# Crear la instancia de la aplicación FastAPI
app = FastAPI(
    title="API Multinivel",
    description="API para manejar afiliados y usuarios",
    version="1.0"
)

# Inicializar procedimientos almacenados
create_procedures_and_triggers()

# Registrar routers de funcionalidades
app.include_router(affiliates_router, prefix="/affiliates", tags=["Affiliates"])
app.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])
app.include_router(ventas_router, prefix="/ventas", tags=["ventas"])



@app.get("/")
async def read_root():
    return {"message": "Hola Mundo"}
