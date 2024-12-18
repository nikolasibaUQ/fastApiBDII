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

            -- Verificar si es el fundador (codigoReferido es NULL o vacío y no existen afiliados)
            IF codigoReferido IS NULL OR codigoReferido = '' THEN
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

                -- Insertar al fundador en su propia jerarquía si no existe
                IF NOT EXISTS (SELECT 1 FROM AfiliadoJerarquia WHERE idAfiliado = id_afiliado AND idSuperior = id_afiliado) THEN
                    INSERT INTO AfiliadoJerarquia (idAfiliado, idSuperior, nivel)
                    VALUES (id_afiliado, id_afiliado, 0);
                END IF;
            ELSE
                -- Validar el codigoReferido y obtener el idSuperior con el nivel más alto
                SELECT a.id, a.idNivel 
                INTO idSuperior, nivelSuperior
                FROM Afiliado a
                WHERE a.codigoReferido = codigoReferido AND a.idEstadoAfiliado = 1
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
                SET codigoReferidoGenerado = id_afiliado;

                -- Insertar el nuevo afiliado
                INSERT INTO Afiliado (
                    id, nombre, apellido, email, telefono, direccion, fechaRegistro,
                    idCiudad, idSuperior, idNivel, username, password, codigoReferido, idEstadoAfiliado
                ) VALUES (
                    id_afiliado, nombre, apellido, email, telefono, direccion, fechaRegistro,
                    idCiudad, idSuperior, nivelSuperior, username, password, codigoReferidoGenerado, 1
                );

                -- Insertar la relación directa en AfiliadoJerarquia si no existe
                IF NOT EXISTS (SELECT 1 FROM AfiliadoJerarquia WHERE idAfiliado = id_afiliado AND idSuperior = idSuperior) THEN
                    INSERT INTO AfiliadoJerarquia (idAfiliado, idSuperior, nivel)
                    VALUES (id_afiliado, idSuperior, 1);
                END IF;

                -- Insertar las relaciones indirectas en AfiliadoJerarquia si no existen
                INSERT INTO AfiliadoJerarquia (idAfiliado, idSuperior, nivel)
                SELECT id_afiliado, aj.idSuperior, aj.nivel + 1
                FROM AfiliadoJerarquia aj
                WHERE aj.idAfiliado = idSuperior
                AND NOT EXISTS (
                    SELECT 1 FROM AfiliadoJerarquia
                    WHERE idAfiliado = id_afiliado AND idSuperior = aj.idSuperior
                );
            END IF;
        END;
    """
  },

    "ListarRedAfiliado": {
    "drop": "DROP PROCEDURE IF EXISTS ListarRedAfiliado;",
    "create": """
        CREATE PROCEDURE ListarRedAfiliado(
            IN p_idAfiliado VARCHAR(16)
        )
        BEGIN
            -- CTE recursiva para construir la jerarquía completa de afiliados
            WITH RECURSIVE AfiliadoRed AS (
                -- Nivel inicial: el afiliado directo
                SELECT 
                    a.id AS idAfiliado,
                    a.nombre,
                    a.apellido,
                    a.email,
                    a.telefono,
                    a.direccion,
                    a.fechaRegistro,
                    a.idCiudad,
                    a.idNivel AS nivel,
                    1 AS nivelEnRed, -- Nivel relativo en la red
                    a.codigoReferido
                FROM Afiliado a
                WHERE a.idSuperior = p_idAfiliado

                UNION ALL

                -- Iteración recursiva para encontrar afiliados indirectos
                SELECT 
                    af.id AS idAfiliado,
                    af.nombre,
                    af.apellido,
                    af.email,
                    af.telefono,
                    af.direccion,
                    af.fechaRegistro,
                    af.idCiudad,
                    af.idNivel AS nivel,
                    ar.nivelEnRed + 1 AS nivelEnRed,
                    af.codigoReferido
                FROM Afiliado af
                INNER JOIN AfiliadoRed ar ON af.idSuperior = ar.idAfiliado
            )

            -- Seleccionar la jerarquía construida
            SELECT * 
            FROM AfiliadoRed;
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

        -- Validar que el afiliado es de nivel 1
        SELECT a.idNivel INTO nivelAfiliado
        FROM Afiliado a
        WHERE a.id = p_idAfiliado;

        IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
        END IF;

        -- Verificar que el producto existe
        IF NOT EXISTS (SELECT 1 FROM Producto WHERE idProducto = p_idProducto) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El producto no existe.';
        END IF;

        -- Eliminar el producto físicamente
        DELETE FROM Producto
        WHERE idProducto = p_idProducto;
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
        IN p_idAfiliado VARCHAR(16),
        IN p_cantidad INT

    )
    BEGIN
        DECLARE nivelAfiliado INT;
        DECLARE productoExistente INT;

        -- Validar que el afiliado es de nivel 1
        SELECT a.idNivel INTO nivelAfiliado
        FROM Afiliado a
        WHERE a.id = p_idAfiliado;

        IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
        END IF;

        -- Verificar si el producto ya existe
        SELECT COUNT(1) INTO productoExistente
        FROM Producto p
        WHERE p.idProducto = p_idProducto;

        IF productoExistente > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El producto ya existe.';
        END IF;

        -- Insertar el producto con la cantidad inicial
        INSERT INTO Producto (idProducto, nombre, descripcion, precio, cantidad)
        VALUES (p_idProducto, p_nombre, p_descripcion, p_precio, p_cantidad);
    END;
    """
},
   "ListarProductos": {
    "drop": "DROP PROCEDURE IF EXISTS ListarProductos;",
    "create": """
    CREATE PROCEDURE ListarProductos()
    BEGIN
        -- Listar todos los productos con su información básica
        SELECT 
            p.idProducto, 
            p.nombre, 
            p.descripcion, 
            p.precio, 
            p.cantidad
        FROM Producto p;
    END;
    """
},

"ActualizarProducto": {
    "drop": "DROP PROCEDURE IF EXISTS ActualizarProducto;",
    "create": """
        CREATE PROCEDURE ActualizarProducto(
            IN p_idProducto INT,
            IN p_nombre VARCHAR(255),
            IN p_descripcion VARCHAR(255),
            IN p_precio DECIMAL(10, 2),
            IN p_cantidad INT,
            IN p_idAfiliado VARCHAR(16)
        )
        BEGIN
            DECLARE nivelAfiliado INT;

            -- Verificar que el afiliado es de nivel 1
            SELECT a.idNivel INTO nivelAfiliado
            FROM Afiliado a
            WHERE a.id = p_idAfiliado;

            IF nivelAfiliado IS NULL OR nivelAfiliado != 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Solo el afiliado principal puede realizar esta operación.';
            END IF;

            -- Verificar si el producto existe
            IF NOT EXISTS (
                SELECT 1
                FROM Producto
                WHERE idProducto = p_idProducto
            ) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'El producto no existe.';
            END IF;

            -- Actualizar los datos del producto
            UPDATE Producto
            SET 
                nombre = p_nombre,
                descripcion = p_descripcion,
                precio = p_precio,
                cantidad = p_cantidad
            WHERE idProducto = p_idProducto;
        END;
    """
},

    #VENTAS
        #Trigger crear despacho luego de una venta
      # Trigger: DespachoVenta
    "DespachoVenta": {
        "drop": "DROP TRIGGER IF EXISTS DespachoVenta;",
        "create": """
        CREATE TRIGGER DespachoVenta
        AFTER INSERT ON Venta
        FOR EACH ROW
        BEGIN
            INSERT INTO Despacho (idVenta, fechaEnvio, idEstado)
            VALUES (NEW.idVenta, NOW(), 1);
        END;
        """
    },


    #Registrar Venta
     "RegistrarVenta": {
        "drop": "DROP PROCEDURE IF EXISTS RegistrarVenta;",
        "create": """
        CREATE PROCEDURE RegistrarVenta(
            IN p_fechaVenta DATE,
            IN p_valor DECIMAL(10, 2),
            IN p_idAfiliado VARCHAR(16),
            IN p_listaProductos JSON
        )
        BEGIN
            DECLARE cantidadDisponible INT;
            DECLARE cantidadSolicitada INT;
            DECLARE idProducto INT;
            DECLARE subtotal DECIMAL(10, 2);
            DECLARE idVenta INT;

            -- Crear la venta
            INSERT INTO Venta (fechaVenta, valor, idAfiliado)
            VALUES (p_fechaVenta, p_valor, p_idAfiliado);

            -- Obtener el ID de la venta recién creada
            SET idVenta = LAST_INSERT_ID();

            -- Iterar sobre la lista de productos proporcionada
            SET @jsonData = p_listaProductos;
            WHILE JSON_LENGTH(@jsonData) > 0 DO
                SET idProducto = CAST(JSON_UNQUOTE(JSON_EXTRACT(@jsonData, '$[0].idProducto')) AS UNSIGNED);
                SET cantidadSolicitada = CAST(JSON_UNQUOTE(JSON_EXTRACT(@jsonData, '$[0].cantidad')) AS UNSIGNED);

                -- Verificar si hay suficiente cantidad disponible en el producto
                SELECT cantidad INTO cantidadDisponible
                FROM Producto
                WHERE idProducto = idProducto
                LIMIT 1;

                IF cantidadDisponible IS NULL OR cantidadDisponible < cantidadSolicitada THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Stock insuficiente para el producto.';
                END IF;

                -- Calcular subtotal
                SELECT precio * cantidadSolicitada INTO subtotal
                FROM Producto
                WHERE idProducto = idProducto
                LIMIT 1;

                -- Insertar en DetalleVenta
                INSERT INTO DetalleVenta (cantidad, subtotal, Venta_idVenta, idProducto)
                VALUES (cantidadSolicitada, subtotal, idVenta, idProducto);

                -- Restar cantidad del producto
                UPDATE Producto
                SET cantidad = cantidad - cantidadSolicitada
                WHERE idProducto = idProducto;

                -- Eliminar el primer elemento del JSON
                SET @jsonData = JSON_REMOVE(@jsonData, '$[0]');
            END WHILE;

            -- El trigger se encargará de insertar en la tabla Despacho
        COMMIT;
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
