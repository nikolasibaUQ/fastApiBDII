from sqlalchemy import text
from database import engine  # Asegúrate de que 'engine' está definido en 'database.py'

# Diccionario que contiene los procedimientos almacenados y triggers
PROCEDURES_AND_TRIGGERS = {

    # Procedimiento: Crear Afiliado 
"CrearAfiliado": {
    "drop": "DROP PROCEDURE IF EXISTS CrearAfiliado;",
    "create": """
        CREATE PROCEDURE CrearAfiliado(
            IN id_afiliado VARCHAR(16),
            IN nombre VARCHAR(255),
            IN apellido VARCHAR(32),
            IN email VARCHAR(200),
            IN telefono VARCHAR(45),
            IN direccion VARCHAR(45),
            IN fechaRegistro DATE,
            IN idCiudad INT,
            IN username VARCHAR(45),
            IN password VARCHAR(255),
            IN codigoReferido VARCHAR(45) -- Puede ser NULL
        )
        BEGIN
            DECLARE nivelSuperior INT;
            DECLARE idSuperior VARCHAR(16);
            DECLARE codigoReferidoGenerado VARCHAR(45);

            -- Verificar si es el fundador (no se envió codigoReferido y no existen afiliados)
            IF codigoReferido IS NULL THEN
                IF EXISTS (SELECT 1 FROM Afiliado) THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Ya existe un afiliado registrado. No se puede crear otro fundador.';
                END IF;

                -- Crear afiliado fundador
                SET codigoReferidoGenerado = 'FUNDADOR';

                INSERT INTO Afiliado (
                    id, nombre, apellido, email, telefono, direccion, fechaRegistro,
                    idCiudad, idSuperior, idNivel, username, password, codigoReferido, idEstadoAfiliado
                ) VALUES (
                    id_afiliado, nombre, apellido, email, telefono, direccion, fechaRegistro,
                    idCiudad, NULL, 1, username, password, codigoReferidoGenerado, 1
                );
            ELSE
                -- Validar el codigoReferido y obtener el idSuperior con el nivel más alto
                SELECT a.id, a.idNivel 
                INTO idSuperior, nivelSuperior
                FROM Afiliado a
                WHERE a.codigoReferido = CONCAT('REF-', codigoReferido) AND a.idEstadoAfiliado = 1
                ORDER BY a.idNivel DESC LIMIT 1;

                IF idSuperior IS NULL THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'El código de referido no es válido.';
                END IF;

                -- Asignar nivel al nuevo afiliado
                IF nivelSuperior >= 5 THEN
                    SET nivelSuperior = 5; -- Si el nivel del referidor es el más bajo, el nuevo afiliado también será nivel 5
                ELSE
                    SET nivelSuperior = nivelSuperior + 1; -- Nivel inmediatamente inferior
                END IF;

                -- Generar código de referido
                SET codigoReferidoGenerado = CONCAT('REF-', id_afiliado);

                -- Insertar el nuevo afiliado
                INSERT INTO Afiliado (
                    id, nombre, apellido, email, telefono, direccion, fechaRegistro,
                    idCiudad, idSuperior, idNivel, username, password, codigoReferido, idEstadoAfiliado
                ) VALUES (
                    id_afiliado, nombre, apellido, email, telefono, direccion, fechaRegistro,
                    idCiudad, idSuperior, nivelSuperior, username, password, codigoReferidoGenerado, 1
                );
            END IF;
        END;
    """
},


    # Procedimiento: Eliminar Producto
   "EliminarProducto": {
        "drop": "DROP PROCEDURE IF EXISTS EliminarProducto;",
        "create": """
        CREATE PROCEDURE EliminarProducto(
            IN p_idProducto INT,
            IN p_idAfiliado VARCHAR(16)
        )
        BEGIN
            DECLARE nivelAfiliado INT;
            DECLARE inventarioID INT;

            -- Validar que el afiliado es de nivel 1
            SELECT a.idNivel INTO nivelAfiliado
            FROM Afiliado a
            WHERE a.id = p_idAfiliado;

            IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
            END IF;

            -- Verificar que el producto existe y no está eliminado
            SELECT p.idInventario INTO inventarioID
            FROM Producto p
            WHERE p.idProducto = p_idProducto AND p.isEliminado = 0;

            IF inventarioID IS NULL THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'El producto no existe o ya está eliminado.';
            END IF;

            -- Rebajar la cantidad en el inventario correspondiente
            UPDATE Inventario i
            SET i.cantidadInventario = i.cantidadInventario - 1
            WHERE i.idInventario = inventarioID;

            -- Marcar el producto como eliminado
            UPDATE Producto p
            SET p.isEliminado = 1
            WHERE p.idProducto = p_idProducto;
        END;
        """
    },
    "CrearProducto": {
        "drop": "DROP PROCEDURE IF EXISTS CrearProducto;",
        "create": """
        CREATE PROCEDURE CrearProducto(
            IN p_idProducto INT,
            IN p_nombre VARCHAR(255),
            IN p_descripcion VARCHAR(255),
            IN p_precio FLOAT,
            IN p_idInventario INT,
            IN p_idAfiliado VARCHAR(16)
        )
        BEGIN
            DECLARE nivelAfiliado INT;

            -- Validar que el afiliado es de nivel 1
            SELECT a.idNivel INTO nivelAfiliado
            FROM Afiliado a
            WHERE a.id = p_idAfiliado;

            IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
            END IF;

            -- Insertar el producto
            INSERT INTO Producto (
                idProducto, nombre, descripcion, precio, idInventario, isEliminado
            ) VALUES (
                p_idProducto, p_nombre, p_descripcion, p_precio, p_idInventario, 0
            );

            -- Incrementar la cantidad en el inventario correspondiente
            UPDATE Inventario i
            SET i.cantidadInventario = i.cantidadInventario + 1
            WHERE i.idInventario = p_idInventario;
        END;
        """
    },
    "ListarProductos": {
        "drop": "DROP PROCEDURE IF EXISTS ListarProductos;",
        "create": """
        CREATE PROCEDURE ListarProductos(
            IN p_idAfiliado VARCHAR(16)
        )
        BEGIN
            DECLARE nivelAfiliado INT;

            -- Validar que el afiliado es de nivel 1
            SELECT a.idNivel INTO nivelAfiliado
            FROM Afiliado a
            WHERE a.id = p_idAfiliado;

            IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
            END IF;

            
            SELECT p.idProducto, p.nombre, p.descripcion, p.precio, i.cantidadInventario
            FROM Producto p 
            INNER JOIN inventario i 
            ON p.idInventario = i.idInventario;
        END;
        """
    }


}

def create_procedures_and_triggers():
    """
    Función para crear o reemplazar procedimientos almacenados y triggers.
    """
    print("Ejecutando creación de procedimientos y triggers...")
    with engine.connect() as connection:
        for name, sqls in PROCEDURES_AND_TRIGGERS.items():
            try:
                # Eliminar si ya existe
                connection.execute(text(sqls["drop"]))
                # Crear el procedimiento o trigger
                connection.execute(text(sqls["create"]))
                print(f"'{name}' creado o reemplazado exitosamente.")
            except Exception as e:
                print(f"Error creando '{name}': {str(e)}")
