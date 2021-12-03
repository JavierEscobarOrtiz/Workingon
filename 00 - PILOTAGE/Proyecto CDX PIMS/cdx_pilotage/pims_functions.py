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

# FUNCIONES PARA CARGADO DE DATOS ===========================================================

def cargar_excel_crudos(excel, hoja):
    """
    Load crude Model Support excel and create df
    
    :param excel: rute excel crudes properties
    :param hoja: Sheet excel crudes properties
    :return df with unqiue cases/versions
    :rtype: pandas dataframe
    """
    df_crudos = pd.read_excel(excel, sheet_name=hoja, header=11)

    for col in list(df_crudos.columns):
        if df_crudos[col].notnull().sum() == 0:
            df_crudos.drop([col], axis=1, inplace=True)

    df_crudos = df_crudos[["TAG", "NAME", "PIMS", "Sin mermas",
                            "API", "%S", "BTM", "Familia + IMO",
                            "country", "region", "% S FV 550+",
                            "% FV 550+"]]
    df_crudos = df_crudos[df_crudos["Familia + IMO"].notnull()]
    df_crudos = df_crudos[df_crudos["Sin mermas"].notnull()]

    pd.set_option('display.max_columns', None)
    print("Cargado df crudos:")
    print(df_crudos.shape)
    display(df_crudos.head(3))
    display(df_crudos.tail(3))
    print("=====================================")
    pd.reset_option('display.max_columns')
    
    return df_crudos



def cargar_access(archivo, tabla):
    """
    Open an access file, choose a table and convert to a dataframe
    
    :param archivo: access to read 
    :param tabla: table of access to convert

    :return df with access table
    :rtype: pandas dataframe
    """
    class CursorByName():
        def __init__(self, cursor):
            self._cursor = cursor

        def __iter__(self):
            return self

        def __next__(self):
            row = self._cursor.__next__()

            return { description[0]: row[col] for col, description in enumerate(self._cursor.description) }

    connection = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + archivo + ";"
    print(connection)
    conn = pyodbc.connect(connection)
    print(conn)
    cursor = conn.cursor()
    print("Connected to:", tabla)
    try:
        cursor.execute('SELECT * FROM {}'.format(tabla))
        x = (cursor.description)

        df = pd.DataFrame(CursorByName(cursor))

        if tabla == "RW_PrimalColumn":
            cadena = archivo.split("\\")[-1]
            df["Mes"] = cadena.split("-")[0]
            df["Version"] = cadena.split("-")[-1].split("_Results")[0]

        display(df.head(3))
        print("Cargada tabla [" + tabla + "] del access: " + archivo)
        print("=====================================\n")  
    except ProgrammingError:
        print("\n=====================================")
        print("El archivo [" + archivo + "] no contiene la tabla [" + tabla + "]")
        print("\n=====================================")
        # Si no existe la tabla se genera un df vacio
        df = pd.DataFrame()
    
    conn.close()
    
    return df



def formato_dfs_access(df_primalcolumn, df_prsolution, df_prcase):
    """
    Modife some dataframes from access
    
    :param df_primalcolumn: dataframe from RW_PrimalColumn
    :ptype: pandas dataframe 
    :param df_prsolution: dataframe from PrSolution 
    :ptype: pandas dataframe
    :param df_prcase: dataframe from PrCase 
    :ptype: pandas dataframe

    :return df with access table
    :rtype: pandas dataframe
    """
    if df_primalcolumn.empty or df_prsolution.empty or df_prcase.empty:
        # Si el df esta empty me salto la funcion
        df_primal = df_primalcolumn
        df_sol = df_prsolution
        df_case = df_prcase
    else:
        # Filtrado de columnas
        # ================================================================================

        df_primal = df_primalcolumn.copy()
        df_primal = df_primal[["Mes", "Version", "SolutionID", "CaseID", "ColumnName", "Activity"]]

        # Submodelo, 4 letras
        df_primal["Submodel"] = df_primal["ColumnName"].str[0:4]
        #print(df_prueba["Submodel"].unique())

        # Crudo
        df_primal["Crudo"] = df_primal["ColumnName"].str[-4:-1]
        #print(df_prueba["Crudo"].unique())

        # Refineria, ultima letra A y H
        df_primal["Refineria"] = df_primal["ColumnName"].str[-1:]
        #print(df_prueba["Refineria"].unique())

        # Filtro por Algeciras y Huelva
        df_primal = df_primal[df_primal["Refineria"].isin(["A", "H"])]

        # Algeciras submodels Crudo 1, Crudo 3 y C1 Lubes, C3 Lubes
        submodelos_algeciras = ["SCD1", "SCD2", "SCD3", "SCD4", 
                                "SCDa", "SCDb", "SCDc", "SCDd",
                               "SCDy", "SCDi"]

        # Huelva submodels Crudo 1, Crudo 2 y C1 Asfaltos, C2 Asfaltos
        submodelos_huelva = ["CD1", "CD2", "CD3", 
                             "CDa", "CDb", "CDc",
                             "CD5", "CDe"]

        df_primal = df_primal.loc[df_primal["Submodel"].isin(submodelos_algeciras)]

        # ================================================================================
        # ================================================================================

        df_sol = df_prsolution.copy()
        df_sol = df_sol[["SolutionID", "DateTime", "ModelID"]]

        # Fecha
        df_sol["DateTime"] = pd.to_datetime(df_sol["DateTime"], format='%Y%m%d %H%M%S')

        # ================================================================================
        # ================================================================================

        df_case = df_prcase.copy()
        df_case = df_case[["SolutionID", "CaseID", "Description", "ObjectiveFunction", "TotalTime"]]

        # ================================================================================

        print("Formateando dfs =====================================")
        display(df_primal.head(3))
        display(df_sol.head(3))
        display(df_case.head(3))
        print("Dfs formateados =====================================\n")
    
    return df_primal, df_sol, df_case



def merge_primal_solution_case_crudos(df_primal, df_sol, df_case, df_crudos, ruta_csv):
    """
    Merge all inputed dfs and generate a csv
    
    :param df_primal: dataframe after function formato_dfs_access from RW_PrimalColumn 
    :ptype: pandas dataframe
    :param df_sol: dataframe after function formato_dfs_access from PrSolution 
    :ptype: pandas dataframe
    :param df_case: dataframe after function formato_dfs_access from PrCase 
    :ptype: pandas dataframe
    :param df_crudos: dataframe returned from function cargado_excel_crudos 
    :ptype: pandas dataframe
    :param ruta_csv: dataframe returned from function cargado_excel_crudos
    :ptype: str

    :return dataframe merged
    :rtype: pandas dataframe
    """
    if df_primal.empty or df_sol.empty or df_case.empty:
        print("\n=====================================")
        print("No se carga el fichero, alguna de las tablas del access está vacía")
        print("\n=====================================")
    else:
        df_merge = df_primal.merge(df_sol, how="left", on = "SolutionID")

        # Merge con PrCase

        df_merge["Solution_Case"] = df_merge["SolutionID"].astype(str) + "_" + df_merge["CaseID"].astype(str)
        df_case["Solution_Case"] = df_case["SolutionID"].astype(str) + "_" + df_case["CaseID"].astype(str)

        df_merge = df_merge.merge(df_case, how="left", on = "Solution_Case")

        # Merge con info crudos

        df_merge = df_merge.merge(df_crudos, how="left", left_on = "Crudo", right_on = "PIMS")
        df_merge = df_merge[df_merge["NAME"].notnull()]

        # Drop y rename
        drop_columns = ["SolutionID_y", "CaseID_y"]
        df_merge = df_merge.drop(columns=drop_columns)
        df_merge = df_merge.rename(columns={"SolutionID_x": "SolutionID", "CaseID_x": "CaseID"})

        print("Merge completado, guardando csv")
        pd.set_option('display.max_columns', None)
        display(df_merge.shape)
        display(df_merge.dtypes)
        display(df_merge.head(3))
        pd.reset_option('display.max_columns')

        df_merge.to_csv(ruta_csv, index=False)
        print("csv guardado " + ruta_csv + " =====================================")

        return df_merge

# ==================================================================================================
# PLOT =============================================================================================

def cases_uniques(df):
    """
    Return unique cases from a dataframe merged
    
    :param df: dataframe merge with all cases
    :ptype: pandas dataframe

    :return df with unqiue cases/versions
    :rtype: pandas dataframe
    """
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

    df_aux = df.drop_duplicates(subset=["Mes", "Version", 'CaseID'])[["Mes", "Version", "CaseID", "Description"]]
    df_aux["len"] = df_aux["Description"].str.len()
    df_aux["ordenar"] = df_aux["Version"].str[:10]
    df_aux["ordenar"] =  pd.to_datetime(df_aux["ordenar"], format= '%Y_%m_%d', errors = "coerce")       
    df_aux = df_aux.sort_values(by=["len", "Mes", "ordenar"], ascending = True)
    print("Número de casos disponibles: ", df_aux.shape[0])
    display(df_aux)

    pd.reset_option('display.max_columns')
    pd.reset_option('display.max_rows')

    return df_aux



def pivot_table_submodel_agrupacion(df_origen, submodel, agrupacion, print_returns=True):
    """
    Generate pivot table to concrete submodel from df_merge filtered
    
    :param df_origen: df_merge filtered
    :ptype: pandas dataframe
    :param submodel: selected submodel
    :ptype: str
    :param agrupacion: variable to agrupate (Crudo, Familia + IMO)
    :ptype: str
    :param print_returns: print or not resume of function's returns
    :ptype: boolean

    :return pivot table
    :rtype: pandas dataframe
    """
    # Generamos pivot table
    table = df_origen[df_origen["Submodel"] == submodel]
    table = pd.pivot_table(table, values = 'Activity', index = ["Description", 'Version', 'CaseID', 'Submodel'],
                           columns = agrupacion, aggfunc = np.sum)
    table = table.fillna(0.0)
    table = table.sort_index(axis = 1).reset_index()

    # Ordenar por Mes y Version
    table["Month_order"] = table["Description"].str[:3] + "-" + table["Description"].str[3:5]
    table["Month_order"] = pd.to_datetime(table["Month_order"], format= '%b-%y', errors = "coerce")

    table["Version_order"] = table["Version"].str[:10]
    table["Version_order"] =  pd.to_datetime(table["Version_order"], format= '%Y_%m_%d', errors = "coerce")

    table = table.sort_values(by = ["Month_order", "Version_order"], ascending = True)

    if print_returns:
        pd.set_option('display.max_columns', None)
        print("\nPivot table de Submodel " + submodel + " agrupado por " + agrupacion)
        display(table.head(3))
        print("\nCasos disponibles: ", list(table.CaseID.unique()))
        print("\nDescriptions disponibles: ", list(table.Description.unique()))
        pd.reset_option('display.max_columns')

    return table



def concat_pt_plot_and_columns_plot(dfs, descriptions, print_returns=True):
    """
    Merge dfs to plot and find columns with activity > 0
    
    :param dfs: dataframes to concat
    :ptype: list of pandas dataframes
    :param descriptions: dataframe Description want to plot
    :ptype: list of str
    :param print_returns: print or not function's returns
    :ptype: boolean

    :return df_plot: concated df filter for descriptions
    :rtype: pandas dataframe
    :return final_columns_to_plot: df_plot cols list where col.sum() != 0
    :rtype: list
    """
    df_plot = pd.concat(dfs, ignore_index = True)
    df_plot = df_plot.fillna(0.0)
    
    # Filtrar por lista descriptions
    df_plot = df_plot.reset_index(drop = True)
    df_plot = df_plot[df_plot.Description.isin(descriptions)]
    
    # Eliminar columnas que no quiero plotear y columnas cuya sum activity = 0
    columns = list(df_plot.columns)
    default_to_remove = ["Description", "Version", "CaseID", "Submodel", "Month_order", "Version_order"]
    final_columns_to_plot = columns.copy()
    for col in columns:
        if col in default_to_remove:
            final_columns_to_plot.remove(col)

    sum_zero = []
    for col in final_columns_to_plot:
        if df_plot[col].sum() == 0:
            sum_zero.append(col)

    for col in columns:
        if col in sum_zero:
            final_columns_to_plot.remove(col)
    
    # Columnas support para los graficos
    df_plot["Total_activity"] = df_plot[final_columns_to_plot].sum(axis=1)
    df_plot["Axis"] = df_plot["Description"] + "-" + df_plot["Version"]
    df_plot["bottom"] = 0

    if print_returns:
        pd.set_option('display.max_columns', None)
        print("df_plot Head:")
        display(df_plot.head(2))
        print("df_plot Tail:")
        display(df_plot.tail(2))
        print("Columnas con Suma de Activity > 0 (columns to plot): " + str(final_columns_to_plot))
        pd.reset_option('display.max_columns')

    return df_plot, final_columns_to_plot



def plot_2_pivot_tables_refinery(df_plot, final_columns_to_plot, description, min_activity=0):
    """
    Plot bar chart from result of function: concat_pt_plot_and_columns_plot.
    
    :param df_plot: df_plot from concat_pt_plot_and_columns_plot
    :ptype: pandas dataframe
    :param final_columns_to_plot: final_columns_to_plot from concat_pt_plot_and_columns_plot
    :ptype: list
    :param description: One value of column Description to plot
    :ptype: str
    :param min_activity: columns with sum activity < min_activity will not plot (default 0)
    :ptype: float  

    no variable return, just ploting
    """
    sns.set_theme(style = "whitegrid")
    # lista de colores CEPSA
    colores_cepsa = ["#365472", "#ADCE6D", "#338B93", "#E54F44",
                     "#BF8F00", "#6C6F70", "#AEB0B3", "#79C9D1", 
                     "#D52B1E", "#AAA584", "#CFCFBD", "#801A12", 
                     "#737353", "#8497B0", "#5A7627", "#59563E"]
    
    # One col for each crude unit
    ncols = 2
    nrows = 1
               
    # Submodels
    submodels = df_plot.Submodel.unique()
    
    fig, ax = plt.subplots(nrows = nrows, ncols = ncols, figsize = (16, 7), sharey = True, constrained_layout = True)
    
    for i, submodel in zip(range(ncols), submodels):
        
        # Filtro por submodel y creo el df con la actividad total de cada version
        df_aux = df_plot[df_plot["Description"] == description]
        df_aux = df_aux[df_aux["Submodel"] == submodel]
        df_line = df_aux[["Axis", "Total_activity"]]
        
        # Cambio valores menores a min_activity por 0
        for col in final_columns_to_plot:
            a = np.array(df_aux[col].values.tolist())
            df_aux[col] = np.where(a < min_activity, 0, a).tolist()
        
        # Plot de cada columna en barras con su bottom
        c = 0
        for col in final_columns_to_plot:
            if df_aux[col].sum() > 0:
                ax[i].bar(df_aux.Axis, df_aux[col], label = col, bottom = df_aux["bottom"], color = colores_cepsa[c])
                df_aux["bottom"] = df_aux["bottom"] + df_aux[col]
            c += 1
            if c == len(colores_cepsa):
                c = 0
        
        # Plot linea con actividad total 
        ax[i].plot(df_line["Axis"], df_line["Total_activity"], marker = "o", linestyle = "--", color = "dimgrey", linewidth=3, 
                   label = "total_act")
        
        # Params, label solo en eje Y de la izquierda
        ax[i].set_xticklabels(df_aux.Axis.str[8:], rotation = 70, fontsize = 15)
        ax[i].set_title("Submodel: " + submodel, fontsize = 15, fontweight = "bold")
        ax[0].set_ylabel("Activity (kt)", fontsize = 15)
        ax[i].tick_params(axis="y", labelsize = 15)
        ax[i].legend(bbox_to_anchor=(0, 1.08, 1,0.2), loc="lower left", mode="expand", borderaxespad=0, ncol = 5)
        
    fig.suptitle(description, fontsize = 20, fontweight = "bold")
    plt.show();

    # Reset Matplotlib defaults
    rc_file_defaults()