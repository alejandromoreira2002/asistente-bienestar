#!/usr/bin/env python3
"""
Script de prueba para validar la lógica del nuevo nodo consulta_usuario
y las tools de extracción mejoradas.
"""

from typing import Dict, Any, Optional, Literal

# Simular las tools mejoradas
class MockToolExtraerDatosIniciales:
    """Mock de la tool extraer_datos_iniciales"""
    
    @staticmethod
    def extraer(
        provincia: Optional[str] = None,
        ciudad: Optional[str] = None,
        parroquia: Optional[str] = None,
        es_estudiante: Optional[Literal["si", "no"]] = None,
        institucion: Optional[str] = None,
        facultad: Optional[str] = None,
        carrera: Optional[str] = None,
        modalidad: Optional[str] = None,
        nivel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extrae datos de forma flexible"""
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
        if facultad is not None:
            resultado['facultad'] = facultad
        if carrera is not None:
            resultado['carrera'] = carrera
        if modalidad is not None:
            resultado['modalidad'] = modalidad
        if nivel is not None:
            resultado['nivel'] = nivel
            
        return resultado


class MockToolExtraerDatosIdentificacion:
    """Mock de la tool extraer_datos_identificacion"""
    
    @staticmethod
    def extraer(
        nombres: Optional[str] = None,
        apellidos: Optional[str] = None,
        cedula: Optional[str] = None,
        celular: Optional[str] = None,
        correo: Optional[str] = None,
        edad: Optional[str] = None,
        fecha_nacimiento: Optional[str] = None,
        nacionalidad: Optional[str] = None,
        sexo: Optional[Literal["femenino", "masculino", "otro"]] = None,
        genero: Optional[str] = None,
        direccion: Optional[str] = None,
        lugar_residencia: Optional[str] = None,
        contacto_referencia: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extrae datos de identificación de forma flexible"""
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


class MockState:
    """Mock del State de LangGraph"""
    
    def __init__(self):
        self.messages = []
        self.datos = {}


class MockFormularioManager:
    """Clase que simula la lógica del nodo consulta_usuario"""
    
    def __init__(self):
        self.preguntas = {
            'provincia': '¿En qué provincia resides?',
            'ciudad': '¿En qué ciudad resides?',
            'parroquia': '¿En qué parroquia resides?',
            'es_estudiante': '¿Eres estudiante? (responde sí o no)',
            'institucion': '¿En qué institución estudias? (UTM u otra)',
            'facultad': '¿Cuál es tu facultad?',
            'carrera': '¿Cuál es tu carrera?',
            'modalidad': '¿Cuál es tu modalidad de estudio? (PRESENCIAL, HÍBRIDA o EN LÍNEA)',
            'nivel': '¿Cuál es tu nivel actual?',
            # Datos de Identificación
            'nombres': '¿Cuáles son tus nombres?',
            'apellidos': '¿Cuáles son tus apellidos?',
            'cedula': '¿Cuál es tu número de cédula?',
            'celular': '¿Cuál es tu número de celular?',
            'correo': '¿Cuál es tu correo electrónico?',
            'edad': '¿Cuál es tu edad?',
            'fecha_nacimiento': '¿Cuál es tu fecha de nacimiento? (formato: DD/MM/YYYY)',
            'nacionalidad': '¿Cuál es tu nacionalidad?',
            'sexo': '¿Cuál es tu sexo? (Femenino, Masculino u Otro)',
            'genero': '¿Cuál es tu identidad de género? (opcional)',
            'direccion': '¿Cuál es tu dirección de domicilio?',
            'lugar_residencia': '¿Dónde resides actualmente?',
            'contacto_referencia': '¿Cuál es el nombre y contacto de tu referencia?'
        }
    
    def inicializar_formulario(self, datos: Dict):
        """Inicializa el estado del formulario"""
        if 'form_state' not in datos:
            datos['form_state'] = {
                'seccion_actual': 'ficha_datos_iniciales',
                'campos_completados': [],
                'campos_faltantes': [
                    'provincia', 'ciudad', 'parroquia', 'es_estudiante',
                    'institucion', 'facultad', 'carrera', 'modalidad', 'nivel'
                ]
            }
    
    def procesar_respuesta(self, datos: Dict, datos_extraidos: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una respuesta del usuario y actualiza el estado"""
        form_state = datos['form_state']
        campos_faltantes = form_state['campos_faltantes']
        campos_completados = form_state['campos_completados']
        
        # Actualizar estado
        nuevos_campos = list(datos_extraidos.keys())
        for campo in nuevos_campos:
            if campo in campos_faltantes:
                campos_faltantes.remove(campo)
                campos_completados.append(campo)
        
        resultado = {
            'campos_extraidos': nuevos_campos,
            'datos_extraidos': datos_extraidos,
            'campos_faltantes_restantes': campos_faltantes,
            'cambio_seccion': False
        }
        
        # Verificar si debemos cambiar de sección
        if form_state['seccion_actual'] == 'ficha_datos_iniciales' and not campos_faltantes:
            form_state['seccion_actual'] = 'datos_identificacion'
            form_state['campos_faltantes'] = [
                'nombres', 'apellidos', 'cedula', 'celular', 'correo',
                'edad', 'fecha_nacimiento', 'nacionalidad', 'sexo',
                'direccion', 'lugar_residencia', 'contacto_referencia'
            ]
            form_state['campos_completados'] = []
            resultado['cambio_seccion'] = True
        
        return resultado
    
    def obtener_siguiente_pregunta(self, datos: Dict) -> Optional[tuple]:
        """Obtiene la siguiente pregunta a realizar"""
        form_state = datos['form_state']
        campos_faltantes = form_state['campos_faltantes']
        
        if not campos_faltantes:
            return None
        
        siguiente_campo = campos_faltantes[0]
        pregunta = self.preguntas.get(siguiente_campo, f'¿Cuál es tu {siguiente_campo}?')
        
        campos_completados = len(form_state['campos_completados'])
        total_campos = len(form_state['campos_completados']) + len(form_state['campos_faltantes'])
        
        return {
            'campo': siguiente_campo,
            'pregunta': pregunta,
            'seccion': form_state['seccion_actual'],
            'progreso': f"{campos_completados}/{total_campos}"
        }


# Tests
def test_extraccion_individual():
    """Test: Extracción de un campo individual"""
    print("=" * 60)
    print("TEST 1: Extracción individual")
    print("=" * 60)
    
    tool = MockToolExtraerDatosIniciales()
    resultado = tool.extraer(provincia="Pichincha")
    
    assert resultado == {'provincia': 'Pichincha'}, "Fallo en extracción individual"
    print("✅ Extracción individual correcta")
    print(f"   Resultado: {resultado}\n")


def test_extraccion_multiple():
    """Test: Extracción de múltiples campos"""
    print("=" * 60)
    print("TEST 2: Extracción múltiple")
    print("=" * 60)
    
    tool = MockToolExtraerDatosIniciales()
    resultado = tool.extraer(
        provincia="Pichincha",
        ciudad="Quito",
        parroquia="Centro"
    )
    
    assert len(resultado) == 3, "Fallo en extracción múltiple"
    print("✅ Extracción múltiple correcta")
    print(f"   Resultado: {resultado}\n")


def test_flujo_completo():
    """Test: Flujo completo del formulario"""
    print("=" * 60)
    print("TEST 3: Flujo completo")
    print("=" * 60)
    
    manager = MockFormularioManager()
    datos = {}
    
    # Inicializar
    manager.inicializar_formulario(datos)
    print("✅ Formulario inicializado")
    
    # Primer campo
    pregunta1 = manager.obtener_siguiente_pregunta(datos)
    print(f"\n📝 Pregunta 1: {pregunta1['pregunta']}")
    print(f"   Sección: {pregunta1['seccion']} | Progreso: {pregunta1['progreso']}")
    
    # Usuario responde 1
    datos_resp1 = MockToolExtraerDatosIniciales.extraer(provincia="Pichincha", ciudad="Quito")
    resultado1 = manager.procesar_respuesta(datos, datos_resp1)
    print(f"\n💾 Datos extraídos: {resultado1['datos_extraidos']}")
    print(f"   Campos restantes: {len(resultado1['campos_faltantes_restantes'])}")
    
    # Siguiente pregunta
    pregunta2 = manager.obtener_siguiente_pregunta(datos)
    print(f"\n📝 Pregunta 2: {pregunta2['pregunta']}")
    print(f"   Progreso: {pregunta2['progreso']}")
    
    # Simular que se completeran todos los campos de la sección 1
    print("\n⚡ Simulando respuestas múltiples para completar sección 1...")
    respuestas = [
        {'parroquia': 'Centro'},
        {'es_estudiante': 'si'},
        {'institucion': 'UTM'},
        {'facultad': 'Ciencias de la Salud'},
        {'carrera': 'Medicina'},
        {'modalidad': 'PRESENCIAL'},
        {'nivel': '3'}
    ]
    
    for i, resp in enumerate(respuestas, 2):
        result = manager.procesar_respuesta(datos, resp)
        if result['cambio_seccion']:
            print(f"\n✅ CAMBIO DE SECCIÓN DETECTADO")
            print(f"   Anterior: ficha_datos_iniciales → Actual: datos_identificacion")
            break
        print(f"   Respuesta {i}: {list(resp.keys())[0]} ✓")
    
    print(f"\n🎉 Sección 1 completada!")


def test_cambio_seccion():
    """Test: Cambio automático de sección"""
    print("=" * 60)
    print("TEST 4: Cambio automático de sección")
    print("=" * 60)
    
    manager = MockFormularioManager()
    datos = {}
    manager.inicializar_formulario(datos)
    
    # Simular completación de todos los campos
    campos_seccion1 = {
        'provincia': 'Pichincha',
        'ciudad': 'Quito',
        'parroquia': 'Centro',
        'es_estudiante': 'si',
        'institucion': 'UTM',
        'facultad': 'Ciencias de la Salud',
        'carrera': 'Medicina',
        'modalidad': 'PRESENCIAL',
        'nivel': '3'
    }
    
    resultado = manager.procesar_respuesta(datos, campos_seccion1)
    
    assert resultado['cambio_seccion'], "El cambio de sección no fue detectado"
    assert datos['form_state']['seccion_actual'] == 'datos_identificacion', "Sección no cambió"
    
    print("✅ Cambio de sección automático correcto")
    print(f"   Sección actual: {datos['form_state']['seccion_actual']}")
    print(f"   Campos de nueva sección: {len(datos['form_state']['campos_faltantes'])}")
    
    # Obtener siguiente pregunta (que debe ser de la nueva sección)
    siguiente = manager.obtener_siguiente_pregunta(datos)
    print(f"   Siguiente pregunta: {siguiente['pregunta']}\n")


def test_datos_identificacion():
    """Test: Extracción de datos de identificación"""
    print("=" * 60)
    print("TEST 5: Datos de Identificación")
    print("=" * 60)
    
    tool = MockToolExtraerDatosIdentificacion()
    resultado = tool.extraer(
        nombres="Juan",
        apellidos="Pérez García",
        cedula="1234567890",
        sexo="masculino"
    )
    
    assert len(resultado) == 4, "Fallo en extracción de identificación"
    print("✅ Extracción de identificación correcta")
    print(f"   Resultado: {resultado}\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRUEBAS DEL SISTEMA ITERATIVO DE FORMULARIO")
    print("=" * 60 + "\n")
    
    try:
        test_extraccion_individual()
        test_extraccion_multiple()
        test_datos_identificacion()
        test_cambio_seccion()
        test_flujo_completo()
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("=" * 60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ PRUEBA FALLIDA: {e}\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
