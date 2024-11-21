from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models.affiliates_model import CreateAffiliateRequest
from models.login_model import LoginRequest

router = APIRouter()

# EndPoint para iniciar sesion
# EndPoint para iniciar sesion
@router.post("/login", summary="Login User")
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint para iniciar sesión con username y password.
    """
    try:
        # Consulta para obtener el usuario
        sql = text("""
            SELECT 
            id, nombre, apellido, email, telefono, direccion, idCiudad, password
            FROM Afiliado
            WHERE username = :username
        """)
        result = db.execute(sql, {"username": request.username}).fetchone()

        # Verificar si el usuario existe
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        id , name, lastName,email , phone, street, ciudad, password  = result

        # Validar la contraseña
        if password != request.password:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        return { "data":  {
        "message": "Bienvenido",
        "id": id,
        "name": name,
        "lastName": lastName,
        "email": email,
        "phone": phone,
        "street": street,
        "ciudad": ciudad
        }
    }

    except HTTPException as e:
        # Maneja excepciones de FastAPI (404 o 401)
        raise e
    except Exception as e:
        # Maneja otros errores (base de datos, lógica, etc.)
        return {"error": "Ocurrió un error inesperado", "details": str(e)}


@router.post("/create-affiliate", summary="Create Affiliate")
async def create_affiliate(
    request: CreateAffiliateRequest, db: Session = Depends(get_db)
):
    """
    Endpoint unificado para crear afiliados:
    - Si no se envía codigoReferido, crea el afiliado fundador.
    - Si se envía codigoReferido, crea un afiliado referenciado.
    """
    try:
        # Llamar al procedimiento con los datos proporcionados
        sql = text("""
            CALL CrearAfiliado(
                :id_afiliado, :nombre, :apellido, :email, 
                :telefono, :direccion, :fechaRegistro, 
                :idCiudad, :username, :password, :codigoReferido
            )
        """)
        db.execute(sql, {
            "id_afiliado": request.id_afiliado,
            "nombre": request.nombre,
            "apellido": request.apellido,
            "email": request.email,
            "telefono": request.telefono,
            "direccion": request.direccion,
            "fechaRegistro": request.fechaRegistro,
            "idCiudad": request.idCiudad,
            "username": request.username,
            "password": request.password,
            "codigoReferido": request.codigoReferido  # Puede ser NULL
        })
        db.commit()
        return {"message": "Afiliado creado exitosamente"}
    except Exception as e:
        return {"error": str(e)}
