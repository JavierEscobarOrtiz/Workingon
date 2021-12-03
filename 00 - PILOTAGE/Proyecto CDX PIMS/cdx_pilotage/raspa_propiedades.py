import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc_file_defaults
import pyodbc
import seaborn as sns
from pyodbc import ProgrammingError
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Dendograma
from sklearn.preprocessing import normalize
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram
from scipy.cluster.hierarchy import linkage

# FUNCIONES PARA CARGADO DE DATOS DE RASPACRUDOS Y ASSAYS DE GLOBAL MODEL ==========================================

def cargar_raspacrudos(excel, hoja, print_returns=True):
    """
    Load Raspa Crudos PILOTAGE and create df
    
    :param excel: Ruta completa excel "Raspa Crudos PILOTAGE.xlsm"
    :param hoja: Hoja con los datos dentro del excel: "CRUDOS"
    :param print_returns: print or not function's returns
    :ptype: boolean

    :return df with raspa crudos
    :rtype: pandas dataframe
    """
    df_raspa = pd.read_excel(excel, sheet_name = hoja, header = 1)

    for col in list(df_raspa.columns):
        if df_raspa[col].notnull().sum() == 0:
            df_raspa.drop([col], axis=1, inplace=True)

    df_raspa["Fecha 1"] = pd.to_datetime(df_raspa["Fecha Desc."], format='%Y-%m-%d %H:%M:%S', errors = "coerce")
    df_raspa["Fecha 2"] = pd.to_datetime(df_raspa["Fecha Desc."], format='%d/%m/%Y', errors = "coerce") 
    df_raspa["Fecha Desc."] = df_raspa["Fecha 1"].combine_first(df_raspa["Fecha 2"])
    df_raspa.drop(['Fecha 1', 'Fecha 2'], axis = 1, inplace = True)
    
    # Rename some crudes
    df_raspa = df_raspa.replace({'Crudo': "Arabia"}, "Arabia Ligero")
    df_raspa = df_raspa.replace({'Crudo': "Arabia ligero"}, "Arabia Ligero")
    df_raspa = df_raspa.replace({'Crudo': "QUA IBOE"}, "Qua iboe")
    df_raspa = df_raspa.replace({'Crudo': "West Texas Cactus"}, "TI CACTUS")
    df_raspa = df_raspa.replace({'Crudo': "WTL"}, "TL 48.6")
    df_raspa = df_raspa.replace({'Crudo': "WTI Light"}, "TL 48.6")
    df_raspa = df_raspa.replace({'Crudo': "Azeri"}, "Azeri CIC 2020")

    if print_returns:
        pd.set_option('display.max_columns', None)
        print("Cargado df con la información de las compras de crudo por parte de PILOTAGE:")
        print(df_raspa.shape)
        display(df_raspa.head(3))
        print("=====================================")
        pd.reset_option('display.max_columns')

    return df_raspa



def crudos_destilados(df, refineria="RGSR", desde="1900-01-01", hasta="2099-01-01", top=15, plot_returns=True, print_returns=True):
    """
    Plot distillates crudes from Raspa Crudos PILOTAGE and create df
    
    :param df: df_raspa from func cargar_raspacrudos
    :ptype: pandas dataframe
    :param refineria: final_columns_to_plot from concat_pt_plot_and_columns_plot
    :ptype: str
    :param desde: Initial date
    :ptype: str
    :param hasta: Final date
    :ptype: str 
    :param top: top values to plot
    :ptype: int 
    :param plot_returns: plot or not function's returns
    :ptype: boolean
    :param print_returns: print or not function's returns
    :ptype: boolean

    :return plot: df sorted with distillation data
    :rtype: pandas dataframe
    """
    df_aux = df[(df["Fecha Desc."] >= desde) & (df["Fecha Desc."] <= hasta)]
    df_aux = df_aux[df_aux["Refinería"] == refineria]
    df_aux = pd.DataFrame(df_aux.groupby(["Refinería", "Crudo"])["Cantidad"].sum()).sort_values(by="Cantidad", ascending = False)
    df_aux = df_aux.round(0)

    # Bar plot results
    desde = datetime.strptime(desde, '%Y-%m-%d').strftime('%b-%y')
    hasta = datetime.strptime(hasta, '%Y-%m-%d').strftime('%b-%y')

    df_plot = df_aux.reset_index().sort_values(by = "Cantidad").tail(top)

    if plot_returns:
        fig, ax = plt.subplots(figsize = (14, 8), constrained_layout = True)
        ax.barh(df_plot.Crudo, df_plot.Cantidad,  color = "#E54F44")
        ax.set_title(f"Top {top} crudos Destilados en {refineria}, periodo: {desde} -- {hasta}", fontsize = 20, fontweight = 'bold')
        ax.set_ylabel("Crudo", fontsize = 18, fontweight = 'bold')
        ax.set_xlabel("Destilación (t)", fontsize = 18, fontweight = 'bold')
        ax.tick_params(axis="both", labelsize = 15)
        ax.bar_label(ax.containers[0], fmt='%.0f', padding = 3, fontsize = 15)
        plt.show();

    if print_returns:
        pd.set_option('display.max_columns', None)
        print("=====================================")
        print("Dataframe returned Head(4):")
        display(df_aux.head(4))
        pd.reset_option('display.max_columns')

    return df_aux



def col_to_bool(df, cols_crudos, print_returns=True):
    """
    Create boolean columns of crude activity, value > 0 == 1 else 0
    
    :param df: dataframe from func pims_functions.pivot_table_submodel_agrupacion
    :ptype: pandas dataframe
    :param cols_crudos: Columns of crudes in df
    :ptype: list
    :param print_returns: print or not function's returns
    :ptype: boolean

    :return df: df with boolean info
    :rtype: pandas dataframe
    :return list_bool_cols: Boolean columns of crudes in df
    :rtype: list
    """
    list_bool_cols = []

    for col in cols_crudos:
        df[f'{col}_bool'] = df[col].apply(lambda x: 0 if x==0 else 1)
        list_bool_cols.append(f'{col}_bool')

    if print_returns:
        pd.set_option('display.max_columns', None)
        print("Creadas columnas_bool en dataframe:")
        display(df.head(3))
        print("=====================================")
        print("Principio lista creada con columnas_bool: ", list_bool_cols[:5], "...")
        pd.reset_option('display.max_columns')

    return df, list_bool_cols



def agrup_by_cols_combination(df, list_bool_cols, count="CaseID", print_returns=True):
    """
    Group same crude combinations
    
    :param df: dataframe from func col_to_bool
    :ptype: pandas dataframe
    :param list_bool_cols: list from func col_to_bool
    :ptype: list
    :param count: columns to aggregate in a list
    :ptype: str
    :param print_returns: print or not function's returns
    :ptype: boolean

    :return df_agrup: Grouped df
    :rtype: pandas dataframe
    """
    df_agrup = df.groupby(list_bool_cols)[count].agg(list).reset_index()
    df_agrup[f'Num_{count}'] = df_agrup[count].str.len()
    df_agrup.sort_values(by = f'Num_{count}', ascending = False, inplace = True)
    
    # Crear lista de listas, cada lista son los crudos_bool = 1 por fila
    list_of_lists = []
    for row in range(df_agrup.shape[0]):
        lista = []
        for col in list_bool_cols:
            if df_agrup.iloc[row, df_agrup.columns.get_loc(col)] > 0:
                lista.append(col)
        lista = sorted(lista)
        list_to_append = []

        for l in lista:
            l_new = l.replace("_bool", "")
            list_to_append.append(l_new)
                               
        list_of_lists.append(list_to_append)
    
    # Columna con listas de las Combinaciones de crudos con bool = 1, elimino listas de un solo crudo
    df_agrup['Crudos_Comb'] = list_of_lists
    df_agrup = df_agrup[df_agrup["Crudos_Comb"].str.len() > 1]

    if print_returns:
        pd.set_option('display.max_columns', None)
        print("Shape de la agrupación de las columnas_bool: ", df_agrup.shape)
        print("Se realiza el conteo sobre: ", count)
        display(df_agrup.head(3))
        pd.reset_option('display.max_columns')
    
    return df_agrup



def cargar_excel_assays_crudos(excel, hoja, print_returns=True):
    """
    Load Raspa Crudos PILOTAGE and create df
    
    :param excel: excel crudes properties
    :param hoja: Sheet excel crudes properties
    :param print_returns: print or not function's returns
    :ptype: boolean

    :return df_assays: df with unqiue cases/versions
    :rtype: pandas dataframe
    """
    df_assays = pd.read_excel(excel, sheet_name = hoja, header = 6)

    for col in list(df_assays.columns):
        if df_assays[col].notnull().sum() == 0:
            df_assays.drop([col], axis=1, inplace=True)

    df_assays = df_assays[df_assays["TEXT"].notnull()]

    if print_returns:
        pd.set_option('display.max_columns', None)
        print("Cargado df assays:", df_assays.shape)
        display(df_assays.head(6))
        print("=====================================")
        pd.reset_option('display.max_columns')
    
    return df_assays



def formato_excel_assays_crudos(df_assays,
                                tags_crudos = ['ABO', 'AGB', 'AJE', 'AKP', 'AMB', 'ATA', 'AZE', 'BAU', 'BGA', 'BOL', 'BON','BUZ', 'CAE', 'CEP', 'CJB', 'E44', 'E46', 'EGI', 'ERH', 'ESC', 'ESH', 'FOR','GUL', 'IRA', 'JON', 'LIV', 'LOK', 'MEL', 'MRO', 'NKO', 'NOD', 'OBE', 'OKO', 'OKR', 'OKW', 'OTA', 'PEN', 'QAR', 'QUI', 'SAB', 'SAP', 'SKF', 'SUR', 'TIE', 'TIP', 'TRO', 'WML', 'WTC', 'WTL', 'YOH', 'ZAB'],
                                properties_columns = ["TEXT", "Name", "Reference", "API", "Den@15°C(g/cc)", "Sul(%w)","Overhead", "OH/KNA Swing", "Kero Naphtha", "Kerosene","KE/GL Swing","Light Gasoil","LGL/GP Swing","Atmospheric Gasoil","Atmospheric Residue"],
                                print_returns = True):
    """
    Transform df_assays from cargar_excel_assays_crudos
    
    :param df_assays: dataframe from func cargar_excel_assays_crudos
    :ptype: pandas dataframe
    :param tags_crudos: chosen crude list
    :ptype: list
    :param properties_columns: chosen property list
    :ptype: list
    :param print_returns: print or not function's returns
    :ptype: boolean

    :return index_info: index values (crudes)
    :rtype: pandas series
    :return df_floats: df of numeric_cols
    :rtype: pandas dataframe
    :return numeric_cols: numeric columns
    :rtype: list
    :return df: complet dataframe
    :rtype: pandas dataframe
    """
    df = df_assays[["TEXT"] + tags_crudos]
    df = df.transpose().reset_index()
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])
    df = df[properties_columns]
    df = df.T.reset_index().drop_duplicates(subset = 0, keep = "first").T
    df.columns = df.iloc[0]
    df = df.drop(df_assays.index[0])
    
    numeric_cols = df.columns.tolist()
    numeric_cols.remove("TEXT")
    numeric_cols.remove("Name")
    numeric_cols.remove("Reference")

    index_info = df["TEXT"]
    df_floats = df[numeric_cols].apply(pd.to_numeric)

    if print_returns:
        pd.set_option('display.max_columns', None)
        display(df.head(3))
        pd.reset_option('display.max_columns')
    
    return index_info, df_floats, numeric_cols, df

