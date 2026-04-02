import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import time
from unidecode import unidecode
from rapidfuzz import process, fuzz

import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error
from skforecast.datasets import fetch_dataset
from skforecast.sarimax import Sarimax
from skforecast.recursive import ForecasterSarimax
from skforecast.model_selection import TimeSeriesFold, backtesting_sarimax, grid_search_sarimax
from skforecast.plot import set_dark_theme
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
warnings.filterwarnings('ignore')
import joblib
import re
from datetime import date, datetime, timedelta
import numpy as np

def getPrediccionConsumo(datos):
    df = pd.DataFrame(datos)
    
    df = df.rename(columns={'x': 'fecha', 'y': 'kilovatio'})

    # Asegúrate de que la columna 'fecha' sea de tipo datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['kilovatio'] = pd.to_numeric(df['kilovatio'])
    df['totalKilovatioEdificio'] = pd.to_numeric(df['totalKilovatioEdificio'])

    # Ordenar los datos por fecha, si no están ordenados
    df = df.sort_values('fecha')

    # Mostrar las primeras filas para verificar
    print(df.head())

    # Configurar la columna 'consumo' como la serie temporal
    y = df['kilovatio']

    # Ajustar el modelo ARIMA (p=1, d=1, q=1 es un buen punto de partida)
    model = ARIMA(y, order=(1, 1, 1))
    model_fit = model.fit()

    # Configurar la columna 'consumo' como la serie temporal
    y1 = df['totalKilovatioEdificio']

    # Ajustar el modelo ARIMA (p=1, d=1, q=1 es un buen punto de partida)
    model1 = ARIMA(y1, order=(1, 1, 1))
    model_fit1 = model1.fit()

    # Realizar la predicción para el día siguiente
    forecast_steps = 7
    forecast = model_fit.forecast(steps=forecast_steps)
    forecast1 = model_fit1.forecast(steps=forecast_steps)


    # Generar las fechas para los próximos 30 días
    last_date = df['fecha'].max()
    forecast_dates = pd.date_range(start=last_date, periods=forecast_steps + 1, freq='D')[1:]

    # Crear un DataFrame con las predicciones futuras
    forecast_df = pd.DataFrame({'fecha': forecast_dates, 'consumo_predicho': forecast, 'consumo_total': forecast1})
    forecast_df['fecha'] = forecast_df['fecha'].dt.strftime('%Y-%m-%d')

    resultado = forecast_df.to_dict(orient='records')
    return resultado


    #Hacerlo por semana
    #Que antes de hacer la prediccion el asistente pregunte a cuanto tiempo se quiere predecir
    # Y que te pregunte si habra un evento especial en la semana

def getPrediccionConsumoAnt(datos):
    df = pd.DataFrame(datos)
    
    df = df.rename(columns={'x': 'fecha', 'y': 'kilovatio'})

    # Asegúrate de que la columna 'fecha' sea de tipo datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['kilovatio'] = pd.to_numeric(df['kilovatio'])
    df['totalKilovatioEdificio'] = pd.to_numeric(df['totalKilovatioEdificio'])

    # Ordenar los datos por fecha, si no están ordenados
    df = df.sort_values('fecha')

    # Mostrar las primeras filas para verificar
    print(df.head())

    # Configurar la columna 'consumo' como la serie temporal
    y = df['kilovatio']

    # Ajustar el modelo ARIMA (p=1, d=1, q=1 es un buen punto de partida)
    model = ARIMA(y, order=(1, 1, 1))
    model_fit = model.fit()

    # Configurar la columna 'consumo' como la serie temporal
    y1 = df['totalKilovatioEdificio']

    # Ajustar el modelo ARIMA (p=1, d=1, q=1 es un buen punto de partida)
    model1 = ARIMA(y1, order=(1, 1, 1))
    model_fit1 = model1.fit()

    # Realizar la predicción para el día siguiente
    forecast_steps = 30
    forecast = model_fit.forecast(steps=forecast_steps)
    forecast1 = model_fit1.forecast(steps=forecast_steps)


    # Generar las fechas para los próximos 30 días
    last_date = df['fecha'].max()
    forecast_dates = pd.date_range(start=last_date, periods=forecast_steps + 1, freq='D')[1:]

    # Crear un DataFrame con las predicciones futuras
    forecast_df = pd.DataFrame({'fecha': forecast_dates, 'consumo_predicho': forecast, 'consumo_total': forecast1})
    forecast_df['fecha'] = forecast_df['fecha'].dt.strftime('%Y-%m-%d')

    resultado = forecast_df.to_dict(orient='records')
    return resultado


    #Hacerlo por semana
    #Que antes de hacer la prediccion el asistente pregunte a cuanto tiempo se quiere predecir
    # Y que te pregunte si habra un evento especial en la semana

def detectar_intencion(consulta, etiquetas):
    print("Paso #2: Detección de la intención de la consulta del usuario.")
    tiempo_inicio_intencion = time.time()
    model_name = "Recognai/bert-base-spanish-wwm-cased-xnli"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)

    resultado = classifier(consulta, etiquetas, hypothesis_template="Que accion desea realizar el usuario con esta consulta: {}.")
    tiempo_fin_intencion = time.time()
    print(f"Tiempo de ejecución de la intención (BERT): {tiempo_fin_intencion - tiempo_inicio_intencion:.2f} segundos")
    # Tomamos la etiqueta con mayor score
    mejor_intencion = resultado["labels"][0]
    print(f"Resultado de la intención: {mejor_intencion}")
    return {
        "intencion": mejor_intencion,
        "confianza": round(resultado["scores"][0], 3)
    }

def norm(s: str) -> str:
    return unidecode(s.lower().strip())

def fuzzy_lookup(name: str, items: list, key='nombre', threshold=80):
    choices = [norm(item[key]) for item in items]
    match = process.extractOne(name, choices, scorer=fuzz.QRatio) #.partial_ratio
    if match and match[1] >= threshold:
        return items[choices.index(match[0])]
    return None

def getInfoLugar(comps, data):
    # Validación de extracción
    if not comps:
        #return {"ok": False, "datos": "No pude extraer edificio, piso ni ambiente de la consulta."}
        return {"ok": False, "datos": "No pudiste reconocer el edificio, piso ni ambiente de la peticion del usuario."}
    
    # Validaciones de contexto
    
    #  - Si pide solo piso sin edificio → error
    if 'piso' in comps and 'edificio' not in comps:
        return {
            "ok": False,
            "datos": "Te solicitaron un piso pero no especificaron edificio; al haber varios pisos en distintos edificios, no puedes filtrar. Dile al usuario que te diga el edificio que desea consultar."
        }
    #  - Si pide solo ambiente sin piso ni edificio → error
    if 'ambiente' in comps and ('piso' not in comps or 'edificio' not in comps):
        return {
            "ok": False,
            "datos": "Te solicitaron un ambiente pero no especificaron piso y edificio; al haber múltiples ambientes en distintos pisos y edificios, no puedes filtrar. Dile al usuario que te diga el edificio y el piso que desea consultar."
        }
    
    # #  - Si no menciona fechas → error
    # if 'fechainicio' not in comps and 'fechafin' not in comps:
    #     return {
    #         "ok": False,
    #         "datos": "No se especificaron las fechas para consultar. Dile al usuario que te mencione las fechas que desea consultar."
    #     }

    # — 5.1 Filtrar edificios
    if 'edificio' in comps:
        ed = next((b for b in data if norm(b['nombre']) == comps['edificio']), None)
        if not ed:
            ed = fuzzy_lookup(comps['edificio'], data)
        if not ed:
            return {"ok": False, "datos": f"Edificio '{comps['edificio']}' no encontrado."}
        edificios = [ed]
    else:
        edificios = data

    # — 5.2 Filtrar pisos (solo si pide piso o ambiente)
    pisos_matches = []
    if 'piso' in comps:
        for b in edificios:
            p = next((p for p in b['pisos'] if norm(p['nombre']) == comps['piso']), None)
            if not p:
                p = fuzzy_lookup(comps['piso'], b['pisos'])
            if p:
                pisos_matches.append({"edificio": b, "piso": p})
        if not pisos_matches:
            return {"ok": False, "datos": f"El piso '{comps['piso']}' solicitado no fue encontrado en el edificio solicitado."}
    else:
        # si no pide piso, tomo todos los pisos de los edificios filtrados
        for b in edificios:
            for p in b['pisos']:
                pisos_matches.append({"edificio": b, "piso": p})

    # — 5.3 Filtrar ambientes (solo si pide ambiente)
    results = []
    if 'ambiente' in comps:
        for item in pisos_matches:
            b, p = item['edificio'], item['piso']
            a = next((a for a in p['ambientes'] if norm(a['nombre']) == comps['ambiente']), None)
            if not a:
                a = fuzzy_lookup(comps['ambiente'], p['ambientes'])
            if a:
                results.append({
                    "edificio":     {"id": b['id'],   "nombre": b['nombre']},
                    "piso":         {"id": p['id'],   "nombre": p['nombre']},
                    "ambiente":     {"id": a['id'],   "nombre": a['nombre']},
                    "fecha_inicio": comps['fechainicio'] if 'fechainicio' in comps else None,
                    "fecha_fin":    comps['fechafin'] if 'fechafin' in comps else None
                })
        if not results:
            return {"ok": False, "datos": f"El ambiente '{comps['ambiente']}' solicitado no fue encontrado en el piso solicitado."}
    else:
        # si no pide ambiente, retorno cada piso (con su edificio)
        for item in pisos_matches:
            b, p = item['edificio'], item['piso']
            results.append({
                "edificio":     {"id": b['id'],   "nombre": b['nombre']},
                "piso":         {"id": p['id'],   "nombre": p['nombre']},
                "fecha_inicio": comps['fechainicio'] if 'fechainicio' in comps else None,
                "fecha_fin":    comps['fechafin'] if 'fechafin' in comps else None
            })

    return {"ok": True, "datos": results}