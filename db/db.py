#import mysql.connector
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine

class db():
    def __init__(self):
        rutaActual = os.getcwd()
        load_dotenv(os.path.join(rutaActual, '.env'))
        
    def consultarDato(self, sql):
        cursor = self.mysql.cursor(dictionary=True)

        cursor.execute(sql)
        data = cursor.fetchone()
        if(data != None and len(data) > 0):
            return data
        else:
            return None

    def consultarDatos(self, sql):
        cursor = self.mysql.cursor(dictionary=True)

        cursor.execute(sql)
        data = cursor.fetchall()
        if(len(data) > 0):
            return data
        else:
            return None
    
    def insertarDatos(self, sql, data, devolucion=0):
        cursor = self.mysql.cursor()
        cursor.execute(sql, data)
        idRow = cursor.lastrowid

        respuesta = None
        if devolucion:
            if idRow:
                respuesta = {'res': 1, 'id': idRow}
            else:
                respuesta = {'res': 0, 'id': 0}

        else:
            respuesta = 1 if idRow else 0
            
        self.mysql.commit()
        cursor.close()
        return respuesta
    
    def actualizarDatos(self, sql, data):
        cursor = self.mysql.cursor()
        cursor.execute(sql, data)
        self.mysql.commit()
        filasAct = cursor.rowcount
        
        respuesta = None
        if filasAct > 0:
            respuesta = 1
        else:
            respuesta = 0
            
        cursor.close()
        return respuesta
    
class PostgresDB():
    def __init__(self, app, dbname):
        self.app = app
        # self.dbname = dbname
        self.connection = None
        config = {
            'dbname':dbname,
            'user': os.getenv("PG_USER"),
            'password': os.getenv("PG_PASSWORD"),
            'host': os.getenv("PG_HOST"),
            'port': os.getenv("PG_PORT")
        }
        print("Datos de conexion: \n", config)
        self._conectar(config)
        self.engine = self._crear_engine(**config)
        conexion = self.probarConexion()
        print(conexion)

    def _conectar(self, config):
        """Crea una nueva conexión a la base de datos."""
        try:
            self.connection = psycopg2.connect(**config)
            self.connection.autocommit = True
        except Exception as e:
            print(f"❌ Error al conectar con PostgreSQL: {e}")
    
    def _crear_engine(self, dbname, user, password, host, port):
        uri_pg = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        return create_engine(uri_pg)

    def _reconectar_si_necesario(self):
        """Reconecta si la conexión está cerrada o inválida."""
        try:
            if self.connection is None or self.connection.closed != 0:
                print("⚠️ Conexión cerrada. Intentando reconectar...")
                self._conectar()
        except Exception as e:
            print(f"⚠️ Error al verificar la conexión: {e}")
            self._conectar()

    def probarConexion(self):
        try:
            self._reconectar_si_necesario()
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"status": "success", "message": "Conexión exitosa"}
        except OperationalError as e:
            self._conectar()
            return {"status": "error", "message": f"Reconectando... {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    def consultarDato(self, sql, params=None):
        self._reconectar_si_necesario()
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchone()
            return data if data else None

    def consultarDatos(self, sql, params=None):
        self._reconectar_si_necesario()
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchall()
            return data if data else None

    def insertarDatos(self, sql, params=None, devolucion=False):
        self._reconectar_si_necesario()
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            idRow = cursor.fetchone()[0] if devolucion else None
            return {'res': 1, 'id': idRow} if devolucion else 1

    def actualizarDatos(self, sql, params=None):
        self._reconectar_si_necesario()
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            filasAct = cursor.rowcount
            return 1 if filasAct > 0 else 0

    def eliminarDatos(self, sql, params=None):
        self._reconectar_si_necesario()
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            filasElim = cursor.rowcount
            return 1 if filasElim > 0 else 0
    
    def llamarFuncion(self, sql, params=None):
        self._reconectar_si_necesario()
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            resultados = cursor.fetchall()
            return resultados if resultados else None