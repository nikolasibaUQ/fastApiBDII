from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Crear la instancia de la aplicación FastAPI
app = FastAPI(title="API Multinivel", description="API para manejar afiliados y usuarios", version="1.0")

#TODO: aqui pone sus propias credenciales  
# Conexión a la base de datos
#aqui va las credenciales de la base de datos
DATABASE_URL = "mysql+pymysql://root:contrasena@127.0.0.1:3306/multinivelDB"
engine = create_engine(DATABASE_URL, future=True)  # Usar modo futuro para compatibilidad con _mapping
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint básico que retorna "Hola Mundo"
@app.get("/")
async def read_root():
    return {"message": "Hola Mundo"}

# Endpoint para probar la conexión a la base de datos
@app.get("/db-status")
async def db_status():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DATABASE()"))
            database_name = result.fetchone()[0]
        return {"message": "Conexión exitosa", "database": database_name}
    except Exception as e:
        return {"message": "Error al conectar a la base de datos", "error": str(e)}

# Endpoint para obtener la lista de usuarios
@app.get("/users/join")
async def get_users_with_city(db: Session = Depends(get_db)):
    try:
        sql = """
        SELECT a.nombre, a.email, c.nombreCiudad
        FROM afiliado a
        INNER JOIN ciudad c ON a.id_ciudad = c.idCiudad;
        """
        result = db.execute(text(sql))
        print(result)
        users = [{"nombre": row[0], "email": row[1], "ciudad": row[2]} for row in result]
        return {"users": users}
    except Exception as e:
        return {"message": "Error al obtener los usuarios con ciudad", "error": str(e)}

