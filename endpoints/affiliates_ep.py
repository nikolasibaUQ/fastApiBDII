from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models.affiliates_model import CreateAffiliateRequest
from models.login_model import LoginRequest

router = APIRouter()

# EndPoint para iniciar sesion
@router.post("/login", summary="Login User")
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint para iniciar sesión con username y password.
    """
    try:
        # Consulta para obtener el usuario
        sql = text("""
            SELECT username, password
            FROM Afiliado
            WHERE username = :username
        """)
        result = db.execute(sql, {"username": request.username}).fetchone()

        # Verificar si el usuario existe
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        db_username, db_password = result

        # Validar la contraseña
        if request.password != db_password:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        return {"message": f"Bienvenido, {db_username}"}

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
