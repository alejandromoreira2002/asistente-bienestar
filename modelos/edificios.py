import requests
import os
from db.db import PostgresDB
from functools import reduce
from modelos.agentes import AgentesModelo

class EdificiosModelo:
    def __init__(self, app):
        self.db = PostgresDB(app, os.getenv("PG_DBSB"))
        self.modeloAgentes = AgentesModelo(app)
    
    def getConsumoEdificiosAsisSQL(self, sql):
        print("Impresion de consulta de energia:")
        print(sql)
        try:
            datos = self.db.consultarDatos(sql)
            return {"res": 1, "data": {'ok':True, 'datos':self.construirObjetoConsumo(datos)}}
        except Exception as e:
            print("Error al consultar:")
            print(e)
            return {"res": 0, "data": str(e)}

    def construirObjetoConsumo(self, datos):
        consumoAmbiente = {
            'amperio': sum(d['total_amperio'] for d in datos if d['total_amperio']),
            'kilovatio': sum(d['total_kilovatio'] for d in datos if d['total_kilovatio'])
        }

        consumoEdificio = sum(d['total_kilovatio_edificio'] for d in datos if d['total_kilovatio_edificio'])

        datosConsumo = [
            {
                'amperio': d['total_amperio'] or 0.00,
                'kilovatio': d['total_kilovatio'] or 0.00,
                'fecha': d['fecha'],
                'totalKilovatioEdificio': d['total_kilovatio_edificio'] or 0.00,
            } for d in datos
        ]

        objetoConsumo = {
            'consumoAmbiente': consumoAmbiente,
            'consumoEdificio': consumoEdificio,
            'datos': datosConsumo
        }

        return objetoConsumo
    
    def consumoSemana(self, edificio, piso, ambiente, fechaInicio, fechaFin):
        print("Envio de datos:")
        print(edificio, piso, ambiente, fechaInicio,fechaFin)
        sql = f""
        try:
            datos = self.db.consultarDatos(sql)
            return {"res": 1, "data": {'ok':True, 'datos':datos}}
        except Exception as e:
            print("Error al consultar:")
            print(e)
            return {"res": 0, "data": str(e)}
     