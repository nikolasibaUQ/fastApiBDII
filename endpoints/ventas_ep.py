from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from database import engine  # Asegúrate de tener este archivo configurado
from models.venta_model import VentaRequest
import json

router = APIRouter()

@router.post("/ventas")
def registrar_venta(venta: VentaRequest):
    """
    Endpoint para registrar una venta. Maneja múltiples productos y valida stock.
    """
    try:
        with engine.connect() as connection:
            # Validar si hay stock suficiente para cada producto
            for producto in venta.listaProductos:
                id_producto = producto.idProducto
                cantidad_solicitada = producto.cantidad
                
                query_stock = text("""
                    SELECT cantidad
                    FROM Producto
                    WHERE idProducto = :idProducto
                """)
                stock_actual = connection.execute(query_stock, {"idProducto": id_producto}).scalar()

                if stock_actual is None:
                    raise HTTPException(status_code=400, detail=f"El producto con ID {id_producto} no existe.")

                if stock_actual < cantidad_solicitada:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Stock insuficiente para el producto con ID {id_producto}. Stock disponible: {stock_actual}, solicitado: {cantidad_solicitada}"
                    )

            # Preparar los datos de la venta
            lista_productos = [{"idProducto": p.idProducto, "cantidad": p.cantidad} for p in venta.listaProductos]
            
            query = text("""
                CALL RegistrarVenta(
                    :fechaVenta,
                    :valor,
                    :idAfiliado,
                    :listaProductos
                )
            """)

            connection.execute(query, {
                "fechaVenta": venta.fechaVenta,
                "valor": venta.valor,
                "idAfiliado": venta.idAfiliado,
                "listaProductos": json.dumps(lista_productos)  # Convertir lista de productos a JSON
            })

            return {"message": "Venta registrada exitosamente."}

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
