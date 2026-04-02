import os
import smtplib
from email.message import EmailMessage

class CorreoControlador:
    def __init__(self):
        self.remitente = os.getenv("MAIL_FROM")
        self.password = os.getenv("MAIL_CODE")

    def enviarCorreo(self, destinatario, asunto, cuerpo_correo, adjuntos=None):
        # --- 1. CONFIGURACIÓN DE LOS DATOS ---
        correo_remitente = self.remitente
        # ¡Usa la contraseña de 16 caracteres de Google, NO tu contraseña normal!
        password_aplicacion = self.password

        correo_destinatario = destinatario
        # ruta_del_word = "ficha_firmada.docx" # El documento que generaste antes

        # --- 2. CREAR EL MENSAJE ---
        msg = EmailMessage()
        msg['Subject'] = asunto
        msg['From'] = correo_remitente
        msg['To'] = correo_destinatario

        # El cuerpo del correo
        # cuerpo_correo = """
        # Hola,

        # Adjunto encontrarás la Ficha de Intervención y Acogida generada por el sistema.

        # Saludos cordiales,
        # Centro FEF.
        # """
        msg.set_content(cuerpo_correo)

        # --- 3. BUCLE PARA ADJUNTAR MÚLTIPLES ARCHIVOS ---
        if adjuntos:
            for ruta in adjuntos:
                try:
                    # Abrimos cada archivo de la lista
                    with open(ruta, 'rb') as archivo:
                        datos_archivo = archivo.read()
                        # os.path.basename extrae solo el nombre final (ej. "ficha_firmada.docx")
                        nombre_archivo = os.path.basename(ruta) 
                        
                    # Lo agregamos al correo
                    msg.add_attachment(
                        datos_archivo, 
                        maintype='application', 
                        subtype='octet-stream', 
                        filename=nombre_archivo
                    )
                    print(f"✅ Archivo adjuntado: {nombre_archivo}")
                    
                except FileNotFoundError:
                    # Si un archivo de la lista no existe, el programa no se cae, solo te avisa y sigue con el siguiente
                    print(f"⚠️ Advertencia: No se encontró el archivo '{ruta}'. Se omitirá.")

        # --- 4. CONECTAR A GMAIL Y ENVIAR ---
        print("Enviando correo con los archivos adjuntos...")
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(correo_remitente, password_aplicacion)
                smtp.send_message(msg)  
            return {
                'ok': True,
                'datos': 'Correo enviado con éxito',
                'observacion': None
            }
            
        except Exception as e:
            print(f"❌ Ocurrió un error al enviar: {e}")
            return {
                'ok': False,
                'datos': None,
                'observacion': f'Error al enviar el correo. Error {e}'
            }