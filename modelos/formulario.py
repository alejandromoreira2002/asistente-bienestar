from db.db import PostgresDB
import os

class FormularioModelo:
    def __init__(self, app):
        self.db = PostgresDB(app, os.getenv("PG_DB"))
        #self.db.app = None  # Asignar la aplicación a la instancia de PostgresDB
    
    # [RealDictRow([('num_ficha', 1), ('provincia', 'manabi'), ('ciudad', 'portoviejo'), 
    #               ('parroquia', 'villas'), ('est_si', True), ('est_no', False), 
    #               ('inst_utm', True), ('inst_otro', False), ('inst_texto', ''), 
    #               ('facultad', 'Informatica'), ('carrera', 'Sistemas'), ('mod_p', True), 
    #               ('mod_h', False), ('mod_l', False), ('nivel', 'primero'), 
    #               ('nombres', 'Teddy Alejandro'), ('apellidos', 'Moreira Velez'), 
    #               ('cedula', '1316307618'), ('celular', '0997679158'), 
    #               ('correo', 'teddy.moreira@utm.edu.ec'), ('edad', 24), 
    #               ('fecha_nac', datetime.date(2002, 1, 24)), ('nacionalidad', 'ecuatoriano'), 
    #               ('sex_f', False), ('sex_m', True), ('sex_otro', False), ('sex_texto', ''), 
    #               ('identidad_genero', ''), ('direccion', 'portoviejo'), 
    #               ('lugar_residencia', 'portoviejo'), ('contacto_ref', 'ale 2222'), 
    #               ('gine', False), ('lc', True), ('v', False), ('s', False), ('hb', True), 
    #               ('hc', False), ('pe', False), ('aj', False), ('ts', False), 
    #               ('psico', False), ('ai_si', True), ('ai_no', False), ('emb_si', True), 
    #               ('emb_no', False), ('emb_meses', 2), ('disc_si', True), ('disc_no', False), 
    #               ('carnet_si', True), ('carnet_no', False), ('porc_disc', '20%'), 
    #               ('estado_c', True), ('estado_uh', False), ('estado_v', False), 
    #               ('estado_so', False), ('estado_d', False), ('estado_se', False), 
    #               ('estado_ul', False), ('estado_o', False), ('estado_texto', ''), 
    #               ('etnia_i', False), ('etnia_mo', True), ('etnia_b', False), 
    #               ('etnia_a', False), ('etnia_me', False), ('etnia_o', False), 
    #               ('etnia_texto', '0'), ('firma', 'firma_teddy_alejandro_moreira.png')])]
    
    def getFormulario(self, num_ficha):
        # Aqui se obtendra el historial de mensajes de la bd
        sql = f"SELECT num_ficha, provincia, ciudad, parroquia, est_si, est_no, inst_utm, inst_otro, inst_texto, facultad, carrera, mod_p, mod_h, mod_l, nivel, nombres, apellidos, cedula, celular, correo, edad, fecha_nac, nacionalidad, sex_f, sex_m, sex_otro, sex_texto, identidad_genero, direccion, lugar_residencia, contacto_ref, gine, lc, v, s, hb, hc, pe, aj, ts, psico, ai_si, ai_no, emb_si, emb_no, emb_meses, disc_si, disc_no, disc_texto, carnet_si, carnet_no, porc_disc, estado_c, estado_uh, estado_v, estado_so, estado_d, estado_se, estado_ul, estado_o, estado_texto, etnia_i, etnia_mo, etnia_b, etnia_a, etnia_me, etnia_o, etnia_texto, firma FROM bienestar.formulario WHERE num_ficha = {num_ficha} ORDER BY num_ficha ASC LIMIT 1"
        formulario = self.db.consultarDatos(sql)
        return formulario
    
    def getNumFicha(self):
        # Aqui se obtendra el historial de mensajes de la bd
        sql = f"SELECT num_ficha FROM bienestar.formulario ORDER BY num_ficha DESC LIMIT 1"
        num_ficha = self.db.consultarDatos(sql)
        return num_ficha
    
    def existeNumFicha(self, num_ficha):
        # Aqui se obtendra el historial de mensajes de la bd
        sql = f"SELECT num_ficha FROM bienestar.formulario WHERE num_ficha = {num_ficha} LIMIT 1"
        num_ficha = self.db.consultarDatos(sql)
        return True if num_ficha and len(num_ficha)>0 else False
    
    def registrarFormulario(self, num_ficha, provincia, ciudad, parroquia, est_si, est_no, inst_utm, inst_otro, inst_texto, facultad, carrera, mod_p, mod_h, mod_l, nivel, nombres, apellidos, cedula, celular, correo, edad, fecha_nac, nacionalidad, sex_f, sex_m, sex_otro, sex_texto, identidad_genero, direccion, lugar_residencia, contacto_ref, gine, lc, v, s, hb, hc, pe, aj, ts, psico, ai_si, ai_no, emb_si, emb_no, emb_meses, disc_si, disc_no, disc_texto, carnet_si, carnet_no, porc_disc, estado_c, estado_uh, estado_v, estado_so, estado_d, estado_se, estado_ul, estado_o, estado_texto, etnia_i, etnia_mo, etnia_b, etnia_a, etnia_me, etnia_o, etnia_texto, firma):
        # Aqui se guardara el mensaje en la bd
        accion = "registrar"
        parametros = (accion, str(num_ficha), str(provincia), str(ciudad), str(parroquia), str(est_si), str(est_no), str(inst_utm), str(inst_otro), str(inst_texto), str(facultad), str(carrera), str(mod_p), str(mod_h), str(mod_l), str(nivel), str(nombres), str(apellidos), str(cedula), str(celular), str(correo), str(edad), str(fecha_nac), str(nacionalidad), str(sex_f), str(sex_m), str(sex_otro), str(sex_texto), str(identidad_genero), str(direccion), str(lugar_residencia), str(contacto_ref), str(gine), str(lc), str(v), str(s), str(hb), str(hc), str(pe), str(aj), str(ts), str(psico), str(ai_si), str(ai_no), str(emb_si), str(emb_no), str(emb_meses), str(disc_si), str(disc_no), str(disc_texto), str(carnet_si), str(carnet_no), str(porc_disc), str(estado_c), str(estado_uh), str(estado_v), str(estado_so), str(estado_d), str(estado_se), str(estado_ul), str(estado_o), str(estado_texto), str(etnia_i), str(etnia_mo), str(etnia_b), str(etnia_a), str(etnia_me), str(etnia_o), str(etnia_texto), str(firma))
        # print("Parámetros para registrar formulario:")
        # print(parametros)
        resultado = self.db.llamarFuncion(
            'SELECT * FROM bienestar.gestionar_formulario(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', 
            parametros
        )
        return resultado