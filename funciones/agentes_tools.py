from langchain.tools import tool
from typing import Literal, Dict, Optional
@tool(
    "clasificador_edificios",
    parse_docstring=True,
    description=(
        "Extrae nombre del edificio, nombre del piso y nombre del ambiente, fechas de inicio y fin en formato YYYY-MM-DD."
        "Utiliza esta tool cuando se desee consultar por el consumo de edificio, piso y ambiente."
    ),
)
def clasificador_edificios(
    edificio: str, piso: str, ambiente: str, fecha_inicio: Optional[str] = '', fecha_fin: Optional[str] = ''
) -> Dict[str, str]:
    """Extrae nombre del edificio, del piso y del ambiente.

    Args:
        edificio (str): Nombre del edificio.
        piso (str): Nombre del piso.
        ambiente (str): Nombre del ambiente.
        fecha_inicio (Optional[str]): Fecha de inicio. (Si no encuentras fecha de inicio, puede quedar vacio)
        fecha_fin (Optional[str]): Fecha de fin. (Si no encuentras fecha de fin, puede quedar vacio)

    Returns:
        Dict[str, str]: Un diccionario de forma {'edificio': 'nombre_edificio', 'piso':'nombre_piso', 'ambiente': 'nombre_ambiente', 'fecha_inicio': 'fecha_inicio', 'fecha_fin': 'fecha_fin'}.
    """
    print("🧮  Invocando clasificador tool")
    resultado = {
        'edificio': edificio, 'piso':piso, 'ambiente': ambiente, 'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin
    }
    
    return resultado

@tool(
    "prediccion_consumo",
    parse_docstring=True,
    description=(
        "Clasifica cada dia de la semana con las etiquetas 'feriado', 'especial', 'normal'; ademas, extrae nombre del edificio, del piso y del ambiente."
        "Utiliza esta tool cuando se desee consultar la prediccion a futuro del consumo."
    ),
)
def prediccion_consumo(
    edificio: str, piso: str, ambiente: str,
    lunes: Literal["feriado", "especial", "normal"] = "normal", 
    martes: Literal["feriado", "especial", "normal"] = "normal", 
    miercoles: Literal["feriado", "especial", "normal"] = "normal", 
    jueves: Literal["feriado", "especial", "normal"] = "normal", 
    viernes: Literal["feriado", "especial", "normal"] = "normal", 
    sabado: Literal["feriado", "especial", "normal"] = "normal", 
    domingo: Literal["feriado", "especial", "normal"] = "normal"
) -> Dict[str, str]:
    """
    Clasifica cada día de la semana con las etiquetas 'feriado', 'especial', 'normal'; ademas, extrae nombre del edificio, del piso y del ambiente.

    Args:
        edificio (str): Nombre del edificio.
        piso (str): Nombre del piso.
        ambiente (str): Nombre del ambiente.
        lunes (Literal["feriado", "especial", "normal"]): Novedad del día lunes (si no se especifica, etiquetaras como 'normal').
        martes (Literal["feriado", "especial", "normal"]): Novedad del día martes (si no se especifica, etiquetaras como 'normal').
        miercoles (Literal["feriado", "especial", "normal"]): Novedad del día miércoles (si no se especifica, etiquetaras como 'normal').
        jueves (Literal["feriado", "especial", "normal"]): Novedad del día jueves (si no se especifica, etiquetaras como 'normal').
        viernes (Literal["feriado", "especial", "normal"]): Novedad del día viernes (si no se especifica, etiquetaras como 'normal').
        sabado (Literal["feriado", "especial", "normal"]): Novedad del día sábado (si no se especifica, etiquetaras como 'normal').
        domingo (Literal["feriado", "especial", "normal"]): Novedad del día domingo (si no se especifica, etiquetaras como 'normal').

    Returns
        Dict[str, str]: Diccionario con la novedad asignada a cada día.
    """
    print("🧮  Invocando clasificador tool")
    resultado = {
        'edificio': edificio, 'piso':piso, 'ambiente': ambiente, 'lunes': lunes, 'martes':martes, 'miercoles': miercoles, 'jueves': jueves, 'viernes': viernes, 'sabado': sabado, 'domingo': domingo
    }
    
    return resultado

@tool("retrieve", response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs