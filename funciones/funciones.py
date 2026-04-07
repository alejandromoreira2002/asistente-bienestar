from datetime import timedelta, datetime
import pandas as pd
import numpy as np

def generarDF(resultados, f_inicio):
    dias_llm_ordenada, fecha_inicio = completarDias(resultados, pd.to_datetime(f_inicio))

    # === Construir el DataFrame ===
    data = []

    for i, (dia, tipo) in enumerate(dias_llm_ordenada):
        fecha = fecha_inicio + timedelta(days=i)
        data.append({
            'fecha': fecha,
            'feriado': 1 if tipo.lower() == 'feriado' else 0,
            'evento_especial': 1 if tipo.lower() == 'especial' else 0
        })
    
    fechas = pd.date_range(start=data[0]['fecha'], end=data[-1]['fecha'], freq="D")
    col_temp = np.random.uniform(np.float64(19.42430644731337), np.float64(30.47436405875521), len(fechas)).astype(np.float64)
    df = pd.DataFrame({
        'feriado': [item['feriado'] for item in data],
        'evento_especial': [item['evento_especial'] for item in data],
        'total_temperatura': col_temp
    }, index=fechas)
    #df = pd.DataFrame(data)
    #df['fecha'] = pd.to_datetime(df['fecha'])
    # Establecer como índice y asegurar frecuencia diaria
    #df.set_index('fecha', inplace=True)
    
    return df