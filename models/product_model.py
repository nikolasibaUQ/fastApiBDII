from pydantic import BaseModel

class ProductRequest(BaseModel):
    idProducto: int
    nombre: str
    descripcion: str
    precio: float
    idInventario: int
    idAfiliado: str
