import AudioMotionAnalyzer from 'https://cdn.skypack.dev/audiomotion-analyzer?min';

const Index = (function () {
  
  let dataEdificios = [];
  let fechaInicio, fechaFin;
  let chart1 = null, chart2 = null;
  let intencionConversar = 'ninguna';
  let nombreArchivoFirma = '';

  let microphoneAviable = true;
  let microphoneOpen = false;
  let isMuted = false;  // Estado de mute/unmute del detector
  const openedMicroIcon = document.getElementById('btnMicUp'),
        closedMicroIcon = document.getElementById('btnMicStop');
  let mediaRecorder;
  let audioChunks = [];
  const assistantAudioPlayer = document.getElementById('assistantAudioPlayer');
  // Declaramos el controlador a nivel de módulo para poder abortar peticiones anteriores
  let currentAbortController = null;

  const iframe = document.querySelector("iframe");

  // Función para mandar datos al iframe
  function sendTalking(audioBase64, talking = 'false') {
    iframe.contentWindow.postMessage(
      { action: "base64", data: audioBase64, talking }, 
      "*"
    );
  }

  const audioMotion = new AudioMotionAnalyzer(document.getElementById('audioMotion'), {
    height: 70,
    ansiBands: false,
    showScaleX: false,
    bgAlpha: 0,
    overlay: true,
    mode: 2,
    frequencyScale: "log",
    showPeaks: false,
    reflexRatio: 0.5,
    reflexAlpha: 1,
    reflexBright: 1,
    smoothing: 0.7
  });
  let audioMotionStream;
  let voiceDetectorStream = null;
  let voiceDetectorActive = false;

  // Parámetros de detección de silencio
  const silenceThreshold = 0.02;      // RMS mínimo para considerar "habla"
  const silenceDelay = 1000;          // ms que debe durar el silencio
  let silenceStart = null;
  let silenceInterval;
  
  // Parámetros de detección automática de voz
  const voiceDetectionThreshold = 0.03;  // RMS para detectar voz
  const voiceDetectionDelay = 0;       // ms antes de iniciar grabación 200s
  let voiceDetectionStart = null;
  let voiceDetectionInterval = null;

  // ============================== Inicialización General ==============================
  $(document).ready(async function() {
    initFormMedico();
    initMicrofono();
    initConsentimiento();
    initFechas();
    initGraficos();
    initFirmaModal();
    // Estado inicial: micrófono silenciado
    isMuted = true;
    openedMicroIcon.hidden = true;
    closedMicroIcon.hidden = false;
    await bindUIEvents();
    // await getEdificios();
  });

  let iniciarController = null;
  let currentStreamId = null;

  function initFormMedico(){
    // Obtener número de ficha reciente
    fetch('/numero-ficha-reciente')
    .then(response => response.json())
    .then(result => {
      if (result.ok) {
        document.getElementById('n_ficha').innerText = result.num_ficha;
        document.getElementById('text_nficha').value = result.num_ficha;
        actualizarFicha(result.num_ficha);
      } else {
        console.error('Error al obtener número de ficha:', result.message);
      }
    })
    .catch(error => {
      console.error('Error en la llamada al endpoint:', error);
    });

    $('input[type=radio][name=institucion]').change(function() {
        mostrarElemento(this, 'institucion');
    });
    $('input[type=radio][name=sexo]').change(function() {
        mostrarElemento(this, 'sexo');
    });
    $('input[type=radio][name=area_consulta]').change(function() {
        mostrarElemento(this, 'area_consulta');
    });
    $('input[type=radio][name=embarazada]').change(function() {
        mostrarElemento(this, 'embarazada');
    });
    $('input[type=radio][name=discapacidad]').change(function() {
        mostrarElemento(this, 'discapacidad');
    });
    $('input[type=radio][name=estado_civil]').change(function() {
        mostrarElemento(this, 'estado_civil');
    });
    $('input[type=radio][name=etnia]').change(function() {
        mostrarElemento(this, 'etnia');
    });

    // const canvas = document.getElementById('pizarra');
    // const ctx = canvas.getContext('2d');
    // let dibujando = false;

    // // Configuración de la línea
    // ctx.lineWidth = 3;
    // ctx.lineCap = 'round';
    // ctx.strokeStyle = '#000';

    // // Iniciar dibujo
    // canvas.addEventListener('pointerdown', (e) => {
    //     dibujando = true;
    //     ctx.beginPath();
    //     ctx.moveTo(e.offsetX, e.offsetY);
    // });

    // // Dibujar mientras se mueve
    // canvas.addEventListener('pointermove', (e) => {
    //     if (dibujando) {
    //         ctx.lineTo(e.offsetX, e.offsetY);
    //         ctx.stroke();
    //     }
    // });

    // // Detener dibujo
    // window.addEventListener('pointerup', () => {
    //     dibujando = false;
    // });
  }

  function actualizarFicha(numFicha){
    fetch('/actualizar-ficha?num_ficha=' + numFicha)
    .then(response => response.json())
    .then(result => {
      console.log(result)
    })
    .catch(error => {
      console.error('Error en la llamada al endpoint:', error);
    });
  }

  function mostrarElemento(elemento, nombre){
        if(nombre === 'institucion') {
            if(elemento.id === 'institucion_otro' && elemento.checked){
                document.getElementById('institucion_div').style.display = 'block';

                // document.getElementById('datos_institucion_select').style.display = 'none';
                // document.getElementById('datos_institucion_text').style.display = 'block';
                
                // document.getElementById('dominio_utm').style.display = 'none';
                // document.getElementById('dominio_otro').style.display = 'block';
                // document.getElementById('correos_dominios').style.display = 'block';
                
            } else {
                document.getElementById('institucion_div').style.display = 'none';

                // document.getElementById('datos_institucion_select').style.display = 'block';
                // document.getElementById('datos_institucion_text').style.display = 'none';

                // document.getElementById('dominio_utm').style.display = 'block';
                // document.getElementById('dominio_otro').style.display = 'none';
                // document.getElementById('correos_dominios').style.display = 'none';
            }
        }

        if(nombre === 'sexo') {
            if(elemento.id === 'sexo_otro' && elemento.checked){
                document.getElementById('sexo_div').style.display = 'block';
            } else {
                document.getElementById('sexo_div').style.display = 'none';
            }
        }

        if(nombre === 'area_consulta') {
            if(elemento.id === 'laboratorio_clinico' && elemento.checked){
                document.getElementById('area_consulta_div').style.display = 'block';
            } else {
                document.getElementById('area_consulta_div').style.display = 'none';
            }
        }
        
        if(nombre === 'embarazada') {
            if(elemento.id === 'embarazada_si' && elemento.checked){
                document.getElementById('embarazada_div').style.display = 'block';
            } else {
                document.getElementById('embarazada_div').style.display = 'none';
            }
        }
        
        if(nombre === 'discapacidad') {
            if(elemento.id === 'discapacidad_si' && elemento.checked){
                document.getElementById('discapacidad_div').style.display = 'block';
            } else {
                document.getElementById('discapacidad_div').style.display = 'none';
            }
        }

        if(nombre === 'estado_civil') {
            if(elemento.id === 'otro_estado_civil' && elemento.checked){
                document.getElementById('estado_civil_div').style.display = 'block';
            } else {
                document.getElementById('estado_civil_div').style.display = 'none';
            }
        }

        if(nombre === 'etnia') {
            if(elemento.id === 'otra_etnia' && elemento.checked){
                document.getElementById('etnia_div').style.display = 'block';
            } else {
                document.getElementById('etnia_div').style.display = 'none';
            }
        }
    }

  function genStreamId() {
    if (window.crypto?.randomUUID) return crypto.randomUUID();
    // Fallback
    return 'stream_' + Date.now() + '_' + Math.random().toString(16).slice(2);
  }

  const openMicrophone = async () => {
    
    // if (!microphoneAviable) return;
    
    if (!assistantAudioPlayer.paused) {
      assistantAudioPlayer.pause();
      assistantAudioPlayer.currentTime = 0;
    }
    console.log("INTENTO ABRIR MICROFONO")

    // Si ya hay una petición en curso, la abortamos antes de lanzar la nueva
    if (currentAbortController) {
      console.log("PETICION ABORTADA")
      currentAbortController.abort();
      sendTalking('base65off', 'false');
    }
    
    // Mostrar icono de grabando
    openedMicroIcon.hidden = false;
    closedMicroIcon.hidden = true;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    // Conectar al visualizador
    audioMotionStream = audioMotion.audioCtx.createMediaStreamSource(stream);
    audioMotion.connectInput(audioMotionStream);
    audioMotion.volume = 0;

    // Crear analysers para detectar silencio
    const analyser = audioMotion.audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    audioMotionStream.connect(analyser);
    const dataArray = new Uint8Array(analyser.fftSize);
    silenceStart = null;

    // Cada 200 ms comprobamos el nivel de RMS
    silenceInterval = setInterval(() => {
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const norm = (dataArray[i] - 128) / 128;
        sum += norm * norm;
      }
      const rms = Math.sqrt(sum / dataArray.length);

      if (rms > silenceThreshold) {
        // Volumen detectado: resetamos el contador de silencio
        silenceStart = null;
      } else {
        // No hay volumen: empezamos o comprobamos el tiempo de silencio
        if (!silenceStart) {
          silenceStart = Date.now();
        } else if (Date.now() - silenceStart > silenceDelay) {
          // Silencio prolongado: detenemos la grabación
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
          clearInterval(silenceInterval);
        }
      }
    }, 200);

    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
      clearInterval(silenceInterval);
      closeMicrophone();
    };

    mediaRecorder.start();
    // microphoneOpen = true;
  };

  const closeMicrophone = async () => {
    // microphoneAviable = false;

    openedMicroIcon.hidden = true;
    closedMicroIcon.hidden = false;

    // Desconectar visualizador
    audioMotion.disconnectInput(audioMotionStream);
    audioMotionStream = null;
    
    // Preparar el blob y enviarlo
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    audioChunks = [];

    // --- VALIDACIÓN: si el blob es muy pequeño, asumimos que no hay voz ---
    const MIN_AUDIO_SIZE = 25000; // bytes (ajusta según pruebas)
    
    if (audioBlob.size < MIN_AUDIO_SIZE) {
      console.log('No se detectó voz (blob demasiado pequeño), no se envía petición.');
      microphoneOpen = false;
      microphoneAviable = true;  // reactivar el micrófono para la siguiente vez
      // Reiniciar detector automático solo si no está muteado
      if (!isMuted) {
        setTimeout(() => iniciarDetectorVozAutomatico(), 500);
        openedMicroIcon.hidden = false;
        closedMicroIcon.hidden = true;
      }
      return;
    }
    
    await Conversar(audioBlob);

    microphoneOpen = false;
    // Reiniciar detector automático después de procesar, solo si no está muteado
    if (!isMuted) {
      setTimeout(() => iniciarDetectorVozAutomatico(), 500);
      openedMicroIcon.hidden = false;
      closedMicroIcon.hidden = true;
    }
  };

  document.getElementById('btnMicrofono').addEventListener('click', () => {
    // Toggle mute/unmute del detector de voz
    if (isMuted) {
      // Reanudar escucha
      isMuted = false;
      iniciarDetectorVozAutomatico();
      console.log('🎤 Micrófono ACTIVO - Escuchando');
      openedMicroIcon.hidden = false;
      closedMicroIcon.hidden = true;
    } else {
      // Pausar escucha
      isMuted = true;
      detenerDetectorVozAutomatico();
      console.log('🔇 Micrófono MUTED - No está escuchando');
      openedMicroIcon.hidden = true;
      closedMicroIcon.hidden = false;
      
      // Detener grabación si está en curso
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
      
      // Detener sonido si está reproduciéndose
      sendTalking('base65off', 'false');
      if (!assistantAudioPlayer.paused) {
        assistantAudioPlayer.pause();
        assistantAudioPlayer.currentTime = 0;
      }
    }
  });

  // Función para iniciar el detector automático de voz
  async function iniciarDetectorVozAutomatico() {
    try {
      if (voiceDetectorActive || isMuted) return; // Evitar inicios multiples o si está muteado
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      voiceDetectorStream = audioMotion.audioCtx.createMediaStreamSource(stream);
      
      const analyser = audioMotion.audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      voiceDetectorStream.connect(analyser);
      const dataArray = new Uint8Array(analyser.fftSize);
      
      voiceDetectorActive = true;
      console.log('✅ Detector de voz automático activo');
      
      // Monitorear la voz continuamente
      voiceDetectionInterval = setInterval(() => {
        if (!voiceDetectorActive || isMuted) return;  // Respetar estado de mute
        
        analyser.getByteTimeDomainData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const norm = (dataArray[i] - 128) / 128;
          sum += norm * norm;
        }
        const rms = Math.sqrt(sum / dataArray.length);

        if (rms > voiceDetectionThreshold) {
          // Voz detectada
          if (!voiceDetectionStart) {
            voiceDetectionStart = Date.now();
          } else if (Date.now() - voiceDetectionStart > voiceDetectionDelay) {
            // Se mantiene la voz el tiempo suficiente, iniciar grabación
            if (!mediaRecorder || mediaRecorder.state !== 'recording') {
              console.log('🎤 Voz detectada - Iniciando grabación automática');
              openMicrophone();
              voiceDetectionStart = null; // Reset
            }
          }
        } else {
          // No hay voz
          voiceDetectionStart = null;
        }
      }, 100); // Revisar cada 100ms
      
    } catch (error) {
      console.error('❌ Error al iniciar detector de voz:', error);
    }
  }

  // Función para detener el detector de voz
  function detenerDetectorVozAutomatico() {
    if (voiceDetectionInterval) {
      clearInterval(voiceDetectionInterval);
      voiceDetectionInterval = null;
    }
    if (voiceDetectorStream) {
      voiceDetectorStream.disconnect();
      voiceDetectorStream = null;
    }
    voiceDetectorActive = false;
    console.log('Detector de voz detenido');
  }

  assistantAudioPlayer.addEventListener('ended', () => {
    console.log("Audio finalizado");
    // Reiniciar detector de voz automático solo si no está muteado
    if (!isMuted) {
      iniciarDetectorVozAutomatico();
    }
  });

  // document.getElementById('infoBtn').addEventListener('click', () => {
  //   if (microphoneOpen) return;
  //   assistantAudioPlayer.play();
  // });

  async function bindUIEvents() {
    $('#btnIniciarRecorrido').on('click', await iniciarRecorrido);
    $('#combo_edificio').on('change', onEdificioChange);
    $('#combo_pisos').on('change', onPisoChange);
    $('#btnConsultarDatos').on('click', function() {
      const idEdificio = $('#combo_edificio option:selected').val();
      const idPiso = $('#combo_pisos option:selected').val();
      const idAmbiente = $('#combo_ambientes option:selected').val();
      console.log(idEdificio, idPiso, idAmbiente);
      if (idEdificio && idPiso && idAmbiente) {
        informacionConsumo({ idEdificio, idPiso, idAmbiente });
      } else {
        Swal.fire('Error', 'Seleccione todos los campos.', 'error');
      }
    });
    $('#btn_firmar').on('click', function() {
      $('#modalFirma').modal('show');
    });
    $('#n_ficha').on('click', cambiarNumFicha);
    $('#text_nficha').on('blur', (e) => {
      const nuevoNum = e.target.value;
      if(!nuevoNum ||nuevoNum === $('#n_ficha').text()){
        document.getElementById('text_nficha').style.display = 'none';
        document.getElementById('n_ficha').style.display = '';
        return;
      }

      if(nuevoNum && nuevoNum !== $('#n_ficha').text()){
        Swal.fire({
          title: `¿Desea modificar el número de ficha ${$('#n_ficha').text()} por ${nuevoNum}?`, 
          text: "Importante: Modificar el número de ficha reiniciará toda la conversacion con el asistente.",
          width: 600,
          icon: "warning",
          showCancelButton: true,
          showDenyButton: true,
          confirmButtonText: "Modificar", 
          cancelButtonText: "Cancelar",
          denyButtonText: "Mantener ficha anterior"
        }).then((result) => {
          if (result.isConfirmed) {
            $('#n_ficha').text(nuevoNum);
            actualizarFicha(nuevoNum);
            // document.getElementById('text_nficha').style.display = 'none';
            // document.getElementById('n_ficha').style.display = '';
          }
          if(result.isConfirmed || result.isDenied){
            document.getElementById('text_nficha').style.display = 'none';
            document.getElementById('n_ficha').style.display = '';
          }
  
        });
      }
      
      
    });
    // $('#select_voz').on('change', verificarVoz);
    // $('#play_voz').on('click', reproducir);
    // $('#guardar_voz').on('click', guardarVocesDefault);
    $('#btnVerChat').on('click', mostrarChat);
    $('#btnVerForm').on('click', mostrarForm);
    $('#btnRecargarPagina').on('click', () => {
      location.reload()
    });
    $('#btnCerrarChat').on('click', cerrarChat)
  }

  function mostrarForm() {
    $('#modalRevision').modal('show');
  }

  function cambiarNumFicha(){
    Swal.fire({
      title: "¿Desea cambiar el número de ficha?",
      text: "Ingrese la clave para realizar el cambio:",
      input: "password",
      topLayer: true,
      inputAttributes: {
        autocapitalize: "off"
      },
      showCancelButton: true,
      confirmButtonText: "Modificar",
      cancelButtonText: "Cancelar",
      target: document.getElementById('modalRevision'),
      // showLoaderOnConfirm: true,
      preConfirm: (login) => {
        try {
          if (login === 'admin123') {
            return "Accediste";
          }else{
            return Swal.showValidationMessage("Clave incorrecta para modificar");
          }
          // return response.json();
        } catch (error) {
          Swal.showValidationMessage(`
            Request failed: ${error}
          `);
        }
      },
      allowOutsideClick: () => !Swal.isLoading()
    }).then((result) => {
      console.log(result)
      if(result.isConfirmed){
        document.getElementById('text_nficha').style.display = 'inline-block';
        document.getElementById('n_ficha').style.display = 'none';
      }
      
    });
  }

  function informacionConsumo(params) {
    $('.text-btn-consultar-datos').html('Consultando datos... <span class="indicator-progress">Cargando... <span class="spinner-border spinner-border-sm align-middle ms-2"></span></span>');
    $('#btnConsultarDatos, select').addClass('disabled');
    fetch(`/datos?idEdificacion=${params.idEdificio}&idPiso=${params.idPiso}&idAmbiente=${params.idAmbiente}&fechaInicio=${fechaInicio}&fechaFin=${fechaFin}`)
      .then(response => response.json())
      .then(result => {
        $('.text-btn-consultar-datos').html('Consultar datos');
        $('#btnConsultarDatos, select').removeClass('disabled');
        if (result.ok) {
          graficarInfoConsumo(result);
        } else {
          Swal.fire('Error', result.observacion, 'error');
        }
      })
      .catch(error => {
        $('.text-btn-consultar-datos').html('Consultar datos');
        $('#btnConsultarDatos, select').removeClass('disabled');
        Swal.fire("Error en el servidor.", "Error: " + error.message, "error");
      });
  }

  async function mostrarChat() {
    
    document.querySelector('#btnVerChat').classList.add('disabled');
    document.querySelector('.spinner-ver-chat').classList.remove('d-none');
    document.querySelector('.spinner-ver-chat').classList.add('d-flex');

    await fetch('/chats', { method: 'GET' })
    .then(response => response.json())
    .then(result => {
      document.querySelector('#btnVerChat').classList.remove('disabled');
      document.querySelector('.spinner-ver-chat').classList.remove('d-flex');
      document.querySelector('.spinner-ver-chat').classList.add('d-none');
      
      let resultado = '';
      
      if(result){
        
        result.forEach(e => {
        
          if(['assistant','tool'].includes(e.datos.role)){
            resultado += `
            <div class="message incoming">
              <small class="text-muted">${(e.datos.role === 'assistant' ? 'Asistente' : 'Tool')} • ${moment(e.creado).format('DD MMM YYY HH:Mmm')}</small>
              <pre class="mb-0">${e.datos.content}</pre>
              <div class="reactions">
                <button class="btn btn-sm btn-active-light-success ${e.reaccion === 1 ? `btn-light-success` : ``} reaction-btn" data-id="${e.id}" data-reaction="1">
                  <i class="ki-duotone ki-like fs-1">
                    <span class="path1"></span>
                    <span class="path2"></span>
                  </i>
                </button>
                <button class="btn btn-sm btn-active-light-danger  ${e.reaccion === 0 ? `btn-light-danger` : ``} reaction-btn fs-2" data-id="${e.id}" data-reaction="0">
                  <i class="ki-duotone ki-dislike fs-1">
                    <span class="path1"></span>
                    <span class="path2"></span>
                  </i>
                </button>
              </div>
            </div>`
          }else{
            resultado += `
            <div class="message outgoing">
              <small class="text-light">Tú • ${moment(e.creado).format('DD MMM YYY HH:Mmm')}</small>
              <pre class="mb-0">${e.datos.content}</pre>
            </div>
            `
  
          }
  
        });

      }

      document.querySelector('#chat').innerHTML = resultado;
      
      document.querySelector('#controles').style.display = 'none';
      document.querySelector('.card-avatar').style.display = 'none';
      document.querySelector('.card-chat').style.display = 'flex';

      document.querySelector('#chat').scrollTop = document.querySelector('#chat').scrollHeight;
      
      $('.reaction-btn').off('click').on('click', function() {
        const reaccion = $(this).data('reaction');
        const idMensaje = $(this).attr('data-id');
        
        // Aquí puedes manejar la reacción, por ejemplo, enviarla al servidor
        fetch('/reaccionar-msg', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reaccion, idMensaje })
        })
        .then(response => response.json())
        .then(data => {
          
          $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="1"]`).removeClass('btn-light-success');
          $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="0"]`).removeClass('btn-light-danger');
          
          if (reaccion === 1) {
            $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="1"]`).addClass('btn-light-success');
          } else if (reaccion === 0) {
            $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="0"]`).addClass('btn-light-danger');
          }
          
        })
        .catch(error => {
          console.error('Error al guardar la reacción:', error);
        });
      })
      
    }).catch(error => {
      console.error('Error:', error);
      document.querySelector('#btnVerChat').classList.remove('disabled');
      document.querySelector('.spinner-ver-chat').classList.remove('d-flex');
      document.querySelector('.spinner-ver-chat').classList.add('d-none');
    });

  }

  function cerrarChat() {
    document.querySelector('#controles').style.display = 'flex';
    document.querySelector('.card-avatar').style.display = 'flex';
    document.querySelector('.card-chat').style.display = 'none';
  }

  async function Conversar(audioBlob, type='voice') {
    
    // Creamos un nuevo controller para esta petición
    currentAbortController = new AbortController();
    const { signal } = currentAbortController;
    console.log("SE INICIO ABORT CONTROLLER")

    const formData = new FormData();

    formData.append('tipo', type);
    if(type == 'voice'){
      formData.append('voice', audioBlob, 'voice.webm');
    }else{
      formData.append('text', audioBlob);
    }
    console.log(audioBlob)
    formData.append('intencion', intencionConversar);

    let reader;
    let textoAcumulado = '';
    let buffer = '';
    const decoder = new TextDecoder('utf-8');

    // const output = document.getElementById("recomendaciones");
    // output.textContent = "";

    const output2 = document.getElementById("typeContenido");
    output2.textContent = "";

    try {
      const res = await fetch('/conversar', {
        method: 'POST',
        body: formData,
        signal,
        headers: { 'Accept': 'application/x-ndjson' } // Indicamos que esperamos NDJSON
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if(!$('#contenedor-typing').hasClass('ct-appear')){
          $('#contenedor-typing').addClass('ct-appear');
      }
      reader = res.body.getReader();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop(); // deja la última línea incompleta en buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          let msg;
          try {
            msg = JSON.parse(trimmed);
          } catch (e) {
            console.warn('Error al procesar la línea NDJSON:', trimmed);
            continue;
          }

          // console.debug(msg)
          // Manejo de mensajes dependiendo del tipo
          switch (msg.type) {
            case 'token':
              
              // Concatenar el token para mostrar texto en tiempo real
              textoAcumulado += msg.token || '';
              // output.textContent = textoAcumulado;
              // output.scrollTop = output.scrollHeight;
              output2.textContent = textoAcumulado;
              // output2.scrollTop = output.scrollHeight;
              // console.log('Texto acumulado:', textoAcumulado);
              break;
            case 'audio':
              // Aquí puedes manejar los datos de audio (por ejemplo, para reproducir)
              // console.log('Audio recibido', msg.data);
              // audioQueue.push(msg.data); // agrega a la cola para reproducción
              sendTalking(msg.data, 'true');
              playNext(); // función que maneja la reproducción
              break;
            case 'info':
              // Información adicional enviada por el backend
              if (msg.data) {
                // console.log("Información adicional recibida:", msg.data);
                ejecutarFuncion(msg.data); // Ejecuta alguna función con los datos
              }
              break;
            case 'grafico':
              // Información adicional enviada por el backend
              if (msg.data) {
                // console.log("Datos de gráficos recibidos:");
                // console.log(msg.data)
                // console.log(JSON.parse(msg.data))
                ejecutarFuncion(JSON.parse(msg.data)); // Ejecuta alguna función con los datos
              }
              break;
            case 'intenciones':
              // Información adicional enviada por el backend
              if (msg.data) {
                // console.log("Datos de gráficos recibidos:");
                // console.log(msg.data)
                // console.log(JSON.parse(msg.data))
                let datosIntenciones = JSON.parse(msg.data);
                intencionConversar = datosIntenciones.siguiente;
              }
              break;
            case 'final':
              // Si el stream terminó o hay una respuesta final
              const respuesta = msg.datos || {};
              if (respuesta.info?.length) {
                ejecutarFuncion(respuesta.info);
              }
              if (respuesta.respuesta) {
                hablar(respuesta); // Aquí manejas la respuesta final (TTS, etc.)
              }
              break;
            case 'end':
              console.log('Stream completo');
              break;
            default:
              console.log('Tipo de mensaje no reconocido:', msg);
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Petición abortada.');
      } else {
        console.error('Hubo un error con la petición:', error);
      }
    } finally {
      if (reader) {
        try { reader.releaseLock(); } catch (e) { console.error(e); }
      }
    }
  }

  $('#enviar_text').on('click', () => {
    let texto = $('#chat_text').val();

    Conversar(texto, "text");
  });

  // AudioContext para decodificar
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // Cola de fragmentos Base64
  const audioQueue = [];
  let isPlaying = false;

  // ============================== Funciones de Voz (Reconocimiento y Síntesis) ==============================
  async function iniciarRecorrido() {
    
    currentStreamId = genStreamId();
    iniciarController = new AbortController();

    //Detiene el sonido si es que está sonando
    sendTalking('base65off', 'false');

    document.querySelector('#btnIniciarRecorrido').classList.add('disabled');
    document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-none');
    document.querySelector('.spinner-iniciar-recorrido').classList.add('d-flex');
    
    const output = document.getElementById("recomendaciones");
    output.textContent = "";
    
    try {

      const res = await fetch("/inicializar", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-stream-id": currentStreamId },
        body: JSON.stringify({ stream: true })
      });

      // if (!res.ok) throw new Error(res.statusText);
      
      document.querySelector('#btnIniciarRecorrido').classList.remove('disabled');
      document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-flex');
      document.querySelector('.spinner-iniciar-recorrido').classList.add('d-none');
      
      if (!$('#contenedor-typing').hasClass('ct-appear')) {
        $('#contenedor-typing').addClass('ct-appear');
      }

      /*if(respuesta.info && respuesta.info.length > 0){
        console.log("Informacion adicional");
        ejecutarFuncion(respuesta.info)
      }
      
      if (respuesta.respuesta) {
        hablar(respuesta);
      }*/
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;
          // console.log(JSON.parse(line))
          const msg = JSON.parse(line);

          if (msg.type === "token") {
            output.textContent += msg.token;
            output.scrollTop = output.scrollHeight;
          }
          else if (msg.type === "audio") {
            // En lugar de reproducir al vuelo, lo añadimos a la cola
            // audioQueue.push(msg.data);
            sendTalking(msg.data, 'true');
            playNext();
          }
          else if (msg.type === "end") {
            console.log("Stream completo");
          }
        }
      }
      
    } catch (error) {
      if (error.name === "AbortError") {
        console.log("Stream abortado por el cliente");
      } else {
        console.error("Error:", err);
      }
      document.querySelector('#btnIniciarRecorrido').classList.remove('disabled');
      document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-flex');
      document.querySelector('.spinner-iniciar-recorrido').classList.add('d-none');
    
    } finally {
      iniciarController = null;
      // ... restablece UI ...
    }

  }

  // === Cancelación manual (garantizada) ===
  async function cancelarRecorrido() {

    sendTalking('base65off', 'false');
    
    try {
      if (iniciarController) iniciarController.abort();
    } catch (_) {}

    if (currentStreamId) {
      try {
        // sendBeacon funciona durante la navegación/cierre
        const data = JSON.stringify({ stream_id: currentStreamId });
        const blob = new Blob([data], { type: "application/json" });
        navigator.sendBeacon("/cancelar", blob);
      } catch (e) {
        // Fallback si sendBeacon falla
        fetch("/cancelar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          keepalive: true,
          body: JSON.stringify({ stream_id: currentStreamId })
        }).catch(() => {});
      }
    }
  }

  // Enlaza el botón cancelar de forma inequívoca:
  document.getElementById("btnCancelar")?.addEventListener("click", cancelarRecorrido);

  // Cancela automáticamente si el usuario cierra/recarga o navega:
  window.addEventListener("pagehide", cancelarRecorrido);
  window.addEventListener("beforeunload", cancelarRecorrido);
  document.addEventListener("visibilitychange", () => {
    // En algunos navegadores, si se va a background y quieres cortar:
    if (document.visibilityState === "hidden") cancelarRecorrido();
  });

  // Función para reproducir el siguiente de la cola
  async function playNext() {
    return false;
    if (isPlaying || audioQueue.length === 0) return;
    isPlaying = true;
    const base64 = audioQueue.shift();

    // Decodificar Base64 → ArrayBuffer
    const raw = atob(base64);
    const buf = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) buf[i] = raw.charCodeAt(i);

    try {
      const audioBuffer = await audioCtx.decodeAudioData(buf.buffer);
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtx.destination);
      source.onended = () => {
        isPlaying = false;
        playNext();  // en cuanto termine, lanzamos el siguiente
      };
      source.start();
    } catch (err) {
      console.error("Error al decodificar/reproducir audio:", err);
      isPlaying = false;
      playNext();
    }
  }

  async function hablar(data) {
    
    assistantAudioPlayer.src = `data:audio/wav;base64,${data.audio}`;
    assistantAudioPlayer.play();
    
  }

  function ejecutarFuncion(aFunciones) {
    const funciones = {
      // 'get_usuario': getDatosUsuario,
      'solicita_prediccion': predecirConsumo3,
      'solicita_recomendaciones': getRecomendaciones,
      'solicita_datos_consumo': getInfoLugar,
      'extraccion_incrementales': extraccion_datos_medico,
      'mostrar_formulario': modalRevision,
    };

    for (const afuncion of aFunciones) {
      const func = funciones[afuncion.nombre];
      func(afuncion.valor);
    }
  }

  function modalRevision(data){
    if(data['abrir']){
      $('#modalRevision').modal('show');
    }else{
      $('#modalRevision').modal('hide');
    }
  }

  function extraccion_datos_medico(data){
    console.log(JSON.stringify(data));

    // // Iterar sobre los datos y setear en el formulario
    for (const [key, value] of Object.entries(data)) {
      if (['provincia', 'ciudad', 'parroquia'].includes(key)) $('#' + key).val(value);
      if(key == 'es_estudiante') $('#estudiante_' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(key == 'institucion') $('#institucion_' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(key == 'nombre_institucion') $('#text_institucion').val(value);
      if (['facultad', 'carrera', 'nivel'].includes(key)) $('#' + key).val(value);
      if(key == 'select_facultad') $('#facultad_select').val(value).trigger('change');
      if(key == 'select_carrera') $('#carrera_select').val(value).trigger('change');
      if(key == 'select_nivel') $('#nivel_select').val(value).trigger('change');
      if(key == 'modalidad') {
        $('#modalidad_estudio').val(value).trigger('change');
        $('#modalidad_estudio_select').val(value).trigger('change');
      }

      if (['nombres', 'apellidos', 'cedula', 'celular', 'correo', 'edad', 'fecha_nacimiento', 'nacionalidad'].includes(key)) $('#' + key).val(value);
      if(key == 'sexo') $('#sexo_' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(key == 'sexo_otro') $('#text_sexo_otro').val(value).trigger('change');
      if (['identidad_genero', 'lugar_residencia', 'contacto_referencia'].includes(key)) $('#' + key).val(value);
      if(key == 'direccion') $('#direccion_domicilio').val(value).trigger('change');

      if(key == 'area_consulta') $('#' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(key == 'area_consulta_especifica') {
        if(value.toLowerCase() == 'prueba_embarazo') {
          $('#area_consulta_select').val('p_embarazo').trigger('change');
        }else{
          $('#area_consulta_select').val(value.toLowerCase()).trigger('change');
        }
      }

      if(key == 'atencion_medica_inmediata') $('#inmediata_' + value.toLowerCase()).prop('checked', true).trigger('change');
      // if(key == 'embarazada') $('#embarazada_' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(key == 'meses_embarazo') $('#'+key.toLowerCase()).val(value);
      // if(key == 'discapacidad') $('#discapacidad_' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(key == 'discapacidad_texto') $('#textarea_discapacidad').val(value);
      // if(key == 'carnet_discapacidad') $('#carnet_discapacidad_' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(['embarazada', 'discapacidad', 'carnet_discapacidad'].includes(key)) $('#' + key + '_' + value.toLowerCase()).prop('checked', true).trigger('change');
      if(key == 'estado_civil'){
        switch (value.toLowerCase()) {
          case 'casado':
          case 'union_hecho':
          case 'union_libre':
            $('#'+value.toLowerCase()).prop('checked', true).trigger('change');
            break;
          case 'viudo':
            $('#viuda_o').prop('checked', true).trigger('change');
            break;
          case 'soltero':
            $('#soltera_o').prop('checked', true).trigger('change');
            break;
          case 'divorciado':
            $('#divorciada_o').prop('checked', true).trigger('change');
            break;
          case 'separado':
            $('#separada_o').prop('checked', true).trigger('change');
            break;
          case 'otro':
            $('#otro_estado_civil').prop('checked', true).trigger('change');
            break;
          }
      }
      if(key == 'estado_civil_otro') $('#text_otro_estado_civil').val(value);
      if(key == 'etnia'){
        switch (value.toLowerCase()) {
          case 'indigena':
          case 'afrodescendiente':
            $('#'+value.toLowerCase()).prop('checked', true).trigger('change');
            break;
          case 'montubia':
            $('#montubio').prop('checked', true).trigger('change');
            break;
          case 'blanca':
            $('#blanca_o').prop('checked', true).trigger('change');
            break;
          case 'mestiza':
            $('#mestiza_o').prop('checked', true).trigger('change');
            break;
          case 'otra':
            $('#otra_etnia').prop('checked', true).trigger('change');
            break;
          }
      }
      if(key == 'etnia_otro') $('#text_otra_etnia').val(value);

    }
  }

  function getInfoLugar(data) {
    console.debug(data)
    if(data.ok){
      let ops = '';
      let params = data.params;
      const edificio = dataEdificios.find(e => e.nombre == params.edificio);
      console.debug(edificio)

      if(edificio){
        const piso = edificio.pisos.find(p => p.nombre == params.piso);
        if (piso) {
          ops = "<option value='' selected disabled>Seleccionar</option>";
          edificio.pisos.forEach(p => ops += `<option value='${p.id}'>${p.nombre}</option>`);
          $('#combo_pisos').html(ops);

          const ambiente = piso.ambientes.find(a => a.nombre == params.ambiente);
          if (ambiente) {
            ops = "<option value='' selected disabled>Seleccionar</option>";
            groupBy(piso.ambientes, 'tipoAmbiente').forEach(group => {
              ops += `<optgroup label="${group[0].tipoAmbiente}">`;
              group.forEach(item => ops += `<option value="${item.id}">${item.nombre}</option>`);
              ops += `</optgroup>`;
            });
            $('#combo_ambientes').html(ops);
          }
        }
      }

      $('#combo_edificio option').filter(function() { return $(this).text() === params.edificio; }).prop('selected', true);
      $('#combo_edificio').trigger('change');
      $('#combo_pisos option').filter(function() { return $(this).text() === params.piso; }).prop('selected', true);
      $('#combo_pisos').trigger('change');
      $('#combo_ambientes option').filter(function() { return $(this).text() === params.ambiente; }).prop('selected', true);
      $('#combo_ambientes').trigger('change');
      
      initFechas({ start: moment(params.fechaInicio), end: moment(params.fechaFin) });
      //console.log(respuesta);
    }

    graficarInfoConsumo(data);
    
  }
  
  function getRecomendaciones(respuesta) {
    //const args = respuesta;
    $('.data-recomendaciones').html(`${respuesta}`);
    $(".data-recomendaciones").get(0).scrollIntoView({ behavior: 'smooth' });
    //return { success: false, reason: "Se han proporcionado las recomendaciones al usuario" };
  }
  
  // ============================== Funciones para Llamadas a la API y Gestión de Datos ==============================
  async function getEdificios() {
    $('#combo_edificio, #combo_pisos, #combo_ambientes').html("<option value='0' selected disabled>Cargando...</option>");
    try {
      const response = await fetch(`/edificios`);
      const result = await response.json();
      $('#combo_edificio, #combo_pisos, #combo_ambientes').html("<option value='0' selected disabled>Seleccionar</option>");
      if (result.ok) {
        dataEdificios = result.datos;
        let ops = "<option value='' selected disabled>Seleccione el edificio</option>";
        result.datos.forEach(element => ops += `<option value='${element.id}'>${element.edificacion}</option>`);
        $('#combo_edificio').html(ops);
        // llenarModalInfoEdificios();
      } else {
        Swal.fire('Error', result.observacion, 'error');
      }
    } catch (error) {
      Swal.fire("Error en el servidor.", "Error: " + error.message, "error");
    }
  }

  function graficarInfoConsumo(result) {
    console.log(result);
    $('.consumo-actual-ambiente').html(
      result.datos.consumoAmbiente.kilovatio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    );
    $('.consumo-actual-edificio').html(
      result.datos.consumoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    );

    const resultConsumoActualAmbiente = result.datos.datos.map(e => ({ x: e.fecha, y: parseFloat(e.kilovatio) }));
    const resultConsumoActualEdificio = result.datos.datos.map(e => ({ x: e.fecha, y: parseFloat(e.totalKilovatioEdificio) }));
    const options = {
      series: [{
        name: 'Consumo actual del ambiente',
        data: resultConsumoActualAmbiente
      }, {
        name: 'Consumo actual del edificio',
        data: resultConsumoActualEdificio
      }]
    };
    chart1.updateOptions(options);
    if(result.datos.datos.length > 0){
      //predecirConsumo(result.datos.datos);
    }
  }

  function predecirConsumo3(datos) {
    const resultConsumoFuturoAmbiente = datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
    //const resultConsumoFuturoEdificio = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_total.toFixed(2)) }));
    const resultConsumoFuturoEdificio = datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
    const consumoFuturoAmbiente = resultConsumoFuturoAmbiente.reduce((acc, item) => acc + item.y, 0);
    //const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
    const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
    $('.consumo-futuro-ambiente').html(consumoFuturoAmbiente.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    $('.consumo-futuro-edificio').html(consumoFuturoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
    const options = {
      series: [{
        name: 'Consumo futuro del ambiente',
        data: resultConsumoFuturoAmbiente
      }, {
        name: 'Consumo futuro del edificio',
        data: resultConsumoFuturoEdificio
      }]
    };
    chart2.updateOptions(options);
  }

  function predecirConsumo() {
    const idEdificio = $('#combo_edificio option:selected').val();
    const idPiso = $('#combo_pisos option:selected').val();
    const idAmbiente = $('#combo_ambientes option:selected').val();
    const fecha = new Date().toISOString().split('T')[0]

    fetch(`/api/prediccion?edificio=${idEdificio}&piso=${idPiso}&ambiente=${idAmbiente}&fecha=${fecha}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(result => {
      if (result.ok) {
        const resultConsumoFuturoAmbiente = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
        //const resultConsumoFuturoEdificio = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_total.toFixed(2)) }));
        const resultConsumoFuturoEdificio = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
        const consumoFuturoAmbiente = resultConsumoFuturoAmbiente.reduce((acc, item) => acc + item.y, 0);
        //const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
        const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
        $('.consumo-futuro-ambiente').html(consumoFuturoAmbiente.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        $('.consumo-futuro-edificio').html(consumoFuturoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        //$('.consumo-futuro-edificio').html(consumoFuturoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        const options = {
          series: [{
            name: 'Consumo futuro del ambiente',
            data: resultConsumoFuturoAmbiente
          }, {
            name: 'Consumo futuro del edificio',
            data: resultConsumoFuturoEdificio
          }]
        };
        chart2.updateOptions(options);
      } else {
        Swal.fire('Ocurrió un error al consultar la información.', '', 'error');
      }
    });
  }
  
  // ------------------------------ Funciones de Inicialización ------------------------------
  function initMicrofono() {
    if (!window.webkitSpeechRecognition) {
      Swal.fire({
        title: "Error",
        text: "Su navegador no soporta el reconocimiento de voz.\nIntente con otro navegador",
        icon: "error",
        showConfirmButton: false,
        allowOutsideClick: false,
        footer: errorChromeMsg
      });
      disableFormControls();
    }
    if (!window.SpeechSynthesisUtterance) {
      Swal.fire({
        title: "Error",
        text: "Su navegador no soporta el intérprete de texto a voz.\nIntente con otro navegador",
        icon: "error",
        showConfirmButton: false,
        allowOutsideClick: false,
        footer: errorChromeMsg
      });
      disableFormControls();
    }
    if (!window.SpeechSynthesis) {
      Swal.fire({
        title: "Error",
        text: "Su navegador no soporta la reproducción de voz.\nIntente con otro navegador",
        icon: "error",
        showConfirmButton: false,
        allowOutsideClick: false,
        footer: `<em>Se recomienda usar ${errorChromeMsg} o ${errorEdgeMsg}</em>`
      });
      disableFormControls();
    }
  }

  function disableFormControls() {
    $('#cod-form').attr('disabled', 'true');
    $('#fecha_atencion').attr('disabled', 'true');
  }

  function initConsentimiento() {
    if (localStorage.getItem('autorizacion') == 1) {
      // inicializarDOM();
    } else {
      $('#modal_autorizacion').modal('show');
    }
    $('#rechazar_auto').on('click', () => clickAutorizacion('R'));
    $('#aceptar_autor').on('click', () => clickAutorizacion('A'));
  }

  // ------------------------------ Eventos de Selección ------------------------------
  function onEdificioChange(event) {
    const idEdificio = event.target.value;
    const edificio = dataEdificios.find(e => e.id == idEdificio);
    if (edificio) {
      let ops = "<option value='' selected disabled>Seleccionar</option>";
      edificio.pisos.forEach(p => ops += `<option value='${p.id}'>${p.nombre}</option>`);
      $('#combo_pisos').html(ops);
    }
  }

  function onPisoChange(event) {
    const idPiso = event.target.value;
    const pisoData = dataEdificios.find(e => e.pisos.find(p => p.id == idPiso));
    const piso = pisoData?.pisos.find(p => p.id == idPiso);
    if (piso) {
      let ops = "<option value='' selected disabled>Seleccionar</option>";
      groupBy(piso.ambientes, 'tipoAmbiente').forEach(group => {
        ops += `<optgroup label="${group[0].tipoAmbiente}">`;
        group.forEach(item => ops += `<option value="${item.id}">${item.nombre}</option>`);
        ops += `</optgroup>`;
      });
      $('#combo_ambientes').html(ops);
    }
  }

  function initFechas(params = {}) {
    const start = params.start ? params.start : moment();
    const end = params.end ? params.end : moment();
    const cb = function(start, end) {
      fechaInicio = start.format('YYYY-MM-DD');
      fechaFin = end.format('YYYY-MM-DD');
      $('#reportrange span').html(`${start.format('DD MMM YYYY')} - ${end.format('DD MMM YYYY')}`);
    };

    $('#reportrange').daterangepicker({
      startDate: start,
      endDate: end,
      ranges: {
        'Hoy': [moment(), moment()],
        'Ayer': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
        'Últimos 7 días': [moment().subtract(6, 'days'), moment()],
        'Últimos 30 días': [moment().subtract(29, 'days'), moment()],
        'Este mes': [moment().startOf('month'), moment().endOf('month')],
        'Último mes': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
      }
    }, cb);
    cb(start, end);
  }

  function initGraficos() {
    const colorVars = {
      success: KTUtil.getCssVariableValue('--bs-success'),
      info: KTUtil.getCssVariableValue('--bs-info'),
      warning: KTUtil.getCssVariableValue('--bs-warning'),
      gray: KTUtil.getCssVariableValue('--bs-gray-500'),
      border: KTUtil.getCssVariableValue('--bs-border-dashed-color')
    };

    const chartOptions = {
      noData: {
        text: 'Sin datos',
        align: 'center',
        verticalAlign: 'middle',
        style: { color: colorVars.gray, fontSize: '12px' }
      },
      series: [{
        name: 'Consumo actual',
        data: []
      }, {
        name: 'Consumo futuro',
        data: []
      }],
      chart: {
        fontFamily: 'Inter, Roboto, Poppins',
        type: 'area',
        height: parseInt(KTUtil.css($('#grafico1')[0], 'height')) + 10,
        toolbar: { show: false },
        sparkline: { enabled: false }
      },
      dataLabels: { enabled: false },
      markers: { size: 4, hover: { size: 7 } },
      stroke: { curve: 'smooth' },
      yaxis: { show: false },
      xaxis: { 
        categories: [],
        labels: {
          formatter: function(value) {
            return moment(value).format('DD MMM YYYY'); // Formatea la fecha
          }
        }
      },
      legend: { position: 'top' },
      tooltip: { 
        x: { format: 'dd MMM yyyy' },
        y: {
          formatter: function(value) {
            return `${value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} W`; // Agrega 'W' a los valores
          }
        }
      }
    };

    chart1 = new ApexCharts(document.querySelector("#grafico1"), chartOptions);
    chart1.render();
    chart2 = new ApexCharts(document.querySelector("#grafico2"), chartOptions);
    chart2.render();

  }

  function clickAutorizacion(accion) {
    console.log(accion);
    if (accion === 'A') {
      $('#modal_autorizacion').modal('hide');
      localStorage.setItem('autorizacion', 1);
      // inicializarDOM();
    } else {
      location.href = "https://www.google.com/";
    }
  }

  // ============================== Funciones de Firma ==============================
  let contextoPizarraFirma = null;

  function enviarFormulario() {
    // Recopilar datos del formulario
    let est_si = $('input[name="es_estudiante"]:checked').attr('id') === 'estudiante_si' ? 1 : 0;
    let inst_utm = 0;
    let inst_otro = 0;
    let inst_texto = '';
    let facultad = '';
    let carrera = '';
    let mod_p = 0;
    let mod_h = 0;
    let mod_l = 0;
    let nivel = '';
    if(est_si){
      inst_utm = $('input[name="institucion"]:checked').attr('id') === 'institucion_utm' ? 1 : 0;
      inst_otro = $('input[name="institucion"]:checked').attr('id') === 'institucion_otro' ? 1 : 0;

      if(inst_otro) {inst_texto = $('#text_institucion').val() || '';}
      // if(inst_utm){
      if(false){
        facultad = $("#facultad_select option:selected").text() || '';
        carrera = $("#carrera_select option:selected").text() || '';
        mod_p = $("#modalidad_estudio_select option:selected").text() === 'PRESENCIAL' ? 1 : 0;
        mod_h = $("#modalidad_estudio_select option:selected").text() === 'HÍBRIDA' ? 1 : 0;
        mod_l = $("#modalidad_estudio_select option:selected").text() === 'EN LÍNEA' ? 1 : 0;
        nivel = $("#nivel_select option:selected").text() || '';
      }else{
        facultad = $("#facultad").val() || '';
        carrera = $("#carrera").val() || '';
        mod_p = $("#modalidad_estudio option:selected").text() === 'PRESENCIAL' ? 1 : 0;
        mod_h = $("#modalidad_estudio option:selected").text() === 'HÍBRIDA' ? 1 : 0;
        mod_l = $("#modalidad_estudio option:selected").text() === 'EN LÍNEA' ? 1 : 0;
        nivel = $("#nivel").val() || '';
      }
    }

    let sex_otro = $('input[name="sexo"]:checked').attr('id') === 'sexo_otro' ? 1 : 0;
    let sex_texto = '';
    if(sex_otro){
      sex_texto = $('#text_sexo_otro').val() || '';
    }

    let lc = $('input[name="area_consulta"]:checked').attr('id') === 'laboratorio_clinico' ? 1 : 0;
    let lcv=0, lcs=0, hb=0, hc=0, pe = 0;

    if(lc){
      lcv = $("#area_consulta_select option:selected").val() === 'vih' ? 1 : 0;
      lcs = $("#area_consulta_select option:selected").val() === 'sifilis' ? 1 : 0;
      hb = $("#area_consulta_select option:selected").val() === 'hepatitis_b' ? 1 : 0;
      hc = $("#area_consulta_select option:selected").val() === 'hepatitis_c' ? 1 : 0;
      pe = $("#area_consulta_select option:selected").val() === 'p_embarazo' ? 1 : 0;
    }

    let emb_si = $('input[name="embarazada"]:checked').attr('id') === 'embarazada_si' ? 1 : 0;
    let emb_meses = '0';
    if(emb_si){
      emb_meses = $('#meses_embarazo').val() || '0';
    }

    let disc_si = $('input[name="discapacidad"]:checked').attr('id') === 'discapacidad_si' ? 1 : 0;
    let disc_texto = '';
    let carnet_si = 0;
    let carnet_no = 0;
    let porc_disc = '';
    if(disc_si){
      disc_texto = $('#textarea_discapacidad').val() || '';
      carnet_si = $('input[name="carnet_discapacidad"]:checked').attr('id') === 'carnet_discapacidad_si' ? 1 : 0;
      carnet_no = $('input[name="carnet_discapacidad"]:checked').attr('id') === 'carnet_discapacidad_no' ? 1 : 0;
      porc_disc = $('#porc_discapacidad').val() || '';
    }

    let estado_o = $('input[name="estado_civil"]:checked').attr('id') === 'otro_estado_civil' ? 1 : 0;
    let estado_texto = '';
    if(estado_o){
      estado_texto = $('#text_otro_estado_civil').val() || '';
    }

    let etnia_o = $('input[name="etnia"]:checked').attr('id') === 'otra_etnia' ? 1 : 0;
    let etnia_texto = '';
    if(etnia_o){
      etnia_texto = $('#text_otra_etnia').val() || '';
    }

    let datosFormulario = {
      num_ficha: $('#n_ficha').text() || 0,
      provincia: $('#provincia').val() || '',
      ciudad: $('#ciudad').val() || '',
      parroquia: $('#parroquia').val() || '',
      est_si,
      est_no: $('input[name="es_estudiante"]:checked').attr('id') === 'estudiante_no' ? 1 : 0,
      inst_utm, 
      inst_otro, 
      inst_texto, 
      facultad, 
      carrera, 
      mod_p, 
      mod_h, 
      mod_l, 
      nivel, 
      nombres: $('#nombres').val() || '', 
      apellidos: $('#apellidos').val() || '', 
      cedula: $('#cedula').val() || '', 
      celular: $('#celular').val() || '', 
      correo: $('#correo').val() || '', 
      edad: $('#edad').val() || '', 
      fecha_nac: $('#fecha_nacimiento').val() || '2000-01-01', 
      nacionalidad: $('#nacionalidad').val() || '', 
      sex_f: $('input[name="sexo"]:checked').attr('id') === 'sexo_femenino' ? 1 : 0, 
      sex_m: $('input[name="sexo"]:checked').attr('id') === 'sexo_masculino' ? 1 : 0, 
      sex_otro, 
      sex_texto, 
      identidad_genero: $('#identidad_genero').val() || '', 
      direccion: $('#direccion_domicilio').val() || '', 
      lugar_residencia: $('#lugar_residencia').val() || '', 
      contacto_ref: $('#contacto_referencia').val() || '', 
      gine: $('input[name="area_consulta"]:checked').attr('id') === 'ginecologia' ? 1 : 0,
      lc,
      lcv, 
      lcs, 
      hb, 
      hc, 
      pe, 
      aj: $('input[name="area_consulta"]:checked').attr('id') === 'asesoria_juridica' ? 1 : 0,
      ts: $('input[name="area_consulta"]:checked').attr('id') === 'trabajo_social' ? 1 : 0,
      psico: $('input[name="area_consulta"]:checked').attr('id') === 'psicologia' ? 1 : 0,
      ai_si: $('input[name="atencion_inmediata"]:checked').attr('id') === 'inmediata_si' ? 1 : 0,
      ai_no: $('input[name="atencion_inmediata"]:checked').attr('id') === 'inmediata_no' ? 1 : 0,
      emb_si, 
      emb_no: $('input[name="embarazada"]:checked').attr('id') === 'embarazada_no' ? 1 : 0, 
      emb_meses,
      disc_si,
      disc_no: $('input[name="discapacidad"]:checked').attr('id') === 'discapacidad_no' ? 1 : 0,
      disc_texto,
      carnet_si,
      carnet_no,
      porc_disc,
      estado_c: $('input[name="estado_civil"]:checked').attr('id') === 'casado' ? 1 : 0,
      estado_uh: $('input[name="estado_civil"]:checked').attr('id') === 'union_hecho' ? 1 : 0, 
      estado_v: $('input[name="estado_civil"]:checked').attr('id') === 'viuda_o' ? 1 : 0, 
      estado_so: $('input[name="estado_civil"]:checked').attr('id') === 'soltera_o' ? 1 : 0, 
      estado_d: $('input[name="estado_civil"]:checked').attr('id') === 'divorciada_o' ? 1 : 0, 
      estado_se: $('input[name="estado_civil"]:checked').attr('id') === 'separada_o' ? 1 : 0, 
      estado_ul: $('input[name="estado_civil"]:checked').attr('id') === 'union_libre' ? 1 : 0, 
      estado_o, 
      estado_texto, 
      etnia_i: $('input[name="etnia"]:checked').attr('id') === 'indigena' ? 1 : 0, 
      etnia_mo: $('input[name="etnia"]:checked').attr('id') === 'montubio' ? 1 : 0, 
      etnia_b: $('input[name="etnia"]:checked').attr('id') === 'blanca_o' ? 1 : 0, 
      etnia_a: $('input[name="etnia"]:checked').attr('id') === 'afrodescendiente' ? 1 : 0, 
      etnia_me: $('input[name="etnia"]:checked').attr('id') === 'mestiza_o' ? 1 : 0, 
      etnia_o, 
      etnia_texto, 
      firma: nombreArchivoFirma || ''
    };

    console.log(datosFormulario);

    // Convertir a JSON y enviar
    fetch('/guardar-formulario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosFormulario)
    })
    .then(response => response.json())
    .then(result => {
      if (result.ok) {
        Swal.fire({
          title: 'Éxito',
          text: result.observacion || 'La información ha sido guardada correctamente. La ficha ha sido enviada',
          icon: 'success',
          confirmButtonText: 'Aceptar'
        });
      } else {
        Swal.fire('Error', result.observacion || 'Error al guardar el formulario', 'error');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      Swal.fire('Error', 'Error al enviar el formulario: ' + error.message, 'error');
    });
  }

  // Exponer función global para el HTML si es necesario
  
  function initFirmaModal() {
    const canvasFirma = document.getElementById('pizarraFirma');
    if (!canvasFirma) return;
    
    contextoPizarraFirma = canvasFirma.getContext('2d');
    let dibujando = false;

    // Configuración de la línea
    contextoPizarraFirma.lineWidth = 3;
    contextoPizarraFirma.lineCap = 'round';
    contextoPizarraFirma.strokeStyle = '#000';
    contextoPizarraFirma.fillStyle = '#ffffff';
    contextoPizarraFirma.fillRect(0, 0, canvasFirma.width, canvasFirma.height);

    // Iniciar dibujo
    canvasFirma.addEventListener('pointerdown', (e) => {
      dibujando = true;
      const rect = canvasFirma.getBoundingClientRect();
      contextoPizarraFirma.beginPath();
      contextoPizarraFirma.moveTo(e.clientX - rect.left, e.clientY - rect.top);
    });

    // Dibujar mientras se mueve
    canvasFirma.addEventListener('pointermove', (e) => {
      if (dibujando) {
        const rect = canvasFirma.getBoundingClientRect();
        contextoPizarraFirma.lineTo(e.clientX - rect.left, e.clientY - rect.top);
        contextoPizarraFirma.stroke();
      }
    });

    // Detener dibujo
    window.addEventListener('pointerup', () => {
      dibujando = false;
    });

    // Event listeners para los botones
    document.getElementById('btnReiniciarFirma').addEventListener('click', reiniciarFirma);
    document.getElementById('btnGuardarFirma').addEventListener('click', () =>{
      Swal.fire({
        title: "Se firmara y guardara el formulario. ¿Desea continuar?", 
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Si", 
        cancelButtonText: "No"
      }).then((result) => {
        if (result.isConfirmed) {
          guardarFirma();
        }
      });
    });
  }

  function reiniciarFirma() {
    const canvasFirma = document.getElementById('pizarraFirma');
    if (!canvasFirma) return;
    
    const ctx = canvasFirma.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvasFirma.width, canvasFirma.height);
    console.log('Canvas de firma limpiado');
  }

  function guardarFirma() {
    const canvasFirma = document.getElementById('pizarraFirma');
    if (!canvasFirma) return;

    // Convertir canvas a blob y enviarlo al servidor
    canvasFirma.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append('firma', blob, 'firma.png');
      let archivo = 'firma';
      if($('#nombres').val() || $('#apellidos').val()){
        if($('#nombres').val()){
          archivo += '_'+$('#nombres').val();
        }
        if($('#apellidos').val()){
          archivo += '_'+$('#apellidos').val();
        }
      }else{
        archivo += '_' + $('#n_ficha').text();
      }
      try {
        const response = await fetch('/guardar-firma?archivo=' + archivo.replaceAll(' ', '_'), {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (result.ok) {
          nombreArchivoFirma = result.datos;
          const modalFirma = bootstrap.Modal.getInstance(document.getElementById('modalFirma'));
          if (modalFirma) modalFirma.hide();
          enviarFormulario();
          // Swal.fire({
          //   title: 'Éxito',
          //   text: 'La firma ha sido guardada correctamente',
          //   icon: 'success',
          //   confirmButtonText: 'Aceptar'
          // }).then(() => {
          //   // Cerrar modal después de guardar
            
          // });
        } else {
          Swal.fire('Error', result.observacion || 'Error al guardar la firma', 'error');
        }
      } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'Error al guardar la firma: ' + error.message, 'error');
      }
    }, 'image/png');
  }

  // ============================== Funciones Utilitarias ==============================
  function groupBy(arr, prop) {
    const map = new Map();
    arr.forEach(item => {
      if (!map.has(item[prop])) {
        map.set(item[prop], []);
      }
      map.get(item[prop]).push(item);
    });
    return Array.from(map.values());
  }

  function limpiarMensaje(mensaje) {
    return mensaje.replaceAll('*', '').replaceAll('\n', '. ');
  }

})();