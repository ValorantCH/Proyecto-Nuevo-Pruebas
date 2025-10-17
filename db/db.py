import sqlite3
import sys
import os
from pathlib import Path

def get_db_path():
    """Obtiene la ruta correcta de la base de datos según el entorno"""
    if getattr(sys, 'frozen', False):
        # Entorno empaquetado (ejecutable)
        base_path = Path(sys._MEIPASS)
    else:
        # Entorno de desarrollo
        base_path = Path(__file__).parent.parent
    
    db_path = base_path / "data" / "ventas.db"
    
    # Si está empaquetado y necesitamos escribir, copiamos a directorio de usuario
    if getattr(sys, 'frozen', False) and not db_path.exists():
        user_data_dir = Path.home() / "AppData" / "Local" / "ventas"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        db_path = user_data_dir / "ventas.db"
        
        # Copiar la base de datos original si no existe
        if not db_path.exists():
            original_db = base_path / "data" / "ventas.db"
            db_path.write_bytes(original_db.read_bytes())
    
    return db_path

def connect_db():
    """Establece conexión con la base de datos"""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row 
    return conn

def ejecutar_query(query, parameters=()):
    """Ejecuta una query de modificación"""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        conn.commit()
        return cursor.lastrowid

def obtener_datos(query, parameters=()):
    """Obtiene resultados de una consulta SELECT"""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        return cursor.fetchall()

def ejecutar_transaccion(queries):
    """
    Ejecuta múltiples queries en una sola transacción atómica.
    
    Args:
        queries (list): Lista de tuplas con (query, parametros)
        
    Returns:
        int: Último rowid de la última operación INSERT
    """
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        for query, params in queries:
            cursor.execute(query, params)
            
        conn.commit()
        return cursor.lastrowid
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()