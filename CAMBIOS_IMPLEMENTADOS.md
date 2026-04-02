# Cambios Implementados - Sistema de Extracción Iterativa de Formulario

## Resumen
Se ha mejorado significativamente el sistema para que el asistente pueda preguntar por cada campo del formulario de forma interactiva y extraer los datos de forma incremental mientras el usuario responde.

## Cambios Principales

### 1. 🔧 Tool: `extraer_datos_iniciales` (Mejorada)
**Ubicación**: `modelos/agentes.py` - línea ~143

**Cambios**:
- ✅ Todos los parámetros ahora son **opcionales** (`Optional`)
- ✅ Permite extracción **incremental** de campos individuales
- ✅ Los campos extraídos se devuelven solo si fueron proporcionados
- ✅ Más flexible para respuestas conversacionales del usuario

**Campos que extrae**:
- `provincia`, `ciudad`, `parroquia`
- `es_estudiante` (si/no)
- `institucion`
- `facultad`, `carrera`, `modalidad`, `nivel`

**Ejemplo de uso**:
```python
# El usuario responde: "Vivo en Pichincha"
# Resultado: {'provincia': 'Pichincha'}

# El usuario responde: "Soy estudiante de medicina en UTM, presencial, nivel 3"
# Resultado: {
#     'es_estudiante': 'si',
#     'institucion': 'UTM',
#     'carrera': 'Medicina',
#     'modalidad': 'PRESENCIAL',
#     'nivel': '3'
# }
```

### 2. 🔧 Tool: `extraer_datos_identificacion` (Nueva)
**Ubicación**: `modelos/agentes.py` - línea ~197

**Descripción**: Nueva herramienta para extraer datos de identificación personal

**Campos que extrae**:
- `nombres`, `apellidos`
- `cedula`, `celular`, `correo`
- `edad`, `fecha_nacimiento`, `nacionalidad`
- `sexo` (femenino/masculino/otro), `genero`
- `direccion`, `lugar_residencia`, `contacto_referencia`

### 3. 🎯 Nodo: `consulta_usuario` (Completamente Rediseñado)
**Ubicación**: `modelos/agentes.py` - línea ~278

**Nueva Lógica (Iterativa)**:

#### Estado del Formulario
Mantiene un estado interno con:
```python
{
    'seccion_actual': 'ficha_datos_iniciales' | 'datos_identificacion',
    'campos_completados': [...],  # Campos que ya se completaron
    'campos_faltantes': [...]     # Campos que aún faltan
}
```

#### Flujo de Trabajo:
1. **Inicialización**: En la primera ejecución, crea el estado del formulario
2. **Pregunta Personalizada**: Pregunta por el siguiente campo faltante
3. **Extracción Flexible**: Usa la tool correspondiente para extraer lo que el usuario menciona
4. **Actualización de Estado**: Actualiza qué campos se completaron
5. **Cambio de Sección**: Cuando completa "Ficha de Datos Iniciales", cambia a "Datos de Identificación"
6. **Terminación**: Cuando todos los campos están completos

#### Características:
- ✅ Preguntas específicas y personalizadas por campo
- ✅ Muestra progreso: "Completados: 3/9"
- ✅ Extrae múltiples campos si el usuario menciona varios
- ✅ Maneja respuestas conversacionales naturales
- ✅ Cambio automático de sección cuando una se completa
- ✅ Envía datos al EVENT_BUFFER inmediatamente

#### Preguntas Generadas Automáticamente:
```
Provincia: "¿En qué provincia resides?"
Ciudad: "¿En qué ciudad resides?"
Parroquia: "¿En qué parroquia resides?"
Es estudiante: "¿Eres estudiante? (responde sí o no)"
Institución: "¿En qué institución estudias? (UTM u otra)"
Facultad: "¿Cuál es tu facultad?"
...y muchas más
```

## Beneficios de la Solución

### Antes ❌
- Solo hacía UNA pregunta (de todo a la vez)
- Esperaba que el usuario mencionara TODO al mismo tiempo
- No era interactivo
- La extracción fallaba si no había TODOS los datos

### Después ✅
- Pregunta **campo por campo** de forma iterativa
- Extrae datos mientras el usuario va respondiendo
- **Conversación natural** y guiada
- Completa formularios de forma **gradual**
- **Progreso visual** para el usuario
- Maneja **múltiples campos** por respuesta
- Cambio automático de sección
- Mejor experiencia de usuario

## Pruebas Sugeridas

### Test 1: Datos en múltiples líneas
```
Usuario: "Vivo en Pichincha, en Quito"
→ Extrae: provincia='Pichincha', ciudad='Quito'
```

### Test 2: Sí, cambio de sección automático
Después de completar todos los campos de "Ficha de Datos Iniciales":
```
→ Cambia automáticamente a "1. Datos de Identificación del Usuario"
→ Pregunta primer campo: "¿Cuáles son tus nombres?"
```

### Test 3: Respuestas parciales
```
Usuario: "Mi carrera es Ingeniería en Sistemas"
→ Extrae: carrera='Ingeniería en Sistemas'
→ Continúa con siguiente campo faltante
```

## Integraciones con Frontend

El HTML en `templates/chat.html` debe:
1. **Escuchar al EVENT_BUFFER** para eventos `extraccion_incrementales`
2. **Actualizar campos en tiempo real** conforme llegan los datos
3. **Mostrar la sección actual** (usar `seccion` del evento)
4. **Mostrar progreso visual**

### Estructura del evento enviado:
```python
{
    "nombre": "extraccion_incrementales",
    "valor": {
        "provincia": "Pichincha",
        "ciudad": "Quito"
        # ... otros campos extraídos
    },
    "seccion": "ficha_datos_iniciales"  # o "datos_identificacion"
}
```

## Próximos Pasos (Opcionales)

1. **Frontend**: Actualizar `chat.html` para procesar eventos `extraccion_incrementales`
   - Rellenar campos HTML conforme llegan los datos
   - Mostrar sección actual
   - Mostrar indicador de progreso

2. **Validación**: Agregar validación de datos
   - Formato de cédula ecuatoriana
   - Formato de correo válido
   - Fecha de nacimiento válida
   - etc.

3. **Confirmación**: Agregar paso de revisión y confirmación
   - Mostrar todos los datos recopilados
   - Permitir ediciones
   - Confirmación final

4. **Base de Datos**: Guardar datos recopilados
   - Crear endpoint para guardar formulario
   - Validar datos en backend
   - Guardartansacciones o en tabla pacientes

## Archivos Modificados
- ✅ `modelos/agentes.py`: Tools y nodo mejorados
- 📝 No se modificó `templates/chat.html` (puede necesitar actualización frontend)
- 📝 No se modificó `App.py` (grafo existente funciona igual)
