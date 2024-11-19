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
   "CrearProducto": {
    "drop": "DROP PROCEDURE IF EXISTS CrearProducto;",
    "create": """
    CREATE PROCEDURE CrearProducto (
        IN idProducto INT,
        IN nombre VARCHAR(255),
        IN descripcion VARCHAR(255),
        IN precio FLOAT,
        IN idInventario INT,
        IN cantidadInventario INT,
        IN idAfiliado VARCHAR(16)
    )
    BEGIN
        DECLARE nivelAfiliado INT;

        -- Validar que el afiliado es de nivel 1
        SELECT idNivel INTO nivelAfiliado
        FROM Afiliado
        WHERE id = idAfiliado;

        IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
        END IF;

        -- Insertar el producto
        INSERT INTO Producto (idProducto, nombre, descripcion, precio, idInventario, cantidadInventario)
        VALUES (idProducto, nombre, descripcion, precio, idInventario, cantidadInventario);

        -- Actualizar cantidad en inventario
        UPDATE Inventario
        SET cantidadInventario = cantidadInventario + cantidadInventario
        WHERE idInventario = idInventario;
    END;
    """
},

    # Procedimiento: Listar Productos
  "ListarProductos": {
    "drop": "DROP PROCEDURE IF EXISTS ListarProductos;",
    "create": """
    CREATE PROCEDURE ListarProductos (
        IN idAfiliado VARCHAR(16)
    )
    BEGIN
        DECLARE nivelAfiliado INT;

        -- Validar que el afiliado es de nivel 1
        SELECT idNivel INTO nivelAfiliado
        FROM Afiliado
        WHERE id = idAfiliado;

        IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
        END IF;

        -- Listar productos con las columnas requeridas
        SELECT idProducto, nombre, descripcion, precio, idInventario
        FROM Producto;
    END;
    """
},

   "EliminarProducto": {
    "drop": "DROP PROCEDURE IF EXISTS EliminarProducto;",
    "create": """
    CREATE PROCEDURE EliminarProducto (
        IN idProducto INT,
        IN idAfiliado VARCHAR(16)
    )
    BEGIN
        DECLARE nivelAfiliado INT;

        -- Validar que el afiliado es de nivel 1
        SELECT idNivel INTO nivelAfiliado
        FROM Afiliado
        WHERE id = idAfiliado;

        IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
        END IF;

        -- Eliminar el producto
        DELETE FROM Producto WHERE idProducto = idProducto;
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
