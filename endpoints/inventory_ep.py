from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models.product_model import ProductRequest

router = APIRouter(tags=["Inventory"])

@router.post("/add", summary="Add Product")
async def add_product(request: ProductRequest, db: Session = Depends(get_db)):
    """
    Endpoint para agregar un producto a tabla productos.
    Solo el afiliado principal puede realizar esta operación.
    """
    try:
        # Llamar al procedimiento almacenado para validar y agregar el producto
        sql = text("""
            CALL CrearProducto(:idProducto, :nombre, :descripcion, :precio,
                                :idAfiliado, :cantidad)
        """)
        db.execute(sql, {
            "idProducto": request.idProducto,
            "nombre": request.nombre,
            "descripcion": request.descripcion,
            "precio": request.precio,
            "idAfiliado": request.idAfiliado,
            "cantidad": request.cantidad
        })
        db.commit()
        return {"message": "Producto añadido exitosamente al listado de productos."}
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
async def list_products(db: Session = Depends(get_db)):
    """
    Endpoint para listar todos los productos en el listado de productos.
    Solo el afiliado principal puede realizar esta operación.
    """
    try:
        sql = text("""
            CALL ListarProductos()
        """)
        result = db.execute(sql).fetchall()
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

@router.put("/producto/{idProducto}", summary="Actualizar Producto")
async def actualizar_producto(
    producto: ProductRequest,  # Usamos tu modelo existente
    db: Session = Depends(get_db)
):
    """
    Endpoint para actualizar un producto. Solo puede ser usado por afiliados de nivel 1.
    """
    try:
        sql = text("""
            CALL ActualizarProducto(
                :p_idProducto, :p_nombre, :p_descripcion, :p_precio, :p_cantidad, :p_idAfiliado
            )
        """)
        db.execute(sql, {
            "p_idProducto": producto.idProducto,
            "p_nombre": producto.nombre,
            "p_descripcion": producto.descripcion,
            "p_precio": producto.precio,
            "p_cantidad": producto.cantidad,
            "p_idAfiliado": producto.idAfiliado
        })
        db.commit()
        return {"message": "Producto actualizado exitosamente"}
    except Exception as e:
        return {"error": str(e)}