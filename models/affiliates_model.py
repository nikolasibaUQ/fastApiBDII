from pydantic import BaseModel
from typing import Optional

class CreateAffiliateRequest(BaseModel):
    id_afiliado: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    direccion: str
    fechaRegistro: str
    idCiudad: int
    username: str
    password: str
    codigoReferido: Optional[str] = None
