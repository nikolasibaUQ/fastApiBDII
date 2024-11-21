from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models.product_model import ProductRequest

router = APIRouter(tags=["Inventory"])

@router.post("/add", summary="Add Product")
async def add_product(request: ProductRequest, db: Session = Depends(get_db)):
    """
    Endpoint para agregar un producto al inventario.
    Solo el afiliado principal puede realizar esta operación.
    """
    try:
        # Llamar al procedimiento almacenado para validar y agregar el producto
        sql = text("""
            CALL CrearProducto(:idProducto, :nombre, :descripcion, :precio,
                               :idInventario, :idAfiliado)
        """)
        db.execute(sql, {
            "idProducto": request.idProducto,
            "nombre": request.nombre,
            "descripcion": request.descripcion,
            "precio": request.precio,
            "idInventario": request.idInventario,
            "idAfiliado": request.idAfiliado
        })
        db.commit()
        return {"message": "Producto añadido exitosamente al inventario."}
    except Exception as e:
        return {"error": str(e)}


@router.post("/delete-product", summary="Logical Delete Product")
async def delete_product(
    idProducto: int, idAfiliado: str, db: Session = Depends(get_db)
):
    """
    Endpoint para realizar la eliminación lógica de un producto. Solo permitido para afiliados de nivel 1.
    """
    try:
        sql = text("""
            CALL EliminarProducto(:p_idProducto, :p_idAfiliado)
        """)
        db.execute(sql, {"p_idProducto": idProducto,
                   "p_idAfiliado": idAfiliado})
        db.commit()
        return {"message": "Producto marcado como eliminado exitosamente"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/list", summary="List Products")
async def list_products(idAfiliado: str, db: Session = Depends(get_db)):
    """
    Endpoint para listar todos los productos en el inventario.
    Solo el afiliado principal puede realizar esta operación.
    """
    try:
        sql = text("""
            CALL ListarProductos(:idAfiliado)
        """)
        result = db.execute(sql, {"idAfiliado": idAfiliado}).fetchall()
        products = [
            {
                "idProducto": row[0],
                "nombre": row[1],
                "descripcion": row[2],
                "precio": row[3],
                "cantidad": row[4],

            } for row in result
        ]
        return {"products": products}
    except Exception as e:
        return {"error": str(e)}
