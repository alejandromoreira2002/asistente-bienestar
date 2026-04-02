
# =======================
# Imports
# =======================
import os
import re
import json
import time
import uuid
import pandas as pd
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from flask import (
    Flask, Response, stream_with_context, render_template, url_for, request, session, jsonify, send_from_directory
)
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langchain.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from threading import Event
#from flask_jwt_extended import JWTManager

# Controladores y funciones propias
from controladores.asistente import AsistenteControlador
from controladores.agentes import AgentesControlador
from controladores.edificios import EdificiosControlador
from controladores.chats import ChatsControlador
from controladores.algoritmo_ml import AlgoritmoMLControlador
from controladores.formulario import FormularioControlador
from funciones.asistente import getPromptAsistentes
from funciones.funciones import determinarSemanaActual, getRandomDF

from data.globals import EVENT_BUFFERS

# =======================
# Configuración y variables globales
# =======================
load_dotenv(os.path.join(os.getcwd(), '.env'))

# nombre_paquete = 'docxtpl'
# try:
#     # sys.executable asegura que usemos el mismo Python que está corriendo el backend
#     subprocess.check_call([sys.executable, "-m", "pip", "install", nombre_paquete])
#     print(f"Paquete {nombre_paquete} instalado con éxito.")
# except Exception as e:
#     print(f"Error al instalar: {e}")
# "python3 -m pip install --no-cache-dir"

app = Flask(__name__)
app.config['SECRET_KEY'] = b'secret_key'
app.config['ASSETS_FOLDER'] = os.path.join(os.getcwd(), 'assets')

# Cancelación por stream (pestaña)
CANCEL_EVENTS = {}   # {stream_id (str): threading.Event}

# Instancia de controladores
controladorChats = ChatsControlador(app)
controladorAgente = AgentesControlador(app)
controladorAsistente = AsistenteControlador(app)
controladorEdificios = EdificiosControlador(app)
controladorFormulario = FormularioControlador(app)
controladorAlgoritmoML = AlgoritmoMLControlador()

# Inicialización del JWT
#jwt = JWTManager(app)

GRAPH = controladorAgente.construirGrafo()

# Precarga de rutas estáticas
with app.test_request_context():
    url_for('static', filename='/resources/')
    url_for('static', filename='/css/')
    url_for('static', filename='/scripts/')
    url_for('static', filename='/assets/')

"""
=======================
 Rutas de archivos estáticos y vistas principales
=======================
"""

print("aa")
# Sirve archivos de la carpeta assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(app.config['ASSETS_FOLDER'], filename)

# Sirve archivos de la carpeta static
@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

# Página principal
@app.get('/')
def index():
    session['intenciones'] = {'actual': 'ninguna', 'siguiente': 'ninguna'}
    session['historial_consumo'] = []
    return render_template('index.html')

@app.get('/getgraph')
def get_graph():
    """Devuelve el diagrama del grafo como una imagen PNG"""
    try:
        # Obtener la imagen PNG del grafo
        graph_image = controladorAgente.mostrarGrafo(GRAPH)
        
        # Devolver como PNG
        return Response(
            graph_image,
            mimetype='image/png',
            headers={'Content-Disposition': 'inline; filename=grafo.png'}
        )
    except Exception as e:
        print(f"Error al generar el grafo: {e}")
        return jsonify({"error": "No se pudo generar el grafo"}), 500

@app.get('/chat')
def chatPage():
    session['intenciones'] = {'actual': 'ninguna', 'siguiente': 'ninguna'}
    session['historial_consumo'] = []
    return render_template('chat.html')

@app.get('/avatar')
def modeloAvatar():
    return render_template('avatar.html')

# Obtener edificios
@app.get('/edificios')
def get_edificios():
    respuesta = controladorEdificios.getEdificios()
    estado = 200 if respuesta['ok'] else 500
    return jsonify(respuesta), estado

# Pruebas y utilidades
@app.get('/chats')
def prueba_chats():
    if 'hilo' not in session:
        hilo = controladorAsistente.crearHilo()
        session['hilo'] = hilo
    mensaje = controladorAsistente.getListaMensajes(session.get('hilo'))
    return jsonify(mensaje)

@app.post('/reaccionar-msg')
def reaccionar_msg():
    if 'hilo' not in session:
        hilo = controladorAsistente.crearHilo()
        session['hilo'] = hilo
    data_dict = json.loads(request.data.decode('utf-8'))
    idMensaje = data_dict['idMensaje']
    reaccion = data_dict['reaccion']
    resultado = controladorAsistente.reaccionarMensaje(session.get('hilo'), idMensaje, reaccion)
    return jsonify(resultado)


# Consumo de edificios
@app.get('/datos')
def get_consumo_edificios():

    edificio = request.args.get('idEdificacion')
    piso = request.args.get('idPiso')
    ambiente = request.args.get('idAmbiente')
    fechaInicio = request.args.get('fechaInicio')
    fechaFin = request.args.get('fechaFin')
    respuesta = controladorEdificios.getConsumoEdificios(edificio, piso, ambiente, fechaInicio, fechaFin)
    return jsonify(respuesta)


# Endpoint de cancelación segura por pestaña (puede ser llamado con sendBeacon)
@app.post("/cancelar")
def cancelar():
    # Acepta JSON con cualquier content-type (incluido sendBeacon text/plain)
    data = request.get_json(silent=True)
    if not data:
        try:
            data = json.loads(request.data.decode("utf-8"))
        except Exception:
            data = {}

    stream_id = data.get("stream_id")
    if stream_id and stream_id in CANCEL_EVENTS:
        CANCEL_EVENTS[stream_id].set()
        return {"ok": True, "cancelled": stream_id}, 200
    return {"ok": False, "msg": "stream_id no encontrado"}, 404


# Inicializa el asistente en tiempo real (streaming SSE)
@app.post('/inicializar')
def inicializar():

    if 'hilo' not in session:
        session['hilo'] = controladorAgente.crearHilo()
        
    codigo = session['hilo']

    textStt = 'El usuario se ha conectado, preséntate ante el usuario y dale una bienvenida.'
   
    
    print("Se recibio el siguiente texto: ", textStt)
    
    # El front nos manda un stream_id por cabecera; si no, lo generamos
    stream_id = request.headers.get("x-stream-id") or str(uuid.uuid4())
    
    # Evento de cancelación exclusivo de ESTA pestaña
    cancel_event = Event()
    CANCEL_EVENTS[stream_id] = cancel_event

    def event_stream_universal_agente(hilo, modo, mensaje, graph, cancel_event: Event):
        config: RunnableConfig = {"configurable": {"thread_id": hilo}}

        buffer = ''
        txt_completo = ''
        
        human_response = None
        
        print("Entrada de datos:")
        print(mensaje)

        if graph.get_state(config).interrupts:
            human_response = Command(
                resume = mensaje
            )
        else:
            historial_msgs = []
            datosEnInfo = {}
            if graph.get_state(config).values:
                datosEnInfo = graph.get_state(config).values['datos']
            else:
                historial_msgs.append(SystemMessage(content="""
                    Eres un asistente medico y te encuentras operativo en el consultorio de bienestar estudiantil. 
                    Tu objetivo es solicitar informacion personal al usuario para registrarlo en una ficha de trabajo 
                    social como un proceso previo al triaje y consulta medica del paciente. Pregunta y responde de 
                    forma profesional como un doctor lo haria.
                """))
            historial_msgs.append(HumanMessage(content=mensaje))
            human_response = {"messages": historial_msgs, "datos":datosEnInfo}
            # human_response = {"messages": [HumanMessage(content=mensaje)], "datos":{}}
        
        # print("\n=======ESTADO=========")
        for clas, chunk in graph.stream(
            human_response,
            stream_mode=["values", "messages"] ,
            config=config,
        ):
            # 2) Leer eventos de nodos (si existen)
            try:
                contenido = EVENT_BUFFERS[hilo].get_nowait()
                yield f"{json.dumps({'type':'grafico','data': json.dumps([contenido], default=str)})}\n\n"
            except Exception:
                pass  # sin eventos
            
            if cancel_event.is_set():
                break

            if clas == 'messages':
                token = ''
                
                if chunk[0].type == 'AIMessageChunk' and chunk[0].content:
                    # print(chunk[0].type)
                    # print(chunk)
                    token = chunk[0].content
                    yield f"{json.dumps({'type':'token','token':token})}\n\n"
                # token = chunk[0].content
                # yield f"{json.dumps({'type':'token','token':token})}\n\n"
                buffer += token
                txt_completo += token
                
                # Cortar por signos de puntuación
                parts = re.split(r'(?<=[.!?])\s+', buffer)
                if len(parts) > 1:
                    for sent in parts[:-1]:
                        sent = sent.strip()
                        if sent:
                            audio = controladorAsistente.text_to_speech(sent)
                            yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
                    buffer = parts[-1]
            
            if clas == 'values' and '__interrupt__' in chunk:
                #print(f"Interrupt:{chunk}")
                msg = chunk['__interrupt__'][-1].value
                print(f"[ INTERRUPT ] {msg}")
                
                break
            
        if buffer.strip():
            audio = controladorAsistente.text_to_speech(buffer.strip())
            yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
        # print("Guardar en la base de datos el mensaje completo:")
        # controladorChats.enviarMensaje(hilo, [{"role": "assistant", "content": txt_completo}])
        yield "{\"type\":\"end\"}\n\n"

    gen = event_stream_universal_agente(
        hilo=codigo,
        #stream_id=stream_id,
        modo="inicializar",
        mensaje=textStt,
        graph=GRAPH,
        cancel_event=cancel_event
    )
    
    return Response(
        stream_with_context(gen),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

    # gen = event_stream_universal(
    #     hilo=hilo,
    #     #stream_id=stream_id,
    #     modo="inicializar",
    #     mensajes=mensajes,
    #     intenciones=intenciones,
    #     contenido=None,
    #     controladorAsistente=controladorAsistente,
    #     controladorChats=controladorChats,
    #     cancel_event=cancel_event
    # )

    # return Response(
    #     stream_with_context(gen),
    #     mimetype='text/event-stream',
    #     headers={
    #         "Cache-Control": "no-cache",
    #         "X-Accel-Buffering": "no",
    #         "Connection": "keep-alive",
    #     }
    # )



# Conversación principal (voz a texto, procesamiento y streaming SSE)
@app.post('/conversarant')
def conversarAnt():
    if 'historial_consumo' not in session:
        session['historial_consumo'] = []
    if 'hilo' not in session:
        session['hilo'] = controladorAsistente.crearHilo()
    if 'prediccion' not in session:
        session['prediccion'] = {'msgs': []}
    if 'intenciones' in session:
        print("Intenciones al inicio de la consulta: ", session['intenciones'])
    if 'intenciones' in session and 'actual' in session['intenciones']:
        session['intenciones']['anterior'] = session['intenciones']['actual']
    else:
        session['intenciones'] = {'anterior': 'ninguna'}
    
    session['intenciones']['actual'] = 'ninguna'
    session['intenciones']['siguiente'] = 'ninguna'
    
    codigo = session['hilo']
    
    intencion = request.form.get('intencion')
    #print(f"Intención recibida: {intencion}")
    
    voz = request.files.get('voice')
    #print("Paso #1: Conversión de voz a texto.")
    
    tiempo_inicio = time.time()
    sttRespuesta = controladorAsistente.speech_to_text(voz, codigo)
    tiempo_fin = time.time()
    print(f"Tiempo de ejecución Conversión de voz a texto: {tiempo_fin - tiempo_inicio:.2f} segundos")
    
    textStt = sttRespuesta['datos'] if sttRespuesta['ok'] else 'No pude entender lo que dijiste, Podrías repetirlo porfavor?'
    controladorChats.enviarMensaje(codigo, [{"role": "user", "content": textStt}])
    respuesta = procesamientoConversacion(textStt, intencion)
    #print("Respuesta procesada:", respuesta)
    #print("Contenido de sesión:", session.get('contenido'))
    
    contenido = session.get('contenido', [])
    intenciones = session.get('intenciones', [])
    #print("Intenciones antes de la respuesta:", intenciones)
    
    # El front nos manda un stream_id por cabecera; si no, lo generamos
    stream_id = request.headers.get("x-stream-id") or str(uuid.uuid4())

    # Evento de cancelación exclusivo de ESTA pestaña
    cancel_event = Event()
    CANCEL_EVENTS[stream_id] = cancel_event

    gen = event_stream_universal(
        hilo=codigo,
        #stream_id=stream_id,
        modo="conversar",
        mensajes=respuesta,
        intenciones=intenciones,
        contenido=contenido,
        controladorAsistente=controladorAsistente,
        controladorChats=controladorChats,
        cancel_event=cancel_event
    )
    
    return Response(
        stream_with_context(gen),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

@app.post('/conversar')
def conversar():
    if 'hilo' not in session:
        session['hilo'] = controladorAgente.crearHilo()
        
    codigo = session['hilo']
    
    tipo = request.form.get('tipo')
    texto = None
    voz = None
    if tipo == 'voice':
        voz = request.files.get('voice')
    else:
        texto = request.form.get('text')

    textStt = ''
    if voz is not None:
        tiempo_inicio = time.time()
        sttRespuesta = controladorAsistente.speech_to_text(voz, codigo)
        tiempo_fin = time.time()
        print(f"Tiempo de ejecución Conversión de voz a texto: {tiempo_fin - tiempo_inicio:.2f} segundos")
    
        textStt = sttRespuesta['datos'] if sttRespuesta['ok'] else 'No pude entender lo que dijiste, Podrías repetirlo porfavor?'
    else:
        textStt = texto
    
    print("Se recibio el siguiente texto: ", textStt)
    
    # El front nos manda un stream_id por cabecera; si no, lo generamos
    stream_id = request.headers.get("x-stream-id") or str(uuid.uuid4())
    
    # Evento de cancelación exclusivo de ESTA pestaña
    cancel_event = Event()
    CANCEL_EVENTS[stream_id] = cancel_event
    
    def event_stream_universal_agente(hilo, modo, mensaje, graph, cancel_event: Event, tipo="voice"):
        config: RunnableConfig = {"configurable": {"thread_id": hilo}}

        buffer = ''
        txt_completo = ''
        
        human_response = None
        
        # print("Configuracion hilo:")
        # print(config)

        if graph.get_state(config).interrupts:
            human_response = Command(
                resume = mensaje
            )
        else:
            historial_msgs = []
            datosEnInfo = {}
            # print("Estado del grafo al iniciar la conversación:")
            print(graph.get_state(config).values)
            if graph.get_state(config).values:
                datosEnInfo = graph.get_state(config).values['datos']
            else:
                historial_msgs.append(SystemMessage(content="""
                    Eres un asistente medico, te llamas Luis y te encuentras operativo en el consultorio de bienestar estudiantil. 
                """))
                # historial_msgs.append(SystemMessage(content="""
                #     Eres un asistente medico, te llamas Luis y te encuentras operativo en el consultorio de bienestar estudiantil. 
                #     Tu objetivo es asistir a pacientes para el llenado de una ficha de trabajo social con datos que
                #     se te proporcionaran despues. Por el momento no preguntaras por datos personales al usuario, hasta 
                #     que se te indique que lo hagas.
                # """))
                # historial_msgs.append(SystemMessage(content="""
                #     Eres un asistente medico y te encuentras operativo en el consultorio de bienestar estudiantil. 
                #     Tu objetivo es solicitar informacion personal al usuario para registrarlo en una ficha de trabajo 
                #     social como un proceso previo al triaje y consulta medica del paciente. Pregunta y responde de 
                #     forma profesional como un doctor lo haria. 
                # """))
            historial_msgs.append(HumanMessage(content=mensaje))
            human_response = {"messages": historial_msgs, "datos":datosEnInfo}
            # print("Respuesta formateada para el grafo:")
            # print(human_response)
            # human_response = {"messages": [HumanMessage(content=mensaje)], "datos":{}}
        
        # print("\n=======ESTADO=========")
        for clas, chunk in graph.stream(
            human_response,
            stream_mode=["values", "messages"] ,
            config=config,
        ):
            # 2) Leer eventos de nodos (si existen)
            try:
                contenido = EVENT_BUFFERS[hilo].get_nowait()
                print(contenido)
                yield f"{json.dumps({'type':'grafico','data': json.dumps([contenido], default=str)})}\n\n"
            except Exception:
                pass  # sin eventos
            
            if cancel_event.is_set():
                print("Rompiendo el evento de audio")
                break

            if clas == 'messages':
                token = ''
                
                if chunk[0].type == 'AIMessageChunk' and chunk[0].content:
                    # print(chunk[0].type)
                    # print(chunk)
                    token = chunk[0].content
                    # print(token)
                    yield f"{json.dumps({'type':'token','token':token})}\n\n"
                # token = chunk[0].content
                # yield f"{json.dumps({'type':'token','token':token})}\n\n"
                buffer += token
                txt_completo += token
                
                if tipo=="voice":
                    # Cortar por signos de puntuación
                    parts = re.split(r'(?<=[.!?])\s+', buffer)
                    if len(parts) > 1:
                        for sent in parts[:-1]:
                            sent = sent.strip()
                            if sent:
                                audio = controladorAsistente.text_to_speech(sent)
                                yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
                        buffer = parts[-1]
            
            if clas == 'values' and '__interrupt__' in chunk:
                #print(f"Interrupt:{chunk}")
                msg = chunk['__interrupt__'][-1].value
                print(f"[ INTERRUPT ] {msg}")
                
                break
            
        if buffer.strip() and tipo=="voice":
            audio = controladorAsistente.text_to_speech(buffer.strip())
            yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
        # print("Guardar en la base de datos el mensaje completo:")
        # controladorChats.enviarMensaje(hilo, [{"role": "assistant", "content": txt_completo}])
        yield f"{json.dumps({'type':'texto_completo','texto':txt_completo})}\n\n"
        yield "{\"type\":\"end\"}\n\n"

    gen = event_stream_universal_agente(
        hilo=codigo,
        #stream_id=stream_id,
        modo="conversar",
        mensaje=textStt,
        graph=GRAPH,
        cancel_event=cancel_event,
        tipo=tipo
    )
    
    return Response(
        stream_with_context(gen),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# Predicción de consumo (API)
@app.get('/api/prediccion')
def get_prediccion():
    edificio = request.args.get('edificio')
    piso = request.args.get('piso')
    ambiente = request.args.get('ambiente')
    fecha = request.args.get('fecha')
    # Determinar las fechas de las semanas
    lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva = determinarSemanaActual(fecha)
    # Se consulta el consumo completo del ambiente seleccionado toda la fecha agrupada por día
    ruta_json = 'consumo_energetico_2025_08_18.json'  # Cambiar por data de base de datos
    # Se consulta la predicción de la última semana del consumo del ambiente seleccionado
    data_semana_consumo = getRandomDF(lunes_semana_actual, inicio_semana_nueva)  # Cambiar por base de datos
    # Se genera la data de variables exógenas para la predicción
    textoLLM = (
        "DÍA: Lunes | TIPO: feriado\nDÍA: Martes | TIPO: normal\nDÍA: Miércoles | TIPO: normal\n"
        "DÍA: Jueves | TIPO: especial\nDÍA: Viernes | TIPO: especial\nDÍA: Sábado | TIPO: normal\nDÍA: Domingo | TIPO: normal"
    )
    data_generada = controladorAlgoritmoML.generarDF(textoLLM, inicio_semana_nueva)
    data_nueva = pd.concat([data_semana_consumo, data_generada], axis=0)
    fechas_prediccion = (lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva)
    datos_prediccion = controladorAlgoritmoML.predecirConsumo(ruta_json, data_nueva, fechas_prediccion)
    datos_ultima_semana = datos_prediccion[-7:]
    return jsonify({'ok': True, 'observacion': None, 'datos': datos_ultima_semana})

# Guardar firma
@app.post('/guardar-firma')
def guardar_firma():
    """Endpoint para guardar la firma del formulario como PNG"""
    try:
        # Obtener archivo de firma del request
        if 'firma' not in request.files:
            return jsonify({'ok': False, 'message': 'No se proporcionó archivo de firma'}), 400
        
        firma_file = request.files['firma']
        firma_codigo = request.args.get('archivo', 'firma')
        
        if firma_file.filename == '':
            return jsonify({'ok': False, 'message': 'El archivo no tiene nombre'}), 400
        
        # Crear directorio de storage si no existe
        # Usar variable de entorno APP_BASE_DIR si está defined, sino usar el directorio de este archivo
        base_dir = os.environ.get('APP_BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
        storage_dir = os.path.join(base_dir, 'docs', 'firmas')
        os.makedirs(storage_dir, exist_ok=True)
        
        # Generar nombre de archivo único con timestamp
        # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{firma_codigo}.png'
        filepath = os.path.join(storage_dir, filename)
        # filepath = "/home/deepseek/1. Sistemas funcionales/2. Asistente Energético/Código/storage/" + filename
        print("Se guardara en la siguiente ruta: ", storage_dir)
        files = os.listdir(storage_dir)
        for file in files:
            print(file)
        
        # Guardar archivo
        firma_file.save(filepath)
        
        print(f"Firma guardada en: {filepath}")
        
        return jsonify({
            'ok': True,
            'datos': filename,
            'observacion': 'Firma guardada correctamente',
        }), 200
        
    except Exception as e:
        print(f"Error al guardar firma: {str(e)}")
        return jsonify({'ok': False, 'datos': None, 'observacion': f'Error al guardar firma: {str(e)}'}), 500


# =======================
# Función universal para streaming SSE (event_stream)
# =======================
def event_stream_universal(hilo, modo, mensajes, intenciones, contenido, controladorAsistente, controladorChats, cancel_event: Event):
    """
    Función generadora universal para streaming SSE en Flask.
    - hilo: id de hilo/conversación
    - modo: 'inicializar' o 'conversar'
    - mensajes: lista de mensajes o respuesta
    - intenciones: diccionario de intenciones
    - contenido: datos extra para gráficas (solo en conversar)
    - controladorAsistente, controladorChats: instancias de controladores
    """
    buffer = ''
    txt_completo = ''
    # Solo para modo conversar
    if contenido:
        yield f"{json.dumps({'type':'grafico','data': json.dumps(contenido, default=str)})}\n\n"
    if intenciones:
        yield f"{json.dumps({'type':'intenciones','data': json.dumps(intenciones, default=str)})}\n\n"
    # Streaming de tokens
    for token in controladorAsistente.stream_tokens(hilo, modo, mensajes, intenciones, contenido, cancel_event=cancel_event):
        
        if cancel_event.is_set():
            break
        
        yield f"{json.dumps({'type':'token','token':token})}\n\n"
        buffer += token
        txt_completo += token
        # Cortar por signos de puntuación
        parts = re.split(r'(?<=[.!?])\s+', buffer)
        if len(parts) > 1:
            for sent in parts[:-1]:
                sent = sent.strip()
                if sent:
                    audio = controladorAsistente.text_to_speech(sent)
                    yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
            buffer = parts[-1]
    if buffer.strip():
        audio = controladorAsistente.text_to_speech(buffer.strip())
        yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
    print("Guardar en la base de datos el mensaje completo:")
    controladorChats.enviarMensaje(hilo, [{"role": "assistant", "content": txt_completo}])
    yield "{\"type\":\"end\"}\n\n"
    
def event_stream_universal_agenteI(hilo, modo, mensaje, controladorAgente, cancel_event: Event):
    """
    Función generadora universal para streaming SSE en Flask.
    - hilo: id de hilo/conversación
    - modo: 'inicializar' o 'conversar'
    - mensajes: lista de mensajes o respuesta
    - intenciones: diccionario de intenciones
    - contenido: datos extra para gráficas (solo en conversar)
    - controladorAsistente, controladorChats: instancias de controladores
    """
    buffer = ''
    txt_completo = ''
    
    # Streaming de tokens
    for token in controladorAgente.stream_tokens(hilo, modo, mensajes, cancel_event=cancel_event):
        
        if cancel_event.is_set():
            break
        
        yield f"{json.dumps({'type':'token','token':token})}\n\n"
        buffer += token
        txt_completo += token
        # Cortar por signos de puntuación
        parts = re.split(r'(?<=[.!?])\s+', buffer)
        if len(parts) > 1:
            for sent in parts[:-1]:
                sent = sent.strip()
                if sent:
                    audio = controladorAsistente.text_to_speech(sent)
                    yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
            buffer = parts[-1]
    if buffer.strip():
        audio = controladorAsistente.text_to_speech(buffer.strip())
        yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
    print("Guardar en la base de datos el mensaje completo:")
    controladorChats.enviarMensaje(hilo, [{"role": "assistant", "content": txt_completo}])
    yield "{\"type\":\"end\"}\n\n"


# =======================
# Funciones auxiliares de procesamiento de conversación
# =======================
@app.post('/guardar-formulario')
def guardar_formulario():
    """Endpoint para guardar los datos del formulario completo"""
    try:
    # Obtener datos JSON del request
        datos = request.get_json()
        
        if not datos:
            return jsonify({'ok': False, datos:None, 'observacion': 'No se proporcionaron datos'}), 400
        
        print("Datos del formulario recibidos:")
        # datos = json.loads(datos, indent=2, ensure_ascii=False)
        print(datos)
        
        # Aquí puedes guardar los datos en la base de datos
        # Por ahora solo guardaremos en un archivo JSON para pruebas
        
        resultado = controladorFormulario.registrarFormulario(datos)
        
        if resultado and resultado['ok']:
            print("Resultado de registrar formulario: ", resultado)
            formulario = controladorFormulario.generarFormulario(datos['num_ficha'])
            controladorFormulario.enviarFormulario('proyectofef@utm.edu.ec', adjuntos=[formulario])
        
            return jsonify({
                'ok': True,
                'datos': formulario,
                'observacion': 'La ficha ha sido guardada correctamente.',
            }), 200
        else:
            return jsonify({
                'ok': False,
                'datos': None,
                'observacion': resultado.get('observacion', 'Error al guardar datos'),
            }), 500
    except Exception as e:
        print(f"Error al guardar formulario: {str(e)}")
        return jsonify({'ok': False, 'message': f'Error al guardar formulario: {str(e)}'}), 500

@app.get('/numero-ficha-reciente')
def numero_ficha_reciente():
    """Endpoint para obtener el número de ficha más reciente de la base de datos"""
    try:
        num_ficha = controladorFormulario.getNumFicha()
        
        return jsonify({
            'ok': True,
            'num_ficha': num_ficha,
            'message': f'Número de ficha reciente: {num_ficha}'
        }), 200
        
    except Exception as e:
        print(f"Error al obtener número de ficha: {str(e)}")
        return jsonify({'ok': False, 'message': f'Error al obtener número de ficha: {str(e)}'}), 500

@app.get('/actualizar-ficha')
def actualizar_ficha():
    global GRAPH
    """Endpoint para actualizar el número de ficha"""
    # try:
    session['hilo'] = f"user_{request.args.get('num_ficha')}"
    config = {"configurable": {"thread_id": session['hilo']}}
    if GRAPH.get_state(config).values:
        GRAPH = controladorAgente.reiniciarGrafo(session['hilo'])  # Reconstruir el grafo para limpiar estados anteriores
    # print("Estado del grafo al actualizar la ficha:")
    # print(GRAPH.get_state(config).values)
    # GRAPH.delete_state(config)
    # print(session['hilo'] + " es el nuevo hilo de conversación")
    
    return jsonify({
        'ok': True,
        'datos': session['hilo'],
        'observacion': None
    }), 200
        
    # except Exception as e:
    #     print(f"Error al obtener número de ficha: {str(e)}")
    #     return jsonify({'ok': False, 'message': f'Error al obtener número de ficha: {str(e)}'}), 500


def procesamientoConversacion(texto, intencion='ninguna'):
    if intencion == 'ninguna':
        session['contenido'] = []
    funciones = {
        'solicita_datos_consumo': controladorEdificios.consultarConsumo,
        'solicita_prediccion': controladorEdificios.getPrediccion
    }
    etiquetas = list(funciones.keys()) + ['pregunta_respuesta_general']
    if intencion == 'ninguna':
        intencion_asistente = controladorEdificios.preguntarAsistente(
            'mistral:latest', getPromptAsistentes('detectar_intencion', texto), 'generar')
        resultado = {'intencion': intencion_asistente.replace('-', '').replace('\n', '').strip().lower(), 'confidence': 1.0}
    else:
        resultado = {'intencion': intencion, 'confidence': 1.0}
    intencion = 'pregunta_respuesta_general' if resultado['intencion'] not in etiquetas else resultado['intencion']
    session['intenciones']['actual'] = str(intencion)
    mensajeAsistente = {"role": "user", "content": texto, "ok": True}
    mensajesAsis = [mensajeAsistente]
    if intencion != 'pregunta_respuesta_general':
        funcionIA = funciones[intencion]
        respuesta = funcionIA(texto)
        if respuesta['info']:
            session['contenido'].append({"nombre": intencion, "valor": respuesta['info']})
            mensajesAsis.append({"role": "user", "content": respuesta['reason'], "ok": respuesta['success']})
        else:
            mensajesAsis = [{"role": "user", "content": respuesta['reason'], "ok": respuesta['success']}]
    return mensajesAsis


if __name__ == '__main__':
    print("hh")
    app.run(port=3005, debug=True, use_reloader=False, host='0.0.0.0', ssl_context=(os.environ.get("RUTA_CERT"), os.environ.get("RUTA_CERT_KEY")))
#    app.run(port=3002, debug=True, host='0.0.0.0')
