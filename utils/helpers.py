# utils/helpers.py

def obtener_opciones_categorias(categorias):
    """Formatea categorías para Combobox incluyendo 'Todas'
    
    Args:
        categorias (list): Lista de tuplas de categorías desde la BD
        
    Returns:
        list: Lista de nombres de categorías con opción "Todas" al inicio
    """
    return ["Todas las categorías"] + [cat[1] for cat in categorias] if categorias else []

def validar_entero_positivo(valor):
    """Valida que un valor sea un entero positivo
    
    Args:
        valor (str): Valor a validar
        
    Returns:
        bool: True si es válido, False si no
    """
    try:
        return int(valor) > 0
    except (ValueError, TypeError):
        return False

# utils/helpers.py
def formatear_stock(stock_actual, stock_minimo):
    """Devuelve texto formateado y color según stock"""
    if stock_actual < stock_minimo:
        return (f"⬇ {stock_actual}", "#bf616a")  # Rojo 
    elif stock_actual == stock_minimo:
        return (f"⚠ {stock_actual}", "#ebcb8b")  # Amarillo 
    return (str(stock_actual), "#2e3440")        # Negro 

def formatear_moneda(valor):
    """Formatea números a moneda"""
    try:
        return f"${float(valor):.2f}"
    except (ValueError, TypeError):
        return "N/A"

def get_inactive_color():
    """Devuelve color para filas inactivas"""
    return "#e0e0e0"  # Gris claro