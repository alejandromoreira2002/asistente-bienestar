import re

from langchain_milvus import Milvus
from langchain_core.documents import Document
from typing_extensions import List, TypedDict
from langchain.tools import tool
from typing import Literal, Dict, Optional, Any, Annotated
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt
from langchain_ollama.chat_models import ChatOllama
from operator import add
from flask import session
from db.db import PostgresDB
import requests
import os
import pandas as pd
from datetime import timedelta, date
import numpy as np
import json
import uuid
from controladores.algoritmo_ml import AlgoritmoMLControlador
from funciones.algoritmos import getInfoLugar, norm, fuzzy_lookup
from funciones.funciones import generarDF
from data.globals import EVENT_BUFFERS
import unicodedata
from rapidfuzz import process, utils, fuzz

class State(TypedDict):
    messages: Annotated[list[Any], add]
    datos: Dict[str, Any]

class AgentesModelo:
    def __init__(self, app):
        self.db = PostgresDB(app, os.getenv("PG_DB"))
        # self.embeddings = HuggingFaceEmbeddings(
        #     model_name=os.getenv("EMBEDDING_MODEL"),
        #     model_kwargs={'device': 'cpu'},
        #     encode_kwargs={'device': 'cpu', 'batch_size': 32}
        # )
        # self.vector_store = Milvus(
        #     embedding_function=self.embeddings,
        #     connection_args={"uri": os.getenv("VS_RUTA")},
        #     index_params={"index_type": "FLAT", "metric_type": "L2"},
        # )
        self.llm = init_chat_model("gpt-4o")
        # self.llm = ChatOllama(model="gemma4:latest", base_url="http://172.16.188.53:3002/", temperature=0.2)
        # self.data = self.leerJSONEdificios()
        self.data = self.leerJSONCampos()
        # data = {
        #     'ficha_datos_iniciales': [
        #         {'id': 'provincia', 'label': '¿En qué provincia resides?', 'saltar_si': []}, 
        #         {'id': 'ciudad', 'label': '¿En qué ciudad resides?', 'saltar_si': []}, 
        #         {'id': 'parroquia', 'label': '¿En qué parroquia resides?', 'saltar_si': []}, 
        #         {'id': 'es_estudiante', 'label': '¿Eres estudiante? (responde sí o no)', 'saltar_si': []}, 
        #         {'id': 'institucion', 'label': 'En qué institución estudias? (UTM u otra)', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}]}, 
        #         {'id': 'nombre_institucion', 'label': 'Si no es UTM, ¿Cuál es el nombre de la institución en la que estudias?', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}, {'id': 'institucion', 'valor': 'utm'}]}, 
                
        #         # {'id': 'facultad', 'label': '¿En qué facultad estudias?', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}, {'id': 'institucion', 'valor': 'utm'}]}, 
        #         {'id': 'facultad', 'label': '¿En qué facultad estudias?', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}]}, 
        #         # {'id': 'select_facultad', 'label': 'Escoge las facultades que estudias: Ciencias de la Salud, Ciencias Informaticas, Ciencias Humanisticas', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}, {'id': 'institucion', 'valor': 'otro'}]}, 
                
        #         # {'id': 'carrera', 'label': '¿Qué carrera estudias?', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}, {'id': 'institucion', 'valor': 'utm'}]}, 
        #         {'id': 'carrera', 'label': '¿Qué carrera estudias?', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}]}, 
        #         # {'id': 'select_carrera', 'label': 'Escoge la carrera que estudias: Medicina, Biologia, Psicologia', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}, {'id': 'institucion', 'valor': 'otro'}]}, 
                
        #         {'id': 'modalidad', 'label': '¿En qué modalidad estudias? (PRESENCIAL, HÍBRIDA, EN LÍNEA)', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}]}, 
                
        #         # {'id': 'nivel', 'label': '¿En qué nivel académico te encuentras?', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}, {'id': 'institucion', 'valor': 'utm'}]}, 
        #         {'id': 'nivel', 'label': '¿En qué nivel académico te encuentras?', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}]}, 
        #         # {'id': 'select_nivel', 'label': 'Escoge el nivel academico en el que te encuentras: Nivel 1, Nivel 2, Nivel 3', 'saltar_si': [{'id': 'es_estudiante', 'valor': 'no'}, {'id': 'institucion', 'valor': 'otro'}]}, 
        #     ],
        #     'datos_identificacion': [
        #         {'id': 'nombres', 'label': '¿Cuáles son tus nombres?', 'saltar_si': []}, 
        #         {'id': 'apellidos', 'label': '¿Cuáles son tus apellidos?', 'saltar_si': []}, 
        #         {'id': 'cedula', 'label': '¿Cuál es tu número de cédula?', 'saltar_si': []}, 
        #         {'id': 'celular', 'label': '¿Cuál es tu número de celular?', 'saltar_si': []}, 
        #         {'id': 'correo', 'label': '¿Cuál es tu correo electrónico?', 'saltar_si': []}, 
        #         {'id': 'edad', 'label': '¿Cuántos años tienes?', 'saltar_si': []}, 
        #         {'id': 'fecha_nacimiento', 'label': '¿Cuál es tu fecha de nacimiento?', 'saltar_si': []}, 
        #         {'id': 'nacionalidad', 'label': '¿Cuál es tu nacionalidad?', 'saltar_si': []}, 
        #         {'id': 'sexo', 'label': '¿Cuál es tu sexo?', 'saltar_si': []}, 
        #         {'id': 'sexo_otro', 'label': 'Si el sexo es otro (no masculino ni femenino), especifique ¿cual es su sexo?', 'saltar_si': [{'id': 'sexo', 'valor': 'femenino'}, {'id': 'sexo', 'valor': 'masculino'}]}, 
        #         {'id': 'identidad_genero', 'label': 'Con que genero se identifica? (Opcional)', 'saltar_si': []}, 
        #         {'id': 'direccion', 'label': '¿Cuál es tu dirección de domicilio?', 'saltar_si': []}, 
        #         {'id': 'lugar_residencia', 'label': 'En caso de residir en otra ciudad o provincia, ¿Dónde resides actualmente?', 'saltar_si': []}, 
        #         {'id': 'contacto_referencia', 'label': '¿Cuál es el nombre y contacto de referencia?', 'saltar_si': []}, 
        #     ]
        # }
        self.controladorAlgoritmoML = AlgoritmoMLControlador()

    def leerJSONEdificios(self):
        ruta = os.getenv('EDIFICIOS_RUTA')
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)  # data es una lista de dicts
        
    def leerJSONCampos(self):
        ruta = os.getenv('CAMPOS_RUTA')
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)  # data es una lista de dicts
    
    def getIdHilo(self):
        idHilo = uuid.uuid4()
        return idHilo
    
    def getTools(self):
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
            "mostrar_formulario",
            parse_docstring=True,
            description=(
                "Abre o cierra un modal que muestra el formulario."
                "Utiliza esta tool cuando el usuario desee ver el formulario o ficha."
            ),
        )
        def mostrar_formulario(
            abrir: bool
        ) -> Dict[str, str]:
            """Abre o cierra un modal que muestra el formulario.

            Args:
                abrir (bool): Indica si se debe abrir o cerrar el modal del formulario.

            Returns:
                Dict[str, str]: Un diccionario de forma {'abrir': 'True/False'}.
            """
            print("🧮  Invocando clasificador tool")
            resultado = {
                'abrir': bool(abrir)
            }
            return resultado
        
        @tool(
            "continuar_al_formulario",
            parse_docstring=True,
            description=(
                "Confirma proceder a llenar el formulario o ficha."
                "Utiliza esta tool cuando el usuario desee pasar a llenar el formulario o ficha."
            ),
        )
        def continuar_al_formulario(
            proceder: bool
        ) -> Dict[str, str]:
            """Confirma proceder a llenar el formulario o ficha.

            Args:
                proceder (bool): Indica si desea proceder a llenar el formulario o ficha.

            Returns:
                Dict[str, str]: Un diccionario de forma {'proceder': 'True/False'}.
            """
            print("🧮  Invocando clasificador tool")
            resultado = {
                'proceder': bool(proceder)
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
            retrieved_docs = self.vector_store.similarity_search(query, k=2)
            serialized = "\n\n".join(
                (f"Source: {doc.metadata}\nContent: {doc.page_content}")
                for doc in retrieved_docs
            )
            return serialized, retrieved_docs
        
        @tool(
            "extraer_datos_iniciales",
            parse_docstring=True,
            description=(
                "Extrae datos de la 'Ficha de Datos Iniciales' que menciona el paciente: provincia, ciudad, parroquia, es_estudiante, institucion, facultad, carrera, modalidad, nivel. "
                "Los parámetros son opcionales. Utiliza esta tool para extraer con flexibilidad los campos que el paciente mencionó sin necesidad de que mencione todos a la vez."
            ),
        )
        def extraer_datos_iniciales(
            provincia: Optional[str] = None,
            ciudad: Optional[str] = None,
            parroquia: Optional[str] = None,
            es_estudiante: Optional[Literal["si", "no"]] = None,
            institucion: Optional[Literal["utm", "otro"]] = None,
            nombre_institucion: Optional[str] = None,
            facultad: Optional[str] = None,
            # select_facultad: Optional[Literal["ciencias_de_la_salud", "ciencias_informaticas", "ciencias_humanisticas"]] = None,
            carrera: Optional[str] = None,
            # select_carrera: Optional[Literal["medicina", "biologia", "psicologia"]] = None,
            modalidad: Optional[Literal["presencial", "hibrida", "en_linea"]] = None,
            nivel: Optional[str] = None,
            # select_nivel: Optional[Literal["nivel1", "nivel2", "nivel3"]] = None
        ) -> Dict[str, Any]:
            """Extrae datos de la 'Ficha de Datos Iniciales' que menciona el paciente.

            Args:
                provincia (Optional[str]): Provincia del paciente.
                ciudad (Optional[str]): Ciudad del paciente.
                parroquia (Optional[str]): Parroquia del paciente.
                es_estudiante (Optional[Literal["si", "no"]]): ¿Es estudiante? Si o No.
                institucion (Optional[Literal["utm", "otro"]]): Institución donde estudia el paciente (UTM u otro).
                nombre_institucion (Optional[str]): Nombre de la institución si no es UTM.
                facultad (Optional[str]): Facultad del paciente.
                carrera (Optional[str]): Carrera del paciente.
                modalidad (Optional[Literal["presencial", "hibrida", "en_linea"]]): Modalidad de estudio (PRESENCIAL, HÍBRIDA, EN LÍNEA).
                nivel (Optional[str]): Nivel del paciente, conviertelo en texto del número cardinal, ejemplo: "nivel 1" -> "PRIMER NIVEL".

            Returns:
                Dict[str, Any]: Diccionario con los datos extraídos. Solo incluye campos que fueron proporcionados.
            """
            # """Extrae datos de la 'Ficha de Datos Iniciales' que menciona el paciente.

            # Args:
            #     provincia (Optional[str]): Provincia del paciente.
            #     ciudad (Optional[str]): Ciudad del paciente.
            #     parroquia (Optional[str]): Parroquia del paciente.
            #     es_estudiante (Optional[Literal["si", "no"]]): ¿Es estudiante? Si o No.
            #     institucion (Optional[Literal["utm", "otro"]]): Institución donde estudia el paciente (UTM u otro).
            #     nombre_institucion (Optional[str]): Nombre de la institución si no es UTM.
            #     facultad (Optional[str]): Facultad del paciente.
            #     select_facultad (Optional[Literal["ciencias_de_la_salud", "ciencias_informaticas", "ciencias_humanisticas"]]): El paciente escoge una de las siguientes facultades de la UTM: Ciencias de la Salud, Ciencias Informaticas, Ciencias Humanisticas.
            #     carrera (Optional[str]): Carrera del paciente.
            #     select_carrera (Optional[Literal["medicina", "biologia", "psicologia"]]): El paciente escoge una de las siguientes carreras de la UTM: Medicina, Biologia, Psicologia.
            #     modalidad (Optional[Literal["presencial", "hibrida", "en_linea"]]): Modalidad de estudio (PRESENCIAL, HÍBRIDA, EN LÍNEA).
            #     nivel (Optional[str]): Nivel del paciente.
            #     select_nivel (Optional[Literal["nivel1", "nivel2", "nivel3"]]): El paciente escoge uno de los siguientes niveles académicos: Nivel 1, Nivel 2, Nivel 3.

            # Returns:
            #     Dict[str, Any]: Diccionario con los datos extraídos. Solo incluye campos que fueron proporcionados.
            # """
            print("🧮  Invocando extraer_datos_iniciales tool")
            resultado = {}
            
            if provincia is not None:
                resultado['provincia'] = provincia
            if ciudad is not None:
                resultado['ciudad'] = ciudad
            if parroquia is not None:
                resultado['parroquia'] = parroquia
            if es_estudiante is not None:
                resultado['es_estudiante'] = es_estudiante
            if institucion is not None:
                resultado['institucion'] = institucion
            if nombre_institucion is not None:
                resultado['nombre_institucion'] = nombre_institucion
            if facultad is not None:
                resultado['facultad'] = facultad
            if carrera is not None:
                resultado['carrera'] = carrera
            if modalidad is not None:
                resultado['modalidad'] = modalidad
            if nivel is not None:
                resultado['nivel'] = nivel
                
            return resultado

        @tool(
            "extraer_datos_identificacion",
            parse_docstring=True,
            description=(
                "Extrae datos de la sección '1. Datos de Identificación del Usuario' que menciona el paciente: nombres, apellidos, cédula, celular, correo, edad, fecha_nacimiento, nacionalidad, sexo, genero, direccion, lugar_residencia, contacto_referencia. "
                "Los parámetros son opcionales. Utiliza esta tool para extraer con flexibilidad los campos que el paciente mencionó."
            ),
        )
        def extraer_datos_identificacion(
            nombres: Optional[str] = None,
            apellidos: Optional[str] = None,
            cedula: Optional[str] = None,
            celular: Optional[str] = None,
            correo: Optional[str] = None,
            edad: Optional[int] = None,
            fecha_nacimiento: Optional[str] = None,
            nacionalidad: Optional[str] = None,
            sexo: Optional[Literal["femenino", "masculino", "otro"]] = None,
            sexo_otro: Optional[str] = None,
            identidad_genero: Optional[str] = None,
            direccion: Optional[str] = None,
            lugar_residencia: Optional[str] = None,
            contacto_referencia: Optional[str] = None
        ) -> Dict[str, Any]:
            """Extrae datos de 'Datos de Identificación del Usuario' que menciona el paciente.

            Args:
                nombres (Optional[str]): Nombres del paciente.
                apellidos (Optional[str]): Apellidos del paciente.
                cedula (Optional[str]): Número de cédula del paciente, sin guiones y sin espacios, todos los numeros juntos.
                celular (Optional[str]): Número de celular del paciente, sin guiones y sin espacios, todos los numeros juntos.
                correo (Optional[str]): Correo electrónico del paciente.
                edad (Optional[int]): Edad del paciente.
                fecha_nacimiento (Optional[str]): Fecha de nacimiento en formato YYYY-MM-DD.
                nacionalidad (Optional[str]): Nacionalidad del paciente.
                sexo (Optional[Literal["femenino", "masculino", "otro"]]): Sexo del paciente.
                sexo_otro (Optional[str]): Si el sexo del paciente no es masculino ni femenino, especifica cuál es su sexo.
                identidad_genero (Optional[str]): Identidad de género del paciente (opcional).
                direccion (Optional[str]): Dirección de domicilio del paciente.
                lugar_residencia (Optional[str]): Lugar de residencia si es diferente al domicilio.
                contacto_referencia (Optional[str]): Nombre y contacto de referencia.

            Returns:
                Dict[str, Any]: Diccionario con los datos extraídos. Solo incluye campos que fueron proporcionados.
            """
            print("🧮  Invocando extraer_datos_identificacion tool")
            resultado = {}
            
            if nombres is not None:
                resultado['nombres'] = nombres
            if apellidos is not None:
                resultado['apellidos'] = apellidos
            if cedula is not None:
                resultado['cedula'] = cedula
            if celular is not None:
                resultado['celular'] = celular
            if correo is not None:
                resultado['correo'] = correo
            if edad is not None:
                resultado['edad'] = edad
            if fecha_nacimiento is not None:
                resultado['fecha_nacimiento'] = fecha_nacimiento
            if nacionalidad is not None:
                resultado['nacionalidad'] = nacionalidad
            if sexo is not None:
                resultado['sexo'] = sexo
            if genero is not None:
                resultado['genero'] = genero
            if direccion is not None:
                resultado['direccion'] = direccion
            if lugar_residencia is not None:
                resultado['lugar_residencia'] = lugar_residencia
            if contacto_referencia is not None:
                resultado['contacto_referencia'] = contacto_referencia
                
            return resultado
        
        @tool(
            "extraer_area_consulta",
            parse_docstring=True,
            description=(
                "Extrae datos de la seccion '2. Área de Consulta' que menciona el paciente: area_consulta, area_consulta_especifica. "
                "Los parámetros son opcionales. Utiliza esta tool para extraer con flexibilidad los campos que el paciente mencionó sin necesidad de que mencione todos a la vez."
            ),
        )
        def extraer_area_consulta(
            area_consulta: Optional[Literal["ginecologia", "asesoria_juridica", "trabajo_social", "psicologia", "laboratorio_clinico"]] = None,
            area_consulta_especifica: Optional[Literal["vih", "sifilis", "hepatitis_b", "hepatitis_c", "prueba_embarazo"]] = None,
        ) -> Dict[str, Any]:
            """Extrae datos de '2. Área de Consulta' que menciona el paciente.

            Args:
                area_consulta (Optional[Literal["ginecologia", "asesoria_juridica", "trabajo_social", "psicologia", "laboratorio_clinico"]]): Área de consulta a la que pertenece el paciente.
                area_consulta_especifica (Optional[Literal["vih", "sifilis", "hepatitis_b", "hepatitis_c", "prueba_embarazo"]]): Especificación de la área de consulta.

            Returns:
                Dict[str, Any]: Diccionario con los datos extraídos. Solo incluye campos que fueron proporcionados.
            """
            print("🧮  Invocando extraer_area_consulta tool")
            return {
                'area_consulta': area_consulta,
                'area_consulta_especifica': area_consulta_especifica
            }
            
        @tool(
            "extraer_datos_personales",
            parse_docstring=True,
            description=(
                "Extrae datos de la seccion '3. Datos Personales' que menciona el paciente: atencion_medica_inmediata, embarazada, meses_embarazo, discapacidad, discapacidad_texto, carnet_discapacidad, porcentaje_discapacidad, estado_civil, estado_civil_otro, etnia, etnia_otro. "
                "Los parámetros son opcionales. Utiliza esta tool para extraer con flexibilidad los campos que el paciente mencionó sin necesidad de que mencione todos a la vez."
            ),
        )
        def extraer_datos_personales(
            atencion_medica_inmediata: Optional[Literal["si", "no"]] = None,
            embarazada: Optional[Literal["si", "no"]] = None,
            meses_embarazo: Optional[int] = None,
            discapacidad: Optional[Literal["si", "no"]] = None,
            discapacidad_texto: Optional[str] = None,
            carnet_discapacidad: Optional[Literal["si", "no"]] = None,
            porcentaje_discapacidad: Optional[str] = None,
            estado_civil: Optional[Literal["casado", "union_hecho", "viudo", "soltero", "divorciado", "separado", "union_libre", "otro"]] = None,
            estado_civil_otro: Optional[str] = None,
            etnia: Optional[Literal["indigena", "montubia", "blanca", "afrodescendiente", "mestiza", "otra"]] = None,
            etnia_otro: Optional[str] = None
        ) -> Dict[str, Any]:
            """Extrae datos de '3. Datos Personales' que menciona el paciente.

            Args:
                atencion_medica_inmediata (Optional[Literal["si", "no"]]): Indica si el paciente requiere atención médica inmediata.
                embarazada (Optional[Literal["si", "no"]]): Indica si la paciente se encuentra embarazada.
                meses_embarazo (Optional[int]): Registra el número de meses de embarazo de la paciente.
                discapacidad (Optional[Literal["si", "no"]]): Indica si el paciente tiene alguna discapacidad.
                discapacidad_texto (Optional[str]): Si el paciente tiene discapacidad, registra la descripción de la discapacidad.
                carnet_discapacidad (Optional[Literal["si", "no"]]): Si el paciente tiene discapacidad, indica si tiene carnet de discapacidad.
                porcentaje_discapacidad (Optional[str]): Si el paciente tiene discapacidad, registra el porcentaje de discapacidad.
                estado_civil (Optional[Literal["casado", "union_hecho", "viudo", "soltero", "divorciado", "separado", "union_libre", "otro"]]): Estado civil del paciente.
                estado_civil_otro (Optional[str]): Si el estado civil es otro, describe su estado civil.
                etnia (Optional[Literal["indigena", "montubia", "blanca", "afrodescendiente", "mestiza", "otra"]]): Pertenencia étnica-cultural.
                etnia_otro (Optional[str]): Si la etnia es otra, describe cuál es su etnia.

            Returns:
                Dict[str, Any]: Diccionario con los datos extraídos. Solo incluye campos que fueron proporcionados.
            """
            print("🧮  Invocando extraer_datos_personales tool")
            return {
                'atencion_medica_inmediata': atencion_medica_inmediata,
                'embarazada': embarazada,
                'meses_embarazo': meses_embarazo,
                'discapacidad': discapacidad,
                'discapacidad_texto': discapacidad_texto,
                'carnet_discapacidad': carnet_discapacidad,
                'porcentaje_discapacidad': porcentaje_discapacidad,
                'estado_civil': estado_civil,
                'estado_civil_otro': estado_civil_otro,
                'etnia': etnia,
                'etnia_otro': etnia_otro
            }
        
        return clasificador_edificios, prediccion_consumo, retrieve, extraer_datos_iniciales, extraer_datos_identificacion, mostrar_formulario, continuar_al_formulario, extraer_area_consulta, extraer_datos_personales
    
    def getNodos(self, END, START):
        # Obtener tools para el llm
        clasificador_edificios, prediccion_consumo, retrieve, extraer_datos_iniciales, extraer_datos_identificacion, mostrar_formulario, continuar_al_formulario, extraer_area_consulta, extraer_datos_personales = self.getTools()
        
        def deteccion_intencion(state: State) -> Command[Literal[END, "consulta_usuario"]]:
            """Generate tool call for retrieval or respond."""
            
            current_datos = state['datos'] if state['datos'] else {}
            # comando = current_datos.get('comando', False)
            comando = False
            
            if comando:
                print("🔍 Comando detectado, generando respuesta del LLM...")
                response = self.llm.invoke(state['messages'])
                print("Respuesta del LLM en el momento que detecta comando: ")
                print(state['messages'] + [response])
                return Command(
                    update={
                        "messages": [response],
                        "datos": current_datos
                    },
                    goto=END
                )
                
            if 'continuar_form' not in current_datos:
                current_datos['continuar_form'] = False
            else:
                if current_datos['continuar_form']:
                    return Command(
                        update={
                            "messages": [],
                            "datos": current_datos
                        },
                        goto="consulta_usuario"
                    )
                
            llm_with_tools = self.llm.bind_tools([continuar_al_formulario])
            
            system_msg = SystemMessage(content=f"""{state['messages'][0].content}
                Debes empezar presentandote al usuario, tambien le mencionaras cual es tu objetivo y luego contestar a los mensajes del usuario.
                Para proceder con el llenado de la ficha de acogida de trabajo social, el usuario debe confirmarlo. En cada interaccion con el usuario puedes preguntarle al usuario sobre si desea proceder al llenado de la ficha.
            """)
            response = llm_with_tools.invoke([system_msg] + state["messages"][1:])
            messages_to_return = []
            messages_to_return.append(response)
            
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    # tool_call = response.tool_calls[0]
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    if tool_name == "continuar_al_formulario":
                        print(f"🔧 Tool llamada: {tool_name}")
                        print(f"📊 Argumentos: {tool_args}")
                        
                        # Enviar datos extraídos al EVENT_BUFFER
                        # try:
                        #     EVENT_BUFFERS[session['hilo']].put_nowait({
                        #         "nombre": tool_name,
                        #         "valor": tool_args,
                        #     })
                        # except:
                        #     pass
                        current_datos['continuar_form'] = bool(tool_args['proceder'])
                        
                        res_tool_call = ToolMessage(
                            content=f"El usuario {'procede con el formulario. Las preguntas del formulario seran descritas en las proximas interacciones, por lo que no debes alucinar preguntas al usuario por el momento.' if tool_args['proceder'] else 'no procede con el formulario por el momento, continua la conversacion.'}",
                            name=tool_name,
                            tool_call_id=tool_call['id']
                        )
                        messages_to_return.append(res_tool_call)
                        # response2 = llm_with_tools.invoke([system_msg] + state["messages"][1:] + messages_to_return)
                        # messages_to_return.append(response2)
                        
                        return Command(
                            update={
                                "messages": [],
                                "datos": current_datos
                            },
                            goto="consulta_usuario"
                        )
                
            else:
                print("El asistente respondio esto: ", response)
            
            return Command(
                update={
                    "messages": messages_to_return,
                    "datos": current_datos
                },
                goto=END
            )
            # return {"messages": messages_to_return, "datos": state['datos']}
        
        # Step 1: Generate an AIMessage that may include a tool-call to be sent.
        def consulta_usuario(state: State) -> Command[Literal[END, "consulta_usuario2"]]:
            """
            Nodo de consulta iterativo que pregunta por cada campo del formulario en orden.
            Mantiene estado de qué campos han sido completados.
            """
            # Inicializar datos si no existen
            current_datos = state['datos'] if state['datos'] else {}
            if 'form_state' not in current_datos:
                current_datos['form_state'] = {
                    'otras_secciones': [
                        # {'ficha_datos_iniciales': "Ficha de Datos Iniciales"}, 
                        {'datos_identificacion': "Datos de Identificación del Usuario"},
                        {'area_consulta': "Área de Consulta"},
                        {'datos_personales': "Datos Personales"}
                    ],
                    'seccion_actual': {'ficha_datos_iniciales': "Ficha de Datos Iniciales"},
                    'campos_completados': [], 
                    'campos_faltantes': self.data['ficha_datos_iniciales'].copy(),  # Copia de los campos para modificar
                    'completado': False
                }
                # current_datos['form_state']['campos_faltantes'] = current_datos['form_state']['seccion_actual'].values()[0].copy()

            form_state = current_datos['form_state']
            seccion_actual = list(form_state['seccion_actual'].keys())[0]
            seccion_nombre = list(form_state['seccion_actual'].values())[0]
            campos_completados = form_state['campos_completados']
            campos_faltantes = form_state['campos_faltantes']
            otras_secciones = form_state['otras_secciones']
            formulario_completado = form_state.get('completado', False)

            # Si el formulario está completado, responder como un asistente normal
            if formulario_completado:
                print("✅ Formulario ya completado. Respondiendo como asistente normal.")
                # El usuario puede hacer preguntas generales después de completar el formulario
#                 sistema_respuesta = """Eres un asistente amable y conversacional. El usuario ha completado un formulario contigo anteriormente.
# Ahora responde sus preguntas o comentarios de manera natural y útil."""
                
#                 llm_normal = self.llm.bind_tools([retrieve])
#                 mensajes_normales = [SystemMessage(content=sistema_respuesta)] + state['messages']
#                 print("Mensajes enviados al LLM para respuesta normal: ", mensajes_normales)
#                 respuesta_normal = llm_normal.invoke(mensajes_normales)
                
#                 return {
#                     "messages": [respuesta_normal],
#                     "datos": current_datos
#                 }
                return Command(
                    update={
                        "messages": [],
                        "datos": current_datos
                    },
                    goto="consulta_usuario2"
                )
            
            # Determinar el siguiente campo a preguntar
            # if campos_faltantes:
                
                # siguiente_campo = grupo_campo['id']
                
            saltar = True
            while saltar and campos_faltantes:
                grupo_campo = campos_faltantes[0]
                if not grupo_campo['saltar_si']:
                    break
                    # saltar = False
                for condicion in grupo_campo['saltar_si']:
                    saltar = True if next((completado for completado in campos_completados if completado == condicion), None) else False
                    if saltar:
                        campos_faltantes.pop(0)
                        break
                # if not saltar:
                #     valor = input(f"El asistente pregunta por el campo {campo['id']}: ")
                #     current_datos['campos_completados'].append({'id': campo['id'], 'valor': valor})
            
            if campos_faltantes:
                grupo_campo = campos_faltantes[0]
                siguiente_campo = grupo_campo['id']
                
                pregunta = grupo_campo['label'] if grupo_campo['label'] else f'¿Cuál es tu {siguiente_campo}?'
                
                # Crear mensaje del sistema mejorado
                # seccion_nombre = "Ficha de Datos Iniciales" if seccion_actual == 'ficha_datos_iniciales' else "Datos de Identificación del Usuario"
                
                progress_text = f"Completados: {len(campos_completados)}/{len(campos_completados) + len(campos_faltantes)}"
                
                system_message = {
                    'role': 'system',
                    # 'content': f"""Eres un asistente amable que está ayudando al usuario a llenar un formulario.
                    'content': f"""{state['messages'][0].content}
                                                
                        Estás llenando el formulario: {seccion_nombre}
                        

                        Ahora necesitas hacer la siguiente pregunta al usuario: {pregunta}

                        Después de que el usuario responda, extraerás el dato mencionado usando la herramienta correspondiente.
                        - Si el usuario menciona el dato solicitado, extrae SOLO ese campo
                        - Si el usuario menciona múltiples datos útiles, extrae todos los que puedas
                        - Sé flexible con las respuestas del usuario
                    """
                }
                
                # Obtener solo las tools que corresponden a la sección actual
                if seccion_actual == 'ficha_datos_iniciales':
                    llm_with_tools = self.llm.bind_tools([extraer_datos_iniciales, mostrar_formulario])
                elif seccion_actual == 'datos_identificacion':
                    llm_with_tools = self.llm.bind_tools([extraer_datos_identificacion, mostrar_formulario])
                elif seccion_actual == 'area_consulta':
                    llm_with_tools = self.llm.bind_tools([extraer_area_consulta, mostrar_formulario])
                else:
                    llm_with_tools = self.llm.bind_tools([extraer_datos_personales, mostrar_formulario])

                mensajes = [SystemMessage(content=system_message['content'])] + state['messages'][1:]
                print("Mensajes enviados al LLM: ", mensajes)
                response = llm_with_tools.invoke(
                    mensajes
                )

                # Procesar respuesta
                messages_to_return = [response]
                nuevos_campos = []
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        # tool_call = response.tool_calls[0]
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        
                        print(f"🔧 Tool llamada: {tool_name}")
                        print(f"📊 Argumentos: {tool_args}")
                        
                        if tool_name == "mostrar_formulario":
                            # messages_to_return.remove(response)
                            # mtr = [response]
                            # Enviar comando para mostrar el formulario
                            try:
                                EVENT_BUFFERS[session['hilo']].put_nowait({
                                    "nombre": tool_name,
                                    "valor": tool_args,
                                })
                            except:
                                pass
                            
                            res_tool_call = ToolMessage(
                                content=f"{'Abriste' if tool_args['abrir'] else 'Cerraste'} correctamente el formulario. Mencionale al usuario que ahora puede revisar como esta siendo llenado el formulario",
                                name=tool_name,
                                tool_call_id=tool_call['id']
                            )
                            # mtr.append(res_tool_call)
                            # response2 = self.llm.invoke(mensajes + mtr)
                            # messages_to_return.append(response2)
                            messages_to_return.append(res_tool_call)
                            # # # response2 = self.llm.invoke(state["messages"] + messages_to_return)
                            # msg2 = mensajes + messages_to_return
                            # print("Mensajes enviados al LLM después de mostrar formulario: ", msg2)
                            # response2 = self.llm.invoke(msg2)
                            # messages_to_return.append(response2)
                        else:
                            # Enviar datos extraídos al EVENT_BUFFER
                            # too_args = self.procesamiento(tool_args, campos_completados)
                            # try:
                            #     EVENT_BUFFERS[session['hilo']].put_nowait({
                            #         "nombre": "extraccion_incrementales",
                            #         "valor": tool_args,
                            #         "seccion": seccion_actual
                            #     })
                            # except:
                            #     pass
                            
                            # Actualizar estado del formulario
                            nuevos_campos = list(tool_args.keys())
                            nuevos_campos_items = list(tool_args.items())
                            tool_args_nuevo = {}
                            observacion_completo = ["Se presentaron los siguientes problemas al intentar llenar alguno de los campos del formulario: "]
                            for campo, valor in list(tool_args.items()):
                                # print("Procesando campo extraído: ", campo, valor)
                                valor, observacion = self.procesamiento(campo, valor, campos_completados)
                                if observacion: observacion_completo.append(observacion)
                                if valor:
                                    tool_args_nuevo[campo] = valor
                                    
                                    campo_faltante = next((faltantes for faltantes in campos_faltantes if faltantes['id'] == campo), None)
                                    # print("Campo encontrado en faltantes: ", campo)
                                    # if campo in campos_faltantes:
                                    if campo_faltante:
                                        campos_faltantes.remove(campo_faltante)
                                        # campos_completados.append(campo)
                                        campos_completados.append({'id': campo_faltante['id'], 'valor': valor})
                                    else:
                                        # campo_completado = next((completados for completados in campos_completados if completados['id'] == campo), None)
                                        print(f"Se reemplaza el valor del campo detectado")
                                        indice_campo = next((i for i, c in enumerate(campos_completados) if c['id'] == campo and c['valor'] != valor), -1)
                                        print(f"Indice de campo detectado '{campo}': {indice_campo}")
                                        
                                        if indice_campo >= 0: 
                                            actualizacion_campo = {'id': campo, 'valor': valor}
                                            campos_completados[indice_campo] = actualizacion_campo
                                            print(f"Campo '{campo}' actualizado con nuevo valor: {valor} en posicion {indice_campo} de completados")
                            
                            try:
                                EVENT_BUFFERS[session['hilo']].put_nowait({
                                    "nombre": "extraccion_incrementales",
                                    "valor": tool_args_nuevo,
                                    "seccion": seccion_actual
                                })
                            except:
                                pass  
                                    
                            # print("Los campos que quedan por completar son: ", [campo['id'] for campo in campos_faltantes])
                            # print("Los campos completados son: ", [campo['id'] for campo in campos_completados])
                            # Crear ToolMessage
                            contenido_res = ""
                            if len(observacion_completo) > 1:
                                contenido_res = "\n".join(observacion_completo)
                            else:
                                contenido_res = f'Extrajiste correctamente los datos: {", ".join(nuevos_campos)}'
                            
                            res_tool_call = ToolMessage(
                                content=contenido_res,
                                name=tool_name,
                                tool_call_id=tool_call['id']
                            )
                            messages_to_return.append(res_tool_call)
                            
                            if len(observacion_completo) > 1:
                                respuesta_conversacional1 = self.llm.invoke(messages_to_return)
                                messages_to_return.append(respuesta_conversacional1)
                                current_datos['form_state'] = form_state
                                return Command(
                                    update={
                                        "messages": messages_to_return,
                                        "datos": current_datos
                                    },
                                    goto=END
                                )
                            
                    # Ahora generar una respuesta del asistente DESPUÉS del ToolMessage
                    # Esto asegura que el frontend vea que está respondiendo tras procesar los datos
                    response_msg = None
                    
                    saltar = True
                    while saltar and campos_faltantes:
                        grupo_campo = campos_faltantes[0]
                        if not grupo_campo['saltar_si']:
                            break
                            # saltar = False
                        for condicion in grupo_campo['saltar_si']:
                            saltar = True if next((completado for completado in campos_completados if completado == condicion), None) else False
                            if saltar:
                                campos_faltantes.pop(0)
                                break
                    
                    
                    if campos_faltantes:
                        print("Los campos que quedan por completar son: ", [campo['id'] for campo in campos_faltantes])
                        print("Los campos completados son: ", [campo['id'] for campo in campos_completados])
                        grupo_campo_nuevo = campos_faltantes[0]
                        siguiente_campo_nuevo = grupo_campo_nuevo['id']
                        # Generar respuesta que incluya confirmación y siguiente pregunta
                        # siguiente_campo_nuevo = campos_faltantes[0]
                        # pregunta_siguiente = preguntas.get(siguiente_campo_nuevo, f'¿Cuál es tu {siguiente_campo_nuevo}?')
                        print("Segunda iteracion, se pregunta por campo: ", siguiente_campo_nuevo)
                        pregunta_siguiente = grupo_campo_nuevo['label'] if grupo_campo_nuevo['label'] else f'¿Cuál es tu {siguiente_campo_nuevo}?'
                        
                        txt_nuevos_campos = f"El usuario acaba de proporcionar los siguientes campos: {', '.join([f'{ckey}={cvalue}' for ckey, cvalue in nuevos_campos_items])}" if nuevos_campos_items else "El usuario no ha proporcionado valores para ningún campo todavia."
                        # Invocar LLM SIN tools para generar una respuesta conversacional natural
                        prompt_respuesta = f"""
                        Eres un asistente amable. {txt_nuevos_campos}.
                        Ahora necesitas:
                        1. Confirmar que recibiste correctamente la información
                        2. Hacer la siguiente pregunta: "{pregunta_siguiente}"
                        
                        Sé breve y conversacional. La confirmación y pregunta deben estar en un solo mensaje natural.
                        """
                        
                        respuesta_conversacional = self.llm.invoke([
                            SystemMessage(content=prompt_respuesta)
                        ])
                        messages_to_return.append(respuesta_conversacional)
                        response_msg = respuesta_conversacional
                    # Verificar si debemos cambiar de sección
                    else:
                        if len(otras_secciones) > 0:
                            siguiente_seccion = otras_secciones.pop(0)
                            seccion_sigte = list(siguiente_seccion.keys())[0]
                            seccion_nombre_sigte = list(siguiente_seccion.values())[0]
                            # Cambiar a la siguiente sección
                            # form_state['otras_secciones'] = otras_secciones.copy()
                            form_state['seccion_actual'] = siguiente_seccion
                            form_state['campos_faltantes'] = self.data[seccion_sigte].copy()
                            form_state['campos_completados'] = []
                            
                            # Generar respuesta conversacional para el cambio de sección
                            grupo_campo_nueva_seccion = form_state['campos_faltantes'][0]
                            siguiente_campo_nueva_seccion = grupo_campo_nueva_seccion['id']
                            # siguiente_campo_nueva_seccion = form_state['campos_faltantes'][0]
                            # pregunta_nueva_seccion = preguntas.get(siguiente_campo_nueva_seccion, f'¿Cuál es tu {siguiente_campo_nueva_seccion}?')
                            pregunta_nueva_seccion = grupo_campo_nueva_seccion['label'] if grupo_campo_nueva_seccion['label'] else f'¿Cuál es tu {siguiente_campo_nueva_seccion}?'
                            
                            prompt_cambio_seccion = f"""
                            Eres un asistente amable. El usuario acaba de completar la '{seccion_nombre}' proporcionando: {', '.join([f'{ckey}={cvalue}' for ckey, cvalue in nuevos_campos_items])}.
                            Ahora necesitas:
                            1. Confirmar que recibiste correctamente la información
                            2. Indicar que hemos completado esa sección
                            3. Anunciar que comenzaremos con la sección '{seccion_nombre_sigte}'
                            4. Hacer la primera pregunta de la nueva sección: "{pregunta_nueva_seccion}"
                            
                            Sé breve y conversacional. Todo debe estar en un solo mensaje natural que fluya bien.
                            """
                            
                            msg_cambio_seccion = self.llm.invoke([
                                SystemMessage(content=prompt_cambio_seccion)
                            ])
                            messages_to_return.append(msg_cambio_seccion)
                            response_msg = msg_cambio_seccion
                    # else:
                    #     form_state['campos_faltantes'] = campos_faltantes
                    #     form_state['campos_completados'] = campos_completados
                        else:
                            # Si se completaron todos los campos de todas las secciones
                            form_state['completado'] = True  # Marcar formulario como completado
                            msg_fin = AIMessage(content="""Has completado todas las preguntas del formulario. Has registrado toda la información del usuario:
    • Sección 1 - Ficha de Datos Iniciales (9 campos completados)
    • Sección 2 - Datos de Identificación del Usuario (13 campos completados)
    • Sección 3 - Área de Consulta (1 campo completado)
    • Sección 4 - Datos Personales (5 campos completados)

    Invita al usuario a revisar el formulario para verificar que todos sus datos se registraron correctamente.""")
                            respuesta_conversacional = self.llm.invoke(
                                state['messages'] + [msg_fin]
                            )
                            # Enviar datos extraídos al EVENT_BUFFER
                            try:
                                EVENT_BUFFERS[session['hilo']].put_nowait({
                                    "nombre": "mostrar_formulario",
                                    "valor": {"abrir": True}
                                })
                            except:
                                pass
                            messages_to_return.append(respuesta_conversacional)
                
                else:
                    # Si no hay tool call, el LLM está siendo conversacional
                    print("💬 Respuesta conversacional del LLM")
                
                current_datos['form_state'] = form_state
                # return {
                #     "messages": messages_to_return,
                #     "datos": current_datos
                # }
                print("Estado actual del formulario al finalizar la iteracion: ", form_state)
                return Command(
                    update={
                        "messages": messages_to_return,
                        "datos": current_datos
                    },
                    goto=END
                ) 
            else:
                print("✅ Todos los campos del formulario han sido completados.")
                form_state['completado'] = True  # Marcar formulario como completado
                # Todos los campos completados
                # return {
                #     "messages": [AIMessage(content="¡Excelente! He completado todas las preguntas del formulario. He registrado toda tu información:\n• Sección 1 - Ficha de Datos Iniciales (9 campos completados)\n• Sección 2 - Datos de Identificación del Usuario (13 campos completados)\n\nAhora te invito a revisar el formulario para verificar que todos tus datos se registraron correctamente. Por favor, tómate un momento para revisar cada sección y confirmar que la información es exacta.")],
                #     "datos": current_datos
                # }
                return Command(
                    update={
                        "messages": [AIMessage(content="¡Excelente! He completado todas las preguntas del formulario. He registrado toda tu información:\n• Sección 1 - Ficha de Datos Iniciales (9 campos completados)\n• Sección 2 - Datos de Identificación del Usuario (13 campos completados)\n\nAhora te invito a revisar el formulario para verificar que todos tus datos se registraron correctamente. Por favor, tómate un momento para revisar cada sección y confirmar que la información es exacta.")],
                        "datos": current_datos
                    },
                    goto=END
                )
        
        # Step 1: Generate an AIMessage that may include a tool-call to be sent.
        
        def consulta_usuario2(state: State):
            current_datos = state['datos'] if state['datos'] else {}
            # El usuario puede hacer preguntas generales después de completar el formulario
            sistema_respuesta = """Eres un asistente amable y conversacional. El usuario ha completado un formulario contigo anteriormente.
Ahora responde sus preguntas o comentarios de manera natural y útil."""
            
            llm_normal = self.llm.bind_tools([retrieve])
            mensajes_normales = [SystemMessage(content=sistema_respuesta)] + state['messages']
            print("Mensajes enviados al LLM para respuesta normal: ", mensajes_normales)
            respuesta_normal = llm_normal.invoke(mensajes_normales)
            
            return {
                "messages": [respuesta_normal],
                "datos": current_datos
            }
        
        def consulta_usuario5(state: State):
            """Generate tool call for retrieval or respond."""
            llm_with_tools = self.llm.bind_tools([retrieve, clasificador_edificios, prediccion_consumo])
            response = llm_with_tools.invoke(state["messages"])

            #response = llm.invoke(state["messages"])
            # State appends messages to state instead of overwriting
            return {"messages": [response], "datos": state['datos'] if state['datos'] else {}}
        
        def tools_node(state: State):
            """Ejecuta la herramienta retrieve y devuelve el ToolMessage."""
            message = state["messages"][-1]
            tool_call = message.tool_calls[0]
            
            if tool_call['name'] == 'retrieve':
                # Ejecutar retrieve y obtener el contenido
                query = tool_call['args'].get('query', '')
                retrieved_docs = self.vector_store.similarity_search(query, k=2)
                serialized = "\n\n".join(
                    (f"Source: {doc.metadata}\nContent: {doc.page_content}")
                    for doc in retrieved_docs
                )
                
                # Crear ToolMessage con el mismo tool_call_id
                tool_message = ToolMessage(
                    content=serialized,
                    name='retrieve',
                    tool_call_id=tool_call['id']
                )
                
                return {"messages": [tool_message], "datos": state['datos'] if state['datos'] else {}}
            
            return {"messages": [], "datos": state['datos'] if state['datos'] else {}}
        
        def get_intencion(state: State):
            """Generate tool call for retrieval or respond."""
            print("\nSTATE: ", state["messages"], "\n")
            message = state["messages"][-1]
            next_msg = {"messages": [], "datos": state['datos'] if state['datos'] else {}}
            next_node = END
            if message.tool_calls:
                tool_call = message.tool_calls[0]

                if tool_call['name'] == 'clasificador_edificios':
                    print("Argumentos: ", tool_call["args"])
                    print("Se dirige a nodo consumo")
                    next_node = "nodo_consumo"
                    
                elif tool_call['name'] == 'prediccion_consumo':
                    print("Argumentos: ", tool_call["args"])
                    next_node = "nodo_prediccion"
                    
                elif tool_call['name'] == 'retrieve':
                    print("Argumentos: ", tool_call["args"])
                    next_node = "tools"
                    
                else:
                    next_node = END
                
            else:
                print("Normal: ", message)
            
            return Command(
                update=next_msg,
                goto=next_node
            )
        
        
        def generate(state: State):
            """Generate answer."""
            print("\nSTATE: ", state["messages"], "\n")
            # Get generated ToolMessages
            recent_tool_messages = []
            for message in reversed(state["messages"]):
                if message.type == "tool":
                    recent_tool_messages.append(message)
                else:
                    break
            tool_messages = recent_tool_messages[::-1]

            # Format into prompt
            docs_content = "\n\n".join(doc.content for doc in tool_messages)
            system_message_content = (
                "Eres un asistente para tareas de preguntas y respuestas."
                "Usa las siguientes partes del contexto recuperado para responder la pregunta."
                "Si no sabes la respuesta, di que no lo sabes."
                "Usa un máximo de tres oraciones y mantén la respuesta concisa."
                "\n\n"
                f"{docs_content}"
            )
            print("Prompt: ", system_message_content)
            conversation_messages = [
                message
                for message in state["messages"]
                if message.type in ("human", "system")
                or (message.type == "ai" and not message.tool_calls)
            ]
            prompt = [SystemMessage(system_message_content)] + conversation_messages

            # Run
            response = self.llm.invoke(prompt)
            return {"messages": [response], "datos": {}}
        
        def nodo_consumo(state: State):
            message = state["messages"][-1]
            datos_consumo = state['datos']
            tool_call = message.tool_calls[0]

            print("Entrada a nodo consumo")
            print("\nSTATE: ", state["messages"], "\n")
            parametros = {
                'edificio': norm(tool_call["args"].get('edificio', '')), 
                'piso': norm(tool_call["args"].get('piso', '')), 
                'ambiente': norm(tool_call["args"].get('ambiente', '')), 
                'fechainicio': tool_call["args"].get('fecha_inicio', ''), 
                'fechafin': tool_call["args"].get('fecha_fin', '')
            }

            info = getInfoLugar(parametros, self.data)

            res_tool_call = ToolMessage(
                content='Extrajiste los datos correctamente', 
                name=tool_call['name'],
                tool_call_id=tool_call['id']
            )
            
            next_msg = {"messages": [res_tool_call], "datos": {}}
            if info['ok']:

                params = info['datos'][0]

                datos = self.getConsumoEdificios(params['edificio']['id'], params['piso']['id'], params['ambiente']['id'], params['fecha_inicio'], params['fecha_fin'])
                
                # Si todo OK -> guardar datos en sesion -> Avanzar a nodo decision
                if datos['res']:
                    datos['data']['params'] = {
                        'idEdificio': params['edificio']['id'], 'edificio':params['edificio']['nombre'],  
                        'idPiso': params['piso']['id'], 'piso':params['piso']['nombre'], 
                        'idAmbiente': params['ambiente']['id'], 'ambiente':params['ambiente']['nombre'], 
                        'fechaInicio': params['fecha_inicio'], 'fechaFin': params['fecha_fin']
                    }
                    
                    EVENT_BUFFERS[session['hilo']].put_nowait({
                        "nombre": "solicita_datos_consumo",
                        "valor": datos['data']
                    })

                    #sesion['info']['consumo'] = datos['data']

                    #memory.put('abc123', 'datos_consumo', datos['data'])
                    datos_consumo['consumo'] = datos['data']

                    system_message = {
                        'role': 'system',
                        'content': """
                            Eres un asistente util capaz de predecir el consumo a futuro para la siguiente semana, y para ello 
                            necesitas saber datos como el nombre del edificio, el nombre del piso y el nombre del ambiente de donde 
                            obtendras los valores de consumo actual, aparte de eso, necesitas saber que dias seran feriado o de evento 
                            especial la siguiente semana.
                        """
                    }
                    user_message = {"role": "user", "content": f"Ya conoces la siguiente informacion: el edificio es {parametros['edificio']}, el piso es {parametros['piso']} y el ambiente es {parametros['ambiente']}. Debes preguntarle al usuario que dias con novedades habra para la siguiente semana para poder calcular la prediccion."}
                
                    res_human = HumanMessage(content=user_message['content'])
                    response = self.llm.invoke([system_message, user_message])
                    # res_ai = AIMessage(content=response.content)
                    
                    next_msg = {"messages": [res_tool_call, res_human, response], "datos": datos_consumo}
                    next_node = "conector_consumo_prediccion"
                else:
                    system_message = {
                        'role': 'system', 
                        'content': """
                            Eres un asistente de consumo energetico, y te encargas de notificar al usuario sobre los errores de consulta del usuario o del mismo sistema.
                            Responderas en base a la conversacion.
                        """
                    }
                    user_message = {"role": "user", "content": datos['observacion']}
                    response = self.llm.invoke([system_message, user_message])
                    #response.id = state["messages"][-1].id

                    res_human = HumanMessage(content=user_message['content'])
                    #res_ai = AIMessage(content=response.content)
                    
                    next_msg = {"messages": [res_tool_call, res_human, response], "datos": datos_consumo}
            else:
                system_message = {
                    'role': 'system', 
                    'content': """
                        Eres un asistente de consumo energetico, y te encargas de notificar al usuario sobre los errores de consulta del usuario o del mismo sistema.
                        Responderas en base a la conversacion.
                    """
                }
                user_message = {"role": "user", "content": info['datos']}
                response = self.llm.invoke([system_message, user_message])
                #response.id = state["messages"][-1].id

                res_human = HumanMessage(content=user_message['content'])
                #res_ai = AIMessage(content=response.content)
                
                next_msg = {"messages": [res_tool_call, res_human, response], "datos": datos_consumo}

            # Validador de extractor de entidades en caso de que fuera falso -> avanzar a nodo bucle
            return next_msg
        
        def nodo_consumoxd(state: State):
            message = state["messages"][-1]
            datos_consumo = state['datos']
            tool_call = message.tool_calls[0]

            print("Entrada a nodo consumo")
            print("\nSTATE: ", state["messages"], "\n")
            parametros = {
                'edificio': norm(tool_call["args"].get('edificio', '')), 
                'piso': norm(tool_call["args"].get('piso', '')), 
                'ambiente': norm(tool_call["args"].get('ambiente', '')), 
                'fechainicio': tool_call["args"].get('fecha_inicio', ''), 
                'fechafin': tool_call["args"].get('fecha_fin', '')
            }

            info = getInfoLugar(parametros, self.data)
            print(info)

            params = info['datos'][0]

            datos = self.getConsumoEdificios(params['edificio']['id'], params['piso']['id'], params['ambiente']['id'], params['fecha_inicio'], params['fecha_fin'])
            
            res_tool_call = ToolMessage(
                content='Extrajiste los datos correctamente', 
                name=tool_call['name'],
                tool_call_id=tool_call['id']
            )
            next_msg = {"messages": [res_tool_call], "datos": {}}
            next_node = END
            # Si todo OK -> guardar datos en sesion -> Avanzar a nodo decision
            if datos['res']:
                datos['data']['params'] = {
                    'idEdificio': params['edificio']['id'], 'edificio':params['edificio']['nombre'],  
                    'idPiso': params['piso']['id'], 'piso':params['piso']['nombre'], 
                    'idAmbiente': params['ambiente']['id'], 'ambiente':params['ambiente']['nombre'], 
                    'fechaInicio': params['fecha_inicio'], 'fechaFin': params['fecha_fin']
                }
                
                EVENT_BUFFERS[session['hilo']].put_nowait({
                    "nombre": "solicita_datos_consumo",
                    "valor": datos['data']
                })

                #sesion['info']['consumo'] = datos['data']

                #memory.put('abc123', 'datos_consumo', datos['data'])
                datos_consumo['consumo'] = datos['data']

                system_message = {
                    'role': 'system',
                    'content': """
                        Eres un asistente util capaz de predecir el consumo a futuro para la siguiente semana, y para ello 
                        necesitas saber datos como el nombre del edificio, el nombre del piso y el nombre del ambiente de donde 
                        obtendras los valores de consumo actual, aparte de eso, necesitas saber que dias seran feriado o de evento 
                        especial la siguiente semana.
                    """
                }
                user_message = {"role": "user", "content": f"Ya conoces la siguiente informacion: el edificio es {parametros['edificio']}, el piso es {parametros['piso']} y el ambiente es {parametros['ambiente']}. Debes preguntarle al usuario que dias con novedades habra para la siguiente semana para poder calcular la prediccion."}
            
                response = self.llm.invoke([system_message, user_message])
                res_human = HumanMessage(content=user_message['content'])
                # res_ai = AIMessage(content=response.content)
                
                next_msg = {"messages": [res_tool_call, res_human, response], "datos": datos_consumo}
                next_node = "conector_consumo_prediccion"
            else:
                system_message = {
                    'role': 'system', 
                    'content': """
                        Eres un asistente de consumo energetico, y te encargas de notificar al usuario sobre los errores de consulta del usuario o del mismo sistema.
                        Responderas en base a la conversacion.
                    """
                }
                user_message = {"role": "user", "content": datos['observacion']}
                response = self.llm.invoke([system_message, user_message])
                #response.id = state["messages"][-1].id

                res_human = HumanMessage(content=user_message['content'])
                #res_ai = AIMessage(content=response.content)
                
                next_msg = {"messages": [res_tool_call, res_human, response], "datos": datos_consumo}
                next_node = END

            # Validador de extractor de entidades en caso de que fuera falso -> avanzar a nodo bucle
            return Command(
                update = next_msg,
                goto = next_node
            )
        
        def conector_consumo_prediccion(state: State): # -> Command[Literal[END, "nodo_prediccion"]]:
            message = state["messages"][-1]
            datos_consumo = state['datos']
            
            print("Entrando a nodo conector entre consumo y prediccion")
            print("\nSTATE: ", state["messages"], "\n")
            #print("Respuesta a pregunta", message)
            
            admin = interrupt("dias_novedad")

            #parametros = sesion['info']['consumo']['params']
            txt_adicional = ""
            if datos_consumo and datos_consumo['consumo']:
                parametros = datos_consumo['consumo']['params']
                txt_adicional = f"El edificio es {parametros['edificio']}, el piso es {parametros['piso']} y el ambiente es {parametros['ambiente']}"
            # user_message = {"role": "user", "content": f"""
            #     En este punto de la conversacion, el usuario tiene que mencionarte un dia o varios dias de la semana con novedades (si es feriado, especial o normal).
            #     En caso de que el usuario mencione al menos un dia entenderas que el desea saber la prediccion para la siguiente semana con esos dias de novedad.
            #     Adicional a esa informacion de los dias, tienes datos como que el edificio es {parametros['edificio']}, el piso es {parametros['piso']} y el ambiente es {parametros['ambiente']}."""}
            system_message = {
                'role': 'system',
                'content': """Eres un asistente util, tu objetivo sera intuir que el usuario necesita saber la prediccion del consumo de la siguiente semana o si es algo diferente.
                    Determinaras si el usuario quiere saber la prediccion a futuro cuando te mencione si uno o varios dias seran feriado, especial o dia normal.
                    Si el usuario responde o pregunta por algo diferente, entonces intuiras que su intencion no es saber el consumo a futuro."""
            }
            # user_message = {"role": "user", "content": f"Deseo saber cual sera la prediccion para la siguiente semana, sabiendo que {admin}. {txt_adicional}"}
            user_message = {"role": "user", "content": f"Consulta del usuario: {admin}"}
            
            #print(user_message)
            
            llm_with_tools = self.llm.bind_tools([prediccion_consumo])
            response = llm_with_tools.invoke([system_message, user_message])
            
            print(response)
            
            # res_human = HumanMessage(content=user_message['content'])
            # all_msgs = [res_human, response]
            #response = llm.invoke([system_message])
            #response.id = state["messages"][-1].id

            # next_node = END
            res_human = [HumanMessage(content=admin)]
    
            if response.tool_calls:
                print("Tool en consumo nodo")
                tool_call = response.tool_calls[0]
                
                if tool_call['name'] == 'prediccion_consumo':
                    print("Argumentos: ", tool_call["args"])
                    print("Se dirige a nodo prediccion desde nodo conector")
                    # next_node = "nodo_prediccion"
                    user_message = {"role": "user", "content": f"Deseo saber cual sera la prediccion para la siguiente semana, sabiendo que {admin}. {txt_adicional}"}
                    res_human = [HumanMessage(content=user_message['content'])]
                
            return {"messages": res_human, "datos": datos_consumo}
        
        return consulta_usuario, tools_node, get_intencion, generate, nodo_consumo, conector_consumo_prediccion, consulta_usuario2, deteccion_intencion
    
    def analizar_similitud(self, entrada_voz, lista_datos):
        # Lo que el modelo de voz entendió mal
        # entrada_voz = "Quininde"
        # entrada_voz = lista_datos[i]
        
        # Limpieza básica y comparación
        entrada_voz = self.normalizar_texto(entrada_voz)
        lista_datos_lower = [self.normalizar_texto(lc) for lc in lista_datos]
        resultado = process.extractOne(
            entrada_voz, 
            # ciudades_validas, 
            lista_datos_lower,
            # processor=utils.default_process
            scorer=fuzz.token_sort_ratio
        )
        
        nombre_corregido, score, indice = resultado
        # print(indice)
        # print(f"Detectada: {entrada_voz} -> Ciudad registrada: {nombre_corregido} (Similitud: {score}%)")
        # ciudades = {'detectada': entrada_voz, 'registrada': nombre_corregido, 'similitud': score}
        ciudades = {'detectada': entrada_voz, 'registrada': lista_datos[indice], 'similitud': score}
        # if score > 85:
        # else:
        #     ciudades = {}
        return ciudades
    
    def procesamiento(self, campo, valor, extra=None):
        observacion = ""
        if campo in ['provincia', 'ciudad', 'parroquia']:
            datos = None
            if campo == 'provincia':
                sql = """SELECT p.nombre AS provincia FROM bienestar.provincias p;"""
                resultado = self.db.consultarDatos(sql)
                datos = [r['provincia'] for r in resultado]
            elif campo == 'ciudad':
                campo_provincia = next((faltantes for faltantes in extra if faltantes['id'] == 'provincia'), None)
                # if extra and 'provincia' in extra:
                if campo_provincia:
                    sql = f"""
                        SELECT c.nombre AS ciudad 
                        FROM bienestar.cantones c 
                        JOIN bienestar.provincias p ON c.provincia_id = p.id 
                        WHERE p.nombre = \'{campo_provincia['valor']}\';
                    """
                    resultado = self.db.consultarDatos(sql)
                    datos = [r['ciudad'] for r in resultado]
                # resultado = self.db.consultarDatos("""SELECT c.nombre AS ciudad FROM bienestar.cantones c;""")
            elif campo == 'parroquia':
                campo_provincia = next((faltantes for faltantes in extra if faltantes['id'] == 'provincia'), None)
                campo_ciudad = next((faltantes for faltantes in extra if faltantes['id'] == 'ciudad'), None)
                # if extra and 'provincia' in extra:
                if campo_provincia and campo_ciudad:
                    sql = f"""
                        SELECT 
                            pr.nombre AS parroquia 
                        FROM bienestar.parroquias pr
                        JOIN bienestar.cantones c ON pr.canton_id = c.id
                        JOIN bienestar.provincias p ON c.provincia_id = p.id
                        WHERE p.nombre = \'{campo_provincia['valor']}\' AND c.nombre = \'{campo_ciudad['valor']}\';
                    """
                    resultado = self.db.consultarDatos(sql)
                    datos = [r['parroquia'] for r in resultado]
                # resultado = self.db.consultarDatos("""SELECT p.nombre AS parroquia FROM bienestar.parroquias p;""")
                # datos = [r['parroquia'] for r in resultado]
                
            if datos:
                dato_analizado = self.analizar_similitud(valor, datos)
                
                if dato_analizado and dato_analizado['similitud'] > 80:
                    valor = dato_analizado['registrada']
                else:
                    if dato_analizado and dato_analizado['similitud'] > 55:
                        # valor = dato_analizado['registrada']
                        observacion = f"- En cuanto a la {campo} puede que el usuario se quiera referir a \'{dato_analizado['registrada']}\'"
                    else:
                        observacion = f"- No existe {campo} registrada como '{valor}'."
                    valor = None
                # valor = dato_analizado['registrada']
                print(f"El valor mas similar es ", valor)
                print(observacion)
        elif campo in ['facultad', 'carrera']:
            # Aquí podrías implementar lógica similar para facultades y carreras si es necesario
            datos = None
            if campo == 'facultad':
                valor = re.sub(r'^(facultad\s+(de\s+)?)', '', valor, flags=re.IGNORECASE).strip()
                sql = """SELECT f.nombre AS facultad FROM bienestar.facultades f;"""
                resultado = self.db.consultarDatos(sql)
                datos = [r['facultad'] for r in resultado]
            elif campo == 'carrera':
                campo_facultad = next((faltantes for faltantes in extra if faltantes['id'] == 'facultad'), None)
                # if extra and 'provincia' in extra:
                if campo_facultad:
                    sql = f"""
                        SELECT c.nombre AS carrera 
                        FROM bienestar.carreras c 
                        JOIN bienestar.facultades f ON f.codigo  = c.facultades_id 
                        WHERE f.nombre = \'{campo_facultad['valor']}\';
                    """
                    resultado = self.db.consultarDatos(sql)
                    datos = [r['carrera'] for r in resultado]
                # resultado = self.db.consultarDatos("""SELECT c.nombre AS carrera FROM bienestar.carreras c;""")
                
            if datos:
                dato_analizado = self.analizar_similitud(valor, datos)
                
                if dato_analizado and dato_analizado['similitud'] > 80:
                    valor = dato_analizado['registrada']
                else:
                    if dato_analizado and dato_analizado['similitud'] > 55:
                        # valor = dato_analizado['registrada']
                        observacion = f"- El usuario menciono la {campo} de {valor}. Es probable que se refiera a \'{dato_analizado['registrada']}\'. Mencionaselo para que confirme si es correcto."
                    else:
                        observacion = f"- El usuario menciono la {campo} carrera '{valor}'. Pero esta no se encuentra registrada."
                    valor = None
                # valor = dato_analizado['registrada']
                print(f"El valor mas similar es ", valor)
                print(observacion)
        return valor, observacion
    
    def normalizar_texto(self, texto):
        """
        Convierte a minúsculas, elimina tildes y caracteres especiales.
        Ejemplo: 'SAN JOSÉ DE ANCÓN' -> 'san jose de ancon'
        """
        if not texto:
            return ""
        
        # Convertir a minúsculas
        texto = texto.lower()
        texto = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', texto)
        
        # Descomponer caracteres Unicode (NFD separa la letra de su tilde)
        texto = unicodedata.normalize('NFD', texto)
        
        # Filtrar solo los caracteres que no sean marcas de acentuación (Non-Spacing Marks)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        
        return texto
    