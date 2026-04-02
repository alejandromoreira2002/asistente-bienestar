# Ejemplos de Conversaciones - Sistema Iterativo de Formulario

## Ejemplo Completo: Usuario Proporciona Múltiples Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CONVERSACIÓN CHAT                          │
└─────────────────────────────────────────────────────────────────────┘

[ASISTENTE - Mensaje Inicial]
"Hola, voy a ayudarte a llenar el formulario. Comenzaremos con la 
 'Ficha de Datos Iniciales'. 
 
 ¿En qué provincia resides?"

[USUARIO - Respuesta 1]
"En Pichincha, específicamente en Quito"

[ASISTENTE - Extrae y continúa]
"✓ Registrado: Provincia=Pichincha, Ciudad=Quito
 Completados: 2/9 campos
 
 ¿En qué parroquia resides?"

[USUARIO - Respuesta 2]
"Centro, en la parroquia Centro"

[ASISTENTE - Extrae y continúa]
"✓ Registrado: Parroquia=Centro
 Completados: 3/9 campos
 
 ¿Eres estudiante?"

[USUARIO - Respuesta 3]
"Sí, soy estudiante de la UTM, en la Facultad de Ciencias de la Salud, 
 estudiando Medicina, en modalidad presencial, voy en nivel 3"

[ASISTENTE - Extrae múltiples campos]
"✓ Registrado: Es estudiante=SÍ, Institución=UTM, 
              Facultad=Ciencias de la Salud, Carrera=Medicina, 
              Modalidad=PRESENCIAL, Nivel=3
 Completados: 9/9 campos
 
 ¡Excelente! Hemos completado la 'Ficha de Datos Iniciales'. 
 Ahora continuaremos con '1. Datos de Identificación del Usuario'.
 
 ¿Cuáles son tus nombres?"

[USUARIO - Respuesta 4]
"Juan Carlos"

[ASISTENTE - Continúa]
"✓ Registrado: Nombres=Juan Carlos
 Completados: 1/13 campos
 
 ¿Cuáles son tus apellidos?"

[USUARIO - Respuesta 5]
"García Morales"

[ASISTENTE - Continúa]
"✓ Registrado: Apellidos=García Morales
 Completados: 2/13 campos
 
 ¿Cuál es tu cédula?"

... y así continúa hasta completar el formulario ...
```

### Estado del Formulario en Este Ejemplo

**Después de Respuesta 3:**

```
FICHA DE DATOS INICIALES
✓ provincia: Pichincha
✓ ciudad: Quito
✓ parroquia: Centro
✓ es_estudiante: si
✓ institucion: UTM
✓ facultad: Ciencias de la Salud
✓ carrera: Medicina
✓ modalidad: PRESENCIAL
✓ nivel: 3

DATOS DE IDENTIFICACIÓN (Cambio de Sección)
  nombres: [necesita respuesta]
  apellidos: [necesita respuesta]
  cedula: [necesita respuesta]
  ... más campos ...
```

---

## Ejemplo 2: Usuario Responde de Forma Incompleta

```
[ASISTENTE]
"¿En qué provincia resides?"

[USUARIO]
"Quito"

[ASISTENTE - ¿Qué extrae?]
El usuario menciona "Quito" que es una cuidad, no provincia.
El asistente lo interpreta como "ciudad" si está en campos faltantes.
Campos faltantes: [provincia, ciudad, parroquia, ...]

EXTRACCIÓN: {'ciudad': 'Quito'}

[ASISTENTE continúa]
"¿Provincia? La ciudad es Quito, que está en la provincia de Pichincha, ¿cierto?"

[USUARIO]
"Exacto, Pichincha"

[ASISTENTE]
"✓ Registrado: Ciudad=Quito, Provincia=Pichincha"
```

---

## Ejemplo 3: Usuario "se Salta" en sus Respuestas

```
[ASISTENTE]
"¿En qué provincia resides?"

[USUARIO]
"Soy estudiante del nivel 3"

[ASISTENTE - ¿Qué extrae?]
Usuario menciona "nivel 3" que es un campo de Ficha de Datos Iniciales.

EXTRACCIÓN: {'nivel': '3'}

[ASISTENTE - Actualiza estado]
Campos faltantes: [provincia, ciudad, parroquia, es_estudiante, 
                    institucion, facultad, carrera, modalidad]

[ASISTENTE responde]
"✓ Registrado: Nivel=3
 
 Veo que eres estudiante. ¿En qué provincia resides?"
```

---

## Ejemplo 4: Usuario con Respuesta Negativa

```
[ASISTENTE]
"¿Eres estudiante?"

[USUARIO]
"No, no soy estudiante, soy empleado"

[ASISTENTE - Extrae]
EXTRACCIÓN: {'es_estudiante': 'no'}

Campos faltantes ahora: [institucion, facultad, carrera, modalidad, nivel]
                         (¿debería preguntarlos si respondió que NO es estudiante?)

COMPORTAMIENTO ACTUAL: Sigue preguntando todos los campos
COMPORTAMIENTO MEJORADO: Podría saltarse estos campos si no aplican
```

---

## Ejemplo 5: Cambio de Sección en Acción

```
[Estado: Último campo de Sección 1]
Campos completados: [provincia, ciudad, parroquia, es_estudiante, 
                      institucion, facultad, carrera, modalidad]
Campos faltantes: [nivel]

[ASISTENTE]
"¿Cuál es tu nivel de estudios?"

[USUARIO]
"Estoy en segundo año"

[ASISTENTE - Detecta fin de sección]
✓ Registrado: Nivel=2do año
Completados: 9/9 campos

>>> CAMBIO DE SECCIÓN <<<

"¡Excelente! Hemos completado la 'Ficha de Datos Iniciales'.
 Ahora pasamos a '1. Datos de Identificación del Usuario'.
 
 ¿Cuáles son tus nombres?"

[Estado: Sección 2 iniciada]
Campos completados: []
Campos faltantes: [nombres, apellidos, cedula, celular, correo, 
                     edad, fecha_nacimiento, nacionalidad, sexo,
                     genero, direccion, lugar_residencia, contacto_referencia]
```

---

## Ejemplo 6: Datos de Contacto Complejos

```
[ASISTENTE]
"¿Cuál es tu correo electrónico?"

[USUARIO]
"Mi correo es juan.garcia@utm.edu.ec y mi celular es 0987654321"

[ASISTENTE - Extrae múltiples campos]
✓ Registrado: Correo=juan.garcia@utm.edu.ec, Celular=0987654321
Completados: X/13 campos

[Nota: El usuario proporcionó 2 datos en una respuesta,
        el sistema los extractó e interpretó correctamente]
```

---

## Mapeo Visual: Respuesta → Campos Extraídos

```
┌────────────────────────────────────────────────────────────────┐
│               RESPUESTA DEL USUARIO                            │
└────────────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────────────┐
│  LLM con Tool: extraer_datos_iniciales o                        │
│                                                                 │
│  extraer_datos_identificacion                                   │
│                                                                 │
│  Extrae parámetros relevantes de la respuesta                  │
└────────────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────────────┐
│  Resultado JSON                                                 │
│  {                                                              │
│    "provincia": "Pichincha",                                    │
│    "ciudad": "Quito"                                            │
│  }                                                              │
└────────────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────────────┐
│  Actualización de Estado                                        │
│  - Actualizar campos_completados                                │
│  - Actualizar campos_faltantes                                  │
│  - Verificar si cambio de sección                               │
└────────────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────────────┐
│  Envío a Frontend (EVENT_BUFFER)                                │
│  {                                                              │
│    "nombre": "extraccion_incrementales",                        │
│    "valor": {"provincia": "...", "ciudad": "..."},              │
│    "seccion": "ficha_datos_iniciales"                           │
│  }                                                              │
└────────────────────────────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────────────────────────────┐
│  Frontend JavaScript                                            │
│  - Rellenar campos HTML automáticamente                         │
│  - Mostrar progreso visual                                      │
│  - Desplazar a sección actual                                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Flujo Completo de Estado

```
ESTADO INICIAL
├── seccion_actual: "ficha_datos_iniciales"
├── campos_completados: []
└── campos_faltantes: [provincia, ciudad, parroquia, es_estudiante, ...]

DESPUÉS RESPUESTA 1 (Usuario: "Pichincha, Quito")
├── seccion_actual: "ficha_datos_iniciales"
├── campos_completados: [provincia, ciudad]
└── campos_faltantes: [parroquia, es_estudiante, ...]

DESPUÉS RESPUESTA 2-6 (Usuario completa todos los campos)
├── seccion_actual: "datos_identificacion"  [CAMBIO AUTOMÁTICO]
├── campos_completados: []
└── campos_faltantes: [nombres, apellidos, cedula, ...]

DESPUÉS RESPUESTA 7-12 (Usuario completa toda la sección 2)
├── seccion_actual: "datos_identificacion"
├── campos_completados: [... todos los campos ...]
└── campos_faltantes: []

FORMULARIO COMPLETADO ✓
```

---

## Tabla Comparativa: Antes vs Después

| Aspecto | Antes ❌ | Después ✅ |
|---------|:--------:|:---------:|
| **Preguntas** | 1 sola (mega-pregunta) | 1 por campo (específica) |
| **Flexibilidad** | Rígida (espera todo de una vez) | Flexible (múltiples campos por respuesta) |
| **Conversación** | Artificial | Natural |
| **Completación** | Fallaba si faltaba algo | Gradual y segura |
| **User Experience** | Abrumador | Guiado y claro |
| **Progreso Visual** | No hay | "3/9 completados" |
| **Cambio de sección** | Manual | Automático |
| **Manejo de respuestas incompletas** | Fallaba | Se adapta |

---

## Notas Importantes

- El sistema es **tolerante a variaciones** en las respuestas del usuario
- Pregunta en **orden específico** pero acepta respuestas en cualquier orden
- **Extrae inteligentemente** lo que es relevante
- **Cambia automáticamente** cuando completa una sección
- **Envía datos en tiempo real** al frontend
- **Mantiene estado** entre interacciones

