from pydantic import BaseModel

class ProductRequest(BaseModel):
    idProducto: int
    nombre: str
    descripcion: str
    precio: float
    idAfiliado: str
    cantidad: int
