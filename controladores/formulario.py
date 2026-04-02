from modelos.formulario import FormularioModelo
from controladores.correo import CorreoControlador
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm  # Importamos Milímetros para darle tamaño a la firma
import os
import smtplib
from email.message import EmailMessage

class FormularioControlador:
    def __init__(self, app):
        self.correo = CorreoControlador()
        self.modelo = FormularioModelo(app)
        # self.enviarFormulario('tedalemorvel@gmail.com', adjuntos=['Ficha_3.docx'])
        # self.generarFormulario(1)
        # self.pruebaFormulario()
    
    def pruebaFormulario(self):
        print("Datos del formulario:")
        form = self.modelo.getFormulario(1)
        print(str(form[0]['fecha_nac']))
        print("\nNúmero de ficha actual:")
        print(self.modelo.getNumFicha())
    
    def getNumFicha(self):
        numFicha = self.modelo.getNumFicha()
        numFicha = numFicha[0]['num_ficha'] + 1 if numFicha else 1
        return numFicha
    
    def registrarFormulario(self, datos):
        if self.modelo.existeNumFicha(datos['num_ficha']):
            return {'ok': False, 'observacion': f"El número de ficha {datos['num_ficha']} ya existe. Por favor, registre con otro número."}
        
        resultado = self.modelo.registrarFormulario(datos['num_ficha'], datos['provincia'], datos['ciudad'], datos['parroquia'], datos['est_si'], datos['est_no'], datos['inst_utm'], datos['inst_otro'], datos['inst_texto'], datos['facultad'], datos['carrera'], datos['mod_p'], datos['mod_h'], datos['mod_l'], datos['nivel'], datos['nombres'], datos['apellidos'], datos['cedula'], datos['celular'], datos['correo'], datos['edad'], datos['fecha_nac'], datos['nacionalidad'], datos['sex_f'], datos['sex_m'], datos['sex_otro'], datos['sex_texto'], datos['identidad_genero'], datos['direccion'], datos['lugar_residencia'], datos['contacto_ref'], datos['gine'], datos['lc'], datos['lcv'], datos['lcs'], datos['hb'], datos['hc'], datos['pe'], datos['aj'], datos['ts'], datos['psico'], datos['ai_si'], datos['ai_no'], datos['emb_si'], datos['emb_no'], datos['emb_meses'], datos['disc_si'], datos['disc_no'], datos['disc_texto'], datos['carnet_si'], datos['carnet_no'], datos['porc_disc'], datos['estado_c'], datos['estado_uh'], datos['estado_v'], datos['estado_so'], datos['estado_d'], datos['estado_se'], datos['estado_ul'], datos['estado_o'], datos['estado_texto'], datos['etnia_i'], datos['etnia_mo'], datos['etnia_b'], datos['etnia_a'], datos['etnia_me'], datos['etnia_o'], datos['etnia_texto'], datos['firma'])
        return resultado[0][0] if resultado else None

    def generarFormulario(self, num_ficha):
        formulario = self.modelo.getFormulario(int(num_ficha))
        
        if formulario:
            base_dir = os.environ.get('APP_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ruta_archivos = os.path.join(base_dir, 'docs')
            
            archivo_plantilla = os.path.join(ruta_archivos, 'plantilla_fef.docx')
            doc = DocxTemplate(archivo_plantilla)
            
            contexto = self.adaptarDatosParaDocx(formulario[0])
            
            ruta_firmas = os.path.join(ruta_archivos, 'firmas')
            archivo_firma = contexto.get('firma', '')
            if archivo_firma:
                ruta_firma = os.path.join(ruta_firmas, archivo_firma)
                imagen_firma = InlineImage(doc, ruta_firma, height=Cm(1.15))
                contexto['firma'] = imagen_firma
            
            doc.render(contexto)
            
            ruta_forms = os.path.join(ruta_archivos, 'formularios')
            nombre_archivo_salida = f"Ficha_{contexto['num_ficha']}.docx"
            form_generado = os.path.join(ruta_forms, nombre_archivo_salida)
            doc.save(form_generado)

            print(f"✅ Documento '{nombre_archivo_salida}' generado con éxito.")

            # subprocess.run([
            #     "libreoffice",
            #     "--headless",
            #     "--convert-to", "pdf",
            #     f"{form_generado}"
            # ])
            
            # print(f"✅ Documento '{nombre_archivo_salida}' convertido a PDF con éxito.")
            return nombre_archivo_salida
        else:
            print(f"No se encontró el formulario con num_ficha: {num_ficha}")
            return None
    
    def adaptarDatosParaDocx(self, form):
        # Aquí puedes adaptar los datos del formulario para que sean compatibles con la plantilla de Word
        # Por ejemplo, convertir booleanos a "Sí"/"No", formatear fechas, etc.
        return {
            "num_ficha": str(form['num_ficha']),
        
            # # Datos Iniciales
            "provincia": form['provincia'],
            "ciudad": form['ciudad'],
            "parroquia": form['parroquia'],
            "est_si": "X" if form['est_si'] else " ",
            "est_no": "X" if form['est_no'] else " ",
            "inst_utm": "X" if form['inst_utm'] else " ",
            "inst_otro": "X" if form['inst_otro'] else " ",
            "inst_texto": form['inst_texto'],
            "facultad": form['facultad'],
            "carrera": form['carrera'],
            "mod_p": "X" if form['mod_p'] else " ",
            "mod_h": "X" if form['mod_h'] else " ",
            "mod_l": "X" if form['mod_l'] else " ",
            "nivel": form['nivel'],
            
            # # Identificacion del Usuario
            "nombres": form['nombres'],
            "apellidos": form['apellidos'],
            "cedula": form['cedula']+(" "*((21*2)-len(form['cedula']))) if form['cedula'] else "_____________________",
            "celular": form['celular']+(" "*((21*2)-len(form['celular']))) if form['celular'] else "_____________________",
            "correo": form['correo'] if form['correo'] else "_____________________",
            "edad": str(form['edad'])+(" "*((11*2)-len(str(form['edad'])))) if str(form['edad']) else "___________",
            "fecha_nac": str(form['fecha_nac'])+(" "*((21*2)-10)) if form['fecha_nac'] else "_____________________",
            "nacionalidad": form['nacionalidad'] if form['nacionalidad'] else "_______________________________",
            "sex_f": "X" if form['sex_f'] else " ",
            "sex_m": "X" if form['sex_m'] else " ",
            "sex_otro": form['sex_otro'] if form['sex_otro'] else "_______________________________________________", 
            "identidad_genero": form['identidad_genero'] if form['identidad_genero'] else "_______________________________________________",
            "direccion": form['direccion'] if form['direccion'] else "______________________________________________________________________________________",
            "lugar_residencia": form['lugar_residencia'] if form['lugar_residencia'] else "_______________________________________",
            "contacto_ref": form['contacto_ref'] if form['contacto_ref'] else "____________________________________________________________________________",
            
            # # Área de Consulta
            "gine": "X" if form['gine'] else " ",
            "lc": "X" if form['lc'] else " ",
            "v": "X" if form['v'] else " ",
            "s": "X" if form['s'] else " ",
            "hb": "X" if form['hb'] else " ",
            "hc": "X" if form['hc'] else " ",
            "pe": "X" if form['pe'] else " ",
            "aj": "X" if form['aj'] else " ",
            "ts": "X" if form['ts'] else " ",
            "psico": "X" if form['psico'] else " ",
            
            # # Datos Personales
            "ai_si": "   X   " if form['ai_si'] else "       ",
            "ai_no": "   X   " if form['ai_no'] else "       ",
            "emb_si": "   X   " if form['emb_si'] else "       ",
            "emb_no": "   X   " if form['emb_no'] else "       ",
            "emb_meses": f"   {form['emb_meses']}   " if str(form['emb_meses']) else "       ",
            "disc_si": "   X   " if form['disc_si'] else "       ",
            "disc_no": "   X   " if form['disc_no'] else "       ",
            "disc_texto": form['disc_texto'] if form['disc_texto'] else "",
            "carnet_si": "      X     " if form['carnet_si'] else "            ",
            "carnet_no": "      X     " if form['carnet_no'] else "            ",
            "porc_disc": f"    {form['porc_disc']}    " if str(form['porc_disc']) else "           ",
            "estado_c": "    X    " if form['estado_c'] else "         ",
            "estado_uh": "    X    " if form['estado_uh'] else "         ",
            "estado_v": "    X    " if form['estado_v'] else "         ",
            "estado_so": "    X    " if form['estado_so'] else "         ",
            "estado_d": "    X    " if form['estado_d'] else "         ",
            "estado_se": "    X    " if form['estado_se'] else "         ",
            "estado_ul": "    X    " if form['estado_ul'] else "         ",
            "estado_o": "    X    " if form['estado_o'] else "         ",
            "estado_texto": form['estado_texto'] if form['estado_texto'] else "________________________________",
            "etnia_i": "    X    " if form['etnia_i'] else "         ", 
            "etnia_mo": "    X   " if form['etnia_mo'] else "         ", 
            "etnia_b": "    X    " if form['etnia_b'] else "         ", 
            "etnia_a": "    X    " if form['etnia_a'] else "         ", 
            "etnia_me": "    X    " if form['etnia_me'] else "         ", 
            "etnia_o": "    X    " if form['etnia_o'] else "         ", 
            "etnia_texto": form['etnia_texto'] if form['etnia_texto'] else "________________________________",
            
            # # Firma
            "firma": form['firma'] if form['firma'] else ""
        }
        # datos_adaptados = {}
        # for clave, valor in formulario.items():
        #     if isinstance(valor, bool):
        #         datos_adaptados[clave] = "Sí" if valor else "No"
        #     elif isinstance(valor, (int, float)):
        #         datos_adaptados[clave] = str(valor)
        #     elif isinstance(valor, str):
        #         datos_adaptados[clave] = valor
        #     else:
        #         datos_adaptados[clave] = str(valor)  # Convertir otros tipos a string
        # return datos_adaptados
        
    def enviarFormulario(self, destinatario, adjuntos = None):
        asunto = "Se ha recibido una nueva ficha de intervención y acogida"
        cuerpo_correo = """
        Nueva ficha de intervención y acogida recibida. Favor revisar el documento adjunto.
        """
        # print(adjuntos)
        
        formularios = None
        if adjuntos and len(adjuntos) > 0:
            formularios = []
            for adjunto in adjuntos:
                base_dir = os.environ.get('APP_BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                ruta_forms = os.path.join(base_dir, 'docs', 'formularios')
                form = os.path.join(ruta_forms, adjunto)
                formularios.append(form)
            
        respuesta = self.correo.enviarCorreo(
            destinatario,
            asunto=asunto,
            cuerpo_correo=cuerpo_correo,
            adjuntos=formularios
        )
        
        print(respuesta)
        
    
    
    
    