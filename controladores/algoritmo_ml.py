from modelos.algoritmo_ml import AlgoritmoMLModelo
from datetime import timedelta
import re
import pandas as pd
import numpy as np

# Libraries
# ==============================================================================
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

class AlgoritmoMLControlador():
    def __init__(self):
        self.modelo = AlgoritmoMLModelo()
    
    def encontrarHiperparametros(self, df_full, fecha_inicio_eval):
        # Proceso para encontrar los mejores hiperparámetros
        # ==============================================================================
        order = (1, 1, 2) #Podrian cambiarse
        seasonal_order = (1, 1, 1, 14) #Podrian cambiarse

        forecaster = ForecasterSarimax(
            regressor=Sarimax(order=order, seasonal_order=seasonal_order, maxiter=200)
        )

        param_grid = {
            'order': [(1, 1, 1), (1, 1, 2), (2, 1, 2)],
            'seasonal_order': [(1, 1, 1, 14), (1, 1, 0, 14), (0, 1, 1, 14)],
            'trend': [None, 'c']
        }

        cv = TimeSeriesFold(
            steps              = 14,
            initial_train_size = len(df_full.loc[:fecha_inicio_eval, 'total_kilovatio']),
            refit              = False
        )

        results_grid = grid_search_sarimax(
            forecaster            = forecaster,
            y                     = df_full.loc[:, 'total_kilovatio'],
            exog                  = df_full.loc[:, ['feriado', 'evento_especial', 'total_temperatura']],
            param_grid            = param_grid,
            cv                    = cv,
            metric                = 'mean_absolute_error',
            return_best           = True,
            n_jobs                = 'auto',
            suppress_warnings_fit = True,
            verbose               = False,
            show_progress         = True
        )
        # ==============================================================================

        return forecaster, results_grid