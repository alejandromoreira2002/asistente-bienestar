# Diagrama de Flujo - Sistema Iterativo de Formulario

## Flujo Principal del Nodo `consulta_usuario`

```
┌─────────────────────────────────────────────┐
│         INICIO DEL NODO                     │
│    (Primer mensaje del usuario)             │
└────────────────┬────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ ¿Existe form_state │
        │ en datos?          │
        └────┬───────────┬───┘
             │ NO        │ SÍ
             ▼           │
      ┌──────────────┐   │
      │ INICIALIZAR  │   │
      │ form_state   │   │
      │ vacío        │   │
      └──────────────┘   │
             │           │
             └─────┬─────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ OBTENER SIGUIENTE CAMPO  │
        │ FALTANTE                 │
        └────┬─────────────────┬───┘
             │ Hay campos      │ No hay campos
             │ faltantes       │ (completado)
             ▼                 ▼
      ┌─────────────────┐  ┌──────────────┐
      │ Generar pregunta│  │ Fin del flujo│
      │ específica      │  │ Formulario   │
      └────────┬────────┘  │ completado   │
               │           └──────────────┘
               ▼
      ┌──────────────────────────┐
      │ LLAMAR LLM CON TOOL      │
      │ (extraer_datos_* )       │
      └────┬──────────────────┬──┘
           │ Tool Called      │ No Tool Called
           ▼                  ▼
      ┌─────────────────┐ ┌──────────────┐
      │ Procesar        │ │ Respuesta    │
      │ Tool Call       │ │ conversacional
      │ Arguments       │ │ (sin extracción)
      └────┬────────────┘ └──────────────┘
          │
          ▼
      ┌──────────────────────────┐
      │ ACTUALIZAR ESTADO        │
      │ - Marcar campos como     │
      │   completados            │
      │ - Eliminar de faltantes  │
      └────┬─────────────────┬───┘
           │ ¿Cambio de      │ No
           │ sección?        │
           ▼ Sí              │
      ┌──────────────────────┐ │
      │ CAMBIAR SECCIÓN      │ │
      │ ficha_datos_iniciales│ │
      │   →                  │ │
      │ datos_identificacion │ │
      │ Reiniciar campos     │ │
      └──────────────────────┘ │
           │                   │
           └───────┬───────────┘
                   │
                   ▼
      ┌──────────────────────────┐
      │ ENVIAR EVENTO AL BUFFER  │
      │ {                        │
      │   nombre: extraccion...  │
      │   valor: {...},          │
      │   seccion: ...           │
      │ }                        │
      └────────────┬─────────────┘
                   │
                   ▼
      ┌──────────────────────────┐
      │ DEVOLVER RESPUESTA       │
      │ - Messages actualizados  │
      │ - Datos actualizados     │
      └──────────────────────────┘
```

---

## Estructura de Decisiones

```
¿Estado inicial o campos vacíos?
│
├─ SÍ → Inicializar form_state con lista de campos
│
└─ NO → Usar form_state existente
       │
       ├─ Campos faltantes = []?
       │  │
       │  ├─ SÍ → Formulario completado (FIN)
       │  │
       │  └─ NO → Continuar
       │         │
       │         ├─ Obtener siguiente campo faltante
       │         ├─ Generar pregunta personalizada
       │         ├─ Llamar LLM con Tool
       │         │
       │         ├─ ¿Tool fue llamada?
       │         │  │
       │         │  ├─ SÍ → Procesar argumentos de Tool
       │         │  │      │
       │         │  │      ├─ Extraer campos mencionados
       │         │  │      ├─ Actualizar campos_completados
       │         │  │      ├─ Actualizar campos_faltantes
       │         │  │      │
       │         │  │      └─ ¿Todos campos completos en sección?
       │         │  │         │
       │         │  │         ├─ SÍ → Cambiar a siguiente sección
       │         │  │         │        └─ Reiniciar listas
       │         │  │         │
       │         │  │         └─ NO → Mantener sección actual
       │         │  │
       │         │  └─ NO → Respuesta conversacional
       │         │
       │         └─ Enviar evento al EVENT_BUFFER
```

---

## Ciclo de Vida de los Datos

```
CICLO 1: Usuario responde "Pichincha, Quito"
│
├─ Tool extrae: {'provincia': 'Pichincha', 'ciudad': 'Quito'}
│
├─ Estado actualizado:
│  ├─ campos_completados: [provincia, ciudad]
│  └─ campos_faltantes: [parroquia, es_estudiante, ...]
│
├─ Evento enviado:
│  └─ {"nombre": "extraccion_incrementales", 
│      "valor": {"provincia": "Pichincha", "ciudad": "Quito"},
│      "seccion": "ficha_datos_iniciales"}
│
└─ Frontend: Actualiza campos HTML automáticamente
   ├─ document.getElementById('provincia').value = "Pichincha"
   └─ document.getElementById('ciudad').value = "Quito"

CICLO 2: Usuario responde "Centro"
│
├─ Tool extrae: {'parroquia': 'Centro'}
│
├─ Estado actualizado:
│  ├─ campos_completados: [provincia, ciudad, parroquia]
│  └─ campos_faltantes: [es_estudiante, institucion, ...]
│
├─ Evento enviado: {"nombre": "...", "valor": {"parroquia": "Centro"}, ...}
│
└─ Frontend: Actualiza campo parroquia

... ciclos subsecuentes ...
```

---

## Cambio de Sección

```
ESTADO: Último campo de Sección 1
├─ seccion_actual: "ficha_datos_iniciales"
├─ campos_completados: [provincia, ciudad, parroquia, es_estudiante, ...]
└─ campos_faltantes: [nivel]  ← Solo falta este campo

Usuario responde: "Nivel 2"
│
├─ Tool extrae: {'nivel': '2'}
│
├─ Estado se actualiza
│  ├─ campos_completados: [..., nivel]
│  └─ campos_faltantes: []  ← ¡VACÍO!
│
├─ DETECTADO: No hay campos faltantes
│  └─ Cambiar sección automáticamente
│
├─ Nuevo estado:
│  ├─ seccion_actual: "datos_identificacion"  ← CAMBIÓ
│  ├─ campos_completados: []  ← REINICIADO
│  └─ campos_faltantes: [nombres, apellidos, cedula, ...]  ← Nueva lista
│
└─ Asistente anuncia: "¡Completamos Ficha, ahora Datos de Identificación!"
```

---

## Extracción de Múltiples Campos

```
Usuario responde:
"Estudio medicina en CTM, presencial, tercer año"

LLM analiza con Tool binding:
│
├─ Parámetro: carrera = "medicina"  ✓
├─ Parámetro: institucion = "UTM" (corrige "CTM") ✓
├─ Parámetro: modalidad = "PRESENCIAL" ✓
├─ Parámetro: nivel = "3" (interpreta "tercer año") ✓
│
└─ No detecta: facultad (no mencionado)

Tool retorna:
{
    'carrera': 'Medicina',
    'institucion': 'UTM',
    'modalidad': 'PRESENCIAL',
    'nivel': '3'
}

Estado actualizado:
├─ Antes: campos_completados = [provincia, ciudad, parroquia, es_estudiante]
└─ Después: campos_completados = [..., carrera, institucion, modalidad, nivel]
           campos_faltantes se reduce en 4 campos
```

---

## Máquina de Estados (Estado del Formulario)

```
┌──────────────────────────────────────┐
│   SECCIÓN 1: FICHA DE DATOS INICIALES│
│   (9 campos)                         │
└────────────────┬─────────────────────┘
                 │
        Campos: [provincia, ciudad, parroquia,
                 es_estudiante, institucion,
                 facultad, carrera, modalidad, nivel]
                 │
        Progreso: 0/9 → 1/9 → 2/9 → ... → 9/9
                 │
                 ├─ 0 completados: Pregunta primera
                 │
                 ├─ 1-8 completados: Continúa ciclo
                 │  ├─ Pregunta siguiente faltante
                 │  ├─ Extrae respuesta
                 │  └─ Actualiza estado
                 │
                 └─ 9 completados: TRANSICIÓN
                                    │
        ┌─────────────────────────────┘
        │
        ▼
┌──────────────────────────────────┐
│ SECCIÓN 2: DATOS DE IDENTIFICACIÓN│
│ (13 campos)                       │
└────────────────┬─────────────────┘
                 │
        Campos: [nombres, apellidos, cedula,
                 celular, correo, edad,
                 fecha_nacimiento, nacionalidad,
                 sexo, genero, direccion,
                 lugar_residencia, contacto_referencia]
                 │
        Progreso: 0/13 → 1/13 → ... → 13/13
                 │
                 └─ Mismo flujo que Sección 1
                    │
                    └─ Al completar: FORMULARIO COMPLETADO ✓
```

---

## Gestión de Datos en STATE

```
State {
    messages: [
        SystemMessage(content: "..."),
        HumanMessage(content: "Vivo en Pichincha"),
        AIMessage(content: "¿Provincia?"),
        ToolMessage(name: "extraer_datos_iniciales", ...),
        ...
    ],
    
    datos: {
        form_state: {
            seccion_actual: "ficha_datos_iniciales",
            campos_completados: ["provincia", "ciudad"],
            campos_faltantes: ["parroquia", "es_estudiante", ...]
        },
        
        // Datos extraídos
        provincia: "Pichincha",
        ciudad: "Quito",
        ...
    }
}
```

---

## Flujo de Eventos (Backend → Frontend)

```
BACKEND (Python)
│
├─ Nodo consulta_usuario se ejecuta
│  │
│  ├─ Extrae datos con Tool
│  │
│  └─ Prepara evento
│     │
│     ├─ nombre: "extraccion_incrementales"
│     ├─ valor: {...datos_extraídos...}
│     └─ seccion: "ficha_datos_iniciales"
│
├─ Envía a EVENT_BUFFER[session['hilo']]
│
└─ EVENT_BUFFERS es un diccionario global
   │
   ├─ Clave: session['hilo'] (ID único del usuario)
   └─ Valor: Cola de eventos

FRONTEND (JavaScript)
│
├─ Escucha evento 'extraccion_incrementales'
│
├─ Recibe: {"valor": {...}, "seccion": "..."}
│
├─ Procesa datos:
│  │
│  ├─ Para cada campo en valor:
│  │  ├─ Obtener elemento HTML por ID
│  │  └─ Actualizar .value
│  │
│  └─ Mostrar sección actual
│
└─ Usuario ve campos rellenarse en tiempo real ✓
```

---

## Ejemplo: Paso a Paso Completo

```
PASO 1: Sistema inicia
─ form_state = None
─ Inicia nodo

PASO 2: Inicialización
─ Crea form_state
─ seccion_actual = "ficha_datos_iniciales"
─ campos_faltantes = [provincia, ciudad, ...]

PASO 3: Primera pregunta
─ Siguiente campo: "provincia"
─ Pregunta: "¿En qué provincia resides?"

PASO 4: Usuario responde
─ Usuario: "Vivo en Pichincha"

PASO 5: Extracción
─ LLM + Tool
─ Tool args: {provincia: "Pichincha"}

PASO 6: Procesa Tool Call
─ Crea ToolMessage
─ provincia en campos_faltantes? SÍ
─ Remove provincia from faltantes
─ Add provincia to completados

PASO 7: Actualiza Estado
─ campos_completados = [provincia]
─ campos_faltantes = [ciudad, parroquia, ...]

PASO 8: Envía Evento
─ EVENT_BUFFERS[id_usuario].put({
    "nombre": "extraccion_incrementales",
    "valor": {"provincia": "Pichincha"},
    "seccion": "ficha_datos_iniciales"
  })

PASO 9: Frontend procesa
─ Recibe evento
─ Actualiza input#provincia
─ Muestra progreso: "1/9"

PASO 10: Siguiente instrucción
─ Siguiente campo: "ciudad"
─ Pregunta: "¿En qué ciudad resides?"

... loop continúa ...
```

