from sqlalchemy import text
from database import engine  # Asegúrate de que 'engine' está definido en 'database.py'

# Diccionario que contiene los procedimientos almacenados y triggers
PROCEDURES_AND_TRIGGERS = {
    # Procedimiento: Crear Afiliado Fundador
    "CrearAfiliadoFundador": {
        "drop": "DROP PROCEDURE IF EXISTS CrearAfiliadoFundador;",
        "create": """
        CREATE PROCEDURE CrearAfiliadoFundador (
            IN id_afiliado VARCHAR(16),
            IN nombre VARCHAR(255),
            IN apellido VARCHAR(32),
            IN email VARCHAR(200),
            IN telefono VARCHAR(45),
            IN direccion VARCHAR(45),
            IN fechaRegistro DATE,
            IN idCiudad INT,
            IN username VARCHAR(45),
            IN password VARCHAR(255)
        )
        BEGIN
            -- Verificar que no existan otros afiliados registrados
            IF EXISTS (SELECT 1 FROM Afiliado) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Ya existe un afiliado registrado. No se puede crear otro fundador.';
            END IF;

            -- Insertar el afiliado fundador
            INSERT INTO Afiliado (
                id, nombre, apellido, email, telefono, direccion, fechaRegistro,
                idCiudad, idSuperior, idNivel, username, password, codigoReferido, idEstadoAfiliado
            ) VALUES (
                id_afiliado, nombre, apellido, email, telefono, direccion, fechaRegistro,
                idCiudad, NULL, 1, username, password, 'FUNDADOR', 1
            );
        END;
        """
    },
    # Procedimiento: Crear Afiliado por Referencia
  "CrearAfiliadoPorReferencia": {
    "drop": "DROP PROCEDURE IF EXISTS CrearAfiliadoPorReferencia;",
    "create": """
    CREATE PROCEDURE CrearAfiliadoPorReferencia (
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
        IN idSuperior VARCHAR(16)
    )
    BEGIN
        DECLARE nivelSuperior INT;
        DECLARE codigoReferido VARCHAR(64);

        -- Verificar que el afiliado referidor existe y obtener su nivel
        SELECT idNivel INTO nivelSuperior
        FROM Afiliado
        WHERE id = idSuperior AND idEstadoAfiliado = 1;

        -- Asignar nivel al nuevo afiliado
        IF nivelSuperior >= 5 THEN
            SET nivelSuperior = 5; -- Si el nivel del referidor es el más bajo, el nuevo afiliado también será nivel 5
        ELSE
            SET nivelSuperior = nivelSuperior + 1; -- Nivel inmediatamente inferior
        END IF;

        -- Generar el código de referido
        SET codigoReferido = CONCAT('REF-', id_afiliado);

        -- Insertar el nuevo afiliado
        INSERT INTO Afiliado (
            id, nombre, apellido, email, telefono, direccion, fechaRegistro,
            idCiudad, idSuperior, idNivel, username, password, codigoReferido, idEstadoAfiliado
        ) VALUES (
            id_afiliado, nombre, apellido, email, telefono, direccion, fechaRegistro,
            idCiudad, idSuperior, nivelSuperior, username, password, codigoReferido, 1
        );
    END;
    """
},

    # Procedimiento: Crear Producto
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

            -- Listar solo productos activos (no eliminados)
            SELECT p.idProducto, p.nombre, p.descripcion, p.precio, p.idInventario
            FROM Producto p
            WHERE p.isEliminado = 0;
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
