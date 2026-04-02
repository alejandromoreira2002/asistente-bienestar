# Guía de Uso - Sistema Iterativo de Formulario

## Cómo Funciona en la Práctica

### Flujo Esperado en Conversación

```
USUARIO INICIAL:
"Hola, quiero llenar el formulario"

ASISTENTE - Pregunta 1:
"Excelente, vamos a llenar el formulario juntos.
Primero, ¿en qué provincia resides?"

USUARIO RESPONDE:
"Vivo en Pichincha, en Quito, en el centro"

ASISTENTE - EXTRAE Y PREGUNTA 2:
✓ Extraído: provincia=Pichincha, ciudad=Quito, parroquia=Centro
Progreso: 3/9 campos completados

"Perfecto, gracias. Ahora, ¿eres estudiante?"

USUARIO RESPONDE:
"Sí, soy estudiante de UTM"

ASISTENTE - EXTRAE Y PREGUNTA 3:
✓ Extraído: es_estudiante=si, institucion=UTM
Progreso: 5/9 campos completados

"¡Genial! ¿Cuál es tu facultad?"

USUARIO RESPONDE:
"Ciencias de la Salud"

...continúa hasta completar todos los campos...

ASISTENTE - AL COMPLETAR SECCIÓN 1:
"Excelente, hemos completado la 'Ficha de Datos Iniciales'.
Ahora continuaremos con la sección '1. Datos de Identificación del Usuario'.

¿Cuáles son tus nombres?"
```

## Ejemplos de Extracción Flexible

### Ejemplo 1: Usuario menciona Ciudad y Parroquia juntos
```
USUARIO: "Quito, centro"

EXTRACCIÓN:
{
    'ciudad': 'Quito',
    'parroquia': 'Centro'
}

PROGRESO: Actualiza 2 campos a la vez
SIGUIENTE PREGUNTA: Pregunta el próximo campo faltante
```

### Ejemplo 2: Usuario menciona datos de institución de forma conversacional
```
USUARIO: "Estudio medicina en la Facultad de Ciencias de la Salud, 
          en modalidad presencial, voy en el tercer nivel"

EXTRACCIÓN:
{
    'facultad': 'Ciencias de la Salud',
    'carrera': 'Medicina',
    'modalidad': 'PRESENCIAL',
    'nivel': '3'
}

PROGRESO: Actualiza 4 campos de una vez
SIGUIENTE PREGUNTA: Solo pregunta campos faltantes
```

### Ejemplo 3: Respuesta con información extra
```
USUARIO: "Mi cédula es 1234567890, estoy en Quito"

EXTRACCIÓN:
{
    'cedula': '1234567890',
    'ciudad': 'Quito'  (si aún no estaba completado)
}

COMPORTAMIENTO: Extrae lo que es relevante para los campos faltantes
```

## Ventajas del Sistema

### ✅ Interactividad
- Pregunta de forma clara y específica
- Espera respuesta antes de continuar
- Mantiene conversación natural

### ✅ Flexibilidad
- Extrae múltiples campos de una sola respuesta
- No requiere que el usuario responda en formato específico
- Maneja respuestas conversacionales naturales

### ✅ Eficiencia
- Completa formularios en menos pasos
- El usuario puede mencionar varios datos a la vez
- Avanza gradualmente sin perder información

### ✅ Progreso Visual
- Muestra "Completados: 3/9"
- El usuario ve cuánto falta
- Cambio automático de sección

### ✅ Continuidad
- Mantiene estado de qué campos se completaron
- No repite preguntas de campos ya completados
- Si el usuario se va, retoma desde donde paró

## Integración con Frontend (chat.html)

### Escuchar los eventos

```javascript
// En tu código de chat.html
socket.on('extraccion_incrementales', function(data) {
    console.log('Datos extraídos:', data.valor);
    console.log('Sección:', data.seccion);
    
    // Ejemplo: llenar campos provincia, ciudad, parroquia
    if (data.valor.provincia) {
        document.getElementById('provincia').value = data.valor.provincia;
    }
    if (data.valor.ciudad) {
        document.getElementById('ciudad').value = data.valor.ciudad;
    }
    if (data.valor.parroquia) {
        document.getElementById('parroquia').value = data.valor.parroquia;
    }
    
    // ... más campos ...
    
    // Mostrar sección actual
    if (data.seccion === 'datos_identificacion') {
        scrollToSection('seccion-identificacion');
    }
});
```

### Mapeo de Campos HTML

Usa los IDs exactamente como aparecen en los campos del formulario:

**Ficha de Datos Iniciales**:
- `provincia` → `<input id="provincia">`
- `ciudad` → `<input id="ciudad">`
- `parroquia` → `<input id="parroquia">`
- `es_estudiante` → `<radio name="es_estudiante" id="estudiante_si|estudiante_no">`
- `institucion` → Usar el selected en radios
- `facultad` → Campo de texto
- `carrera` → Campo de texto
- `modalidad` → `<select id="modalidad_estudio">`
- `nivel` → Campo de texto

**Datos de Identificación**:
- `nombres` → Form input
- `apellidos` → Form input
- `cedula` → Form input
- `celular` → Form input
- `correo` → Form input
- `edad` → Form input
- `fecha_nacimiento` → Form input date
- `nacionalidad` → Form input
- `sexo` → Radio buttons
- `genero` → Form input (opcional)
- `direccion` → Form input
- `lugar_residencia` → Form input
- `contacto_referencia` → Form input

## Campos por Sección

### Sección 1: Ficha de Datos Iniciales (9 campos)
1. Provincia
2. Ciudad
3. Parroquia
4. Es estudiante
5. Institución
6. Facultad
7. Carrera
8. Modalidad
9. Nivel

### Sección 2: Datos de Identificación del Usuario (13 campos)
1. Nombres
2. Apellidos
3. Cédula
4. Celular
5. Correo
6. Edad
7. Fecha de nacimiento
8. Nacionalidad
9. Sexo
10. Género (opcional)
11. Dirección
12. Lugar de residencia
13. Contacto de referencia

## Estructura del Evento Enviado

```python
{
    "nombre": "extraccion_incrementales",
    "valor": {
        # Ejemplo con múltiples campos extraídos
        "provincia": "Pichincha",
        "ciudad": "Quito",
        "parroquia": "Centro",
        "es_estudiante": "si",
        "institucion": "UTM",
        "facultad": "Ciencias de la Salud",
        "carrera": "Medicina",
        "modalidad": "PRESENCIAL",
        "nivel": "3"
    },
    "seccion": "ficha_datos_iniciales"  # o "datos_identificacion"
}
```

## Validaciones Sugeridas (Opcional)

El sistema actual extrae lo que el usuario menciona. Para mejorar, puedes agregar validaciones:

### Cédula
```python
if 'cedula' in datos:
    if len(datos['cedula']) != 10:
        # Aviso: "La cédula debe tener 10 dígitos"
        pass
```

### Correo
```python
if 'correo' in datos:
    if '@' not in datos['correo']:
        # Aviso: "Formato de correo inválido"
        pass
```

### Fecha de Nacimiento
```python
if 'fecha_nacimiento' in datos:
    try:
        datetime.strptime(datos['fecha_nacimiento'], '%Y-%m-%d')
    except:
        # Aviso: "Formato de fecha inválida"
        pass
```

## Troubleshooting

### Problema: El LLM no extrae el campo esperado
**Solución**: 
- Asegúrate que el campo esté en la lista de campos esperados
- El LLM puede interpretar sinónimos (p.e., "metro/provincia")
- Puedes mejorar el prompt del system_message en consulta_usuario

### Problema: Se salta de sección demasiado rápido
**Solución**:
- Verifica que realmente todos los campos estén en campos_faltantes
- Revisa que la extracción esté correcta en el EVENT_BUFFER

### Problema: El frontend no recibe los eventos
**Solución**:
- Verifica que el hilo (session['hilo']) sea válido
- Busca en EVENT_BUFFERS[session['hilo']] si hay eventos
- Revisa logs del server backend

## Próximas Mejoras Posibles

1. **Confirmación de datos**: 
   - Mostrar resumen al final
   - Permitir ediciones antes de guardar

2. **Validación en tiempo real**:
   - Validar formato de cédula/teléfono mientras se escribe
   - Avisos al usuario de datos incorrectos

3. **Guardado automático**:
   - Guardar en BD conforme se completan campos
   - Permitir reanudar formulario posterior

4. **Campos condicionales**:
   - Si es_estudiante=no, no preguntar institución
   - Mostrar/ocultar campos dinámicamente

5. **Sugerencias**:
   - Si menciona "medicina", sugerir carreras relacionadas
   - Auto-completar basado en histórico

## Conclusión

Este sistema proporciona una experiencia más natural y fluida al llenar formularios. El usuario puede responder de forma conversacional y el sistema inteligentemente extrae lo relevante, avanzando paso a paso sin perder información.
