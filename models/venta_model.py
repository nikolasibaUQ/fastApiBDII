from pydantic import BaseModel
from typing import List

class ProductoRequest(BaseModel):
    idProducto: int
    cantidad: int

class VentaRequest(BaseModel):
    fechaVenta: str
    valor: float
    idAfiliado: str
    listaProductos: List[ProductoRequest]
