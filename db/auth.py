import sqlite3

def obtener_usuario(correo):
    conn = sqlite3.connect("data/ventas.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM Usuarios WHERE correo = ?", (correo,))
    row = cur.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None
