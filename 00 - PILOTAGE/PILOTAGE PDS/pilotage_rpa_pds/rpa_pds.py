import time
import pandas as pd
import pyautogui
import os

pyautogui.PAUSE = 0.1 # Pausa entre acciones (defecto 0.1)
pyautogui.FAILSAFE = True # Detiene el codigo si te vas a la esquina de arriba a la izquierda


# ================================= Crear dataframe de acciones ==================================
# ================================================================================================

# Valores por defecto:
num_of_clicks = 1
secs_between_clicks = 1
secs_between_keys = 0
click_button = "left"
sleep_tras_accion = 2
escribir = "0"
drag_seconds = 0.5
drag_button = "left"
confidence = 0.8
grayscale = False

def cargar_acciones(directorio, ruta_jupyter, accion, input_pmv=None, dict_actions=None):
    """
    Create dataframe with parameters of each action
    
    :param directorio: directory where images are
    :ptype: string
    :param ruta_jupyter: path from jupyter notebook
    :ptype: string
    :param accion: title of the action
    :ptype: string
    :param input_pmv: select periods in column "pasos".
    :ptype: dict
            {key: "image"} 
            {"pmv": "07_pmv_11"}
    :param dict_actions: list of index where you want to execute the actions in keys
    :ptype: dict of lists of tuples
            {"press_button": [(8, "enter"), (8, ["ctrl", "c"])], # index and button (str) or hotkey (list)
            "press_before": [(8, True)], # index and True or False
            "press_after": [(8, True)], # index and True or False
            "scroll": [(8, True)], # index and True or False
            "can_skip": [(1, True)], # index and True or False
            "escribir": [(6, "JESCOBARO"), (7, "Javier987")], # index and str
            "click_button": [(1, "left")], # index and button
            "n_clicks": [(1, 2)], # index and int
            "sleep": [(1, 20)], # index and int
            "drag": [(1, True)], # index and True or False
            "drag_to_x": [(1, 2559)], # index and int
            "drag_to_y": [(1, 771)], # index and int
            "drag_seconds": [(1, 0.5)], # index and float
            "drag_button": [(1, "left")] # index and button
            "go_to_location": [(1, True)], # index and True or False
            "loc_x": [(1, 2559)], # index and int
            "loc_y": [(1, 771)] # index and int
            "confidence": [(1, 0.95)] # index and float (0 - 1)
            "grayscale": [(1, True)] # index and True or False
            }

    :return df with parameters needed for actions
    :rtype: pandas dataframe
    """
    # Obtener imagenes (no capatura carpetas)
    with os.scandir(directorio) as ficheros:
        contenido = [fichero.name for fichero in ficheros if fichero.is_file()]
    
    pasos = [imagen.replace(r".PNG", "").replace(r".png", "") for imagen in contenido]
    rutas = [ruta_jupyter + imagen for imagen in contenido]
    
    # Crear columnas por defecto
    df = pd.DataFrame()
    df["pasos"] = pasos
    df["ruta_jupyter"] = rutas
    df.insert(0, 'accion', accion)
    df["press_button"] = "0"
    df["press_after"] = False
    df["press_before"] = False
    df["scroll"] = False
    df["can_skip"] = False
    df["escribir"] = escribir
    df["click_button"] = click_button
    df["n_clicks"] = num_of_clicks
    df["sleep"] = sleep_tras_accion
    df["s_btw_clicks"] = secs_between_clicks
    df["s_btw_keys"] = secs_between_keys
    df["drag"] = False
    df["drag_to_x"] = 0
    df["drag_to_y"] = 0
    df["drag_seconds"] = drag_seconds
    df["drag_button"] = drag_button
    df["go_to_location"] = False
    df["loc_x"] = 0
    df["loc_y"] = 0
    df["confidence"] = confidence
    df["grayscale"] = grayscale
    
    # Seleccionar valores elegidos en el dict input_pmv
    if input_pmv is not None:
        for key in input_pmv:
            iden = input_pmv[key][:2] # Accedo al numero de paso
            selec = input_pmv[key] # Valor que quiero
            df_aux = df[df["pasos"] == selec]
            df = df[df["pasos"].str[:2] != iden]
            df = pd.concat([df, df_aux])

    df["ordenar"] = df["pasos"].str[:2].astype(int)
    df = df.sort_values(by="ordenar", ascending = True).drop(columns = ['ordenar']).reset_index(drop = True)
    
    # Introducir parametros en dataframe de dict_actions
    if dict_actions is not None:
        for key in dict_actions: 
            for elemento in dict_actions[key]:
                fila = elemento[0]
                df.at[fila, key] = elemento[1]

    return df


# ==================================== Funciones enter y tab =====================================
# ================================================================================================

def press_button(df, sleep = 1):
    """
    Press button
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    :param sleep: seconds to sleep after press
    :ptype: int
    """
    boton = df['press_button'].values[0]
    pyautogui.press(boton)
    time.sleep(sleep)

def press_hotkey(df, sleep = 1):
    """
    Press hotkey
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    :param sleep: seconds to sleep after press
    :ptype: int
    """
    botones = df['press_button'].values[0]
    if len(botones) == 2:
        pyautogui.hotkey(botones[0], botones[1])
    else:
        pyautogui.hotkey(botones[0], botones[1], botones[2])     
        
    time.sleep(sleep)

def press_button_before(df):
    """
    Execute press_button() before action
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    """
    if df['press_before'].values[0] == True:
        # Si es una lista hotkey si no press button
        if isinstance(df['press_button'].values[0], list) == True:
            press_hotkey(df)
        else:
            press_button(df)

def press_button_after(df):
    """
    Execute press_button() after action
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe

    :return pulsado: if press_button() was executed or not
    :rtype: boolean
    """
    pulsado = False
    if df['press_after'].values[0] == True:
        # Si es una lista hotkey si no press button
        if isinstance(df['press_button'].values[0], list) == True:
            press_hotkey(df)
        else:
            press_button(df)

        pulsado = True
        
    return pulsado


# =============================== Mouse and Keyboard functions ===================================
# ================================================================================================

def click_mouse(df, localizacion):
    """
    move to location and then click
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    :param localizacion: coordenates of image, result of pyautogui.locateCenterOnScreen() or from df
    :ptype: pyscreeze.Point

    :return resultado: if image was clicked or not
    :rtype: boolean
    """
    paso = df['pasos'].values[0]

    if localizacion is not None:
        moveToX = localizacion[0]
        moveToY = localizacion[1]
        pyautogui.click(x=moveToX, y=moveToY, clicks=df['n_clicks'].values[0], 
                        interval=df['s_btw_clicks'].values[0], 
                        button=df['click_button'].values[0])
        
        resultado = True
        print(paso, resultado)
    else:
        resultado = False
        print(paso, resultado)
        
    return resultado

def drag_mouse(df, localizacion):
    """
    move to location and then drag
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    :param localizacion: coordenates of image, result of pyautogui.locateCenterOnScreen() or from df
    :ptype: pyscreeze.Point

    :return resultado: if image was draged or not
    :rtype: boolean
    """
    paso = df['pasos'].values[0]

    if localizacion is not None:

        moveToX = localizacion[0]
        moveToY = localizacion[1]
        pyautogui.moveTo(moveToX, moveToY)

        drag_to_x = df['drag_to_x'].values[0]
        drag_to_y = df['drag_to_y'].values[0]
        drag_seconds = df['drag_seconds'].values[0]
        drag_button = df['drag_button'].values[0]

        pyautogui.dragTo(drag_to_x, drag_to_y, drag_seconds, button = drag_button)
        
        resultado = True
        print(paso, resultado)
    else:
        resultado = False
        print(paso, resultado)
        
    return resultado
 
def search_scroll_click(df, scroll = 500, saltos = 5, sleep = 2):
    """
    Search an image scrolling the page and then click
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    :param scroll: clicks to vertical scroll (up positive, down negative)
    :ptype: int
    :param saltos: times to try loop scroll/search
    :ptype: int
    :param sleep: time to sleep before search
    :ptype: int

    :return pulsado: if image was clicked or not, from click_mouse()
    :rtype: boolean
    """
    n = 0
    while n < saltos + 1:
        n += 1
        if n == 1:
            pyautogui.scroll(-100000000) # Si es la primera vez me voy abajo del todo
        else:
            pyautogui.scroll(scroll)   
            
        time.sleep(sleep)
        localizacion = pyautogui.locateCenterOnScreen(df['ruta_jupyter'].values[0], 
                                                      confidence = df['confidence'].values[0], 
                                                      grayscale = df['grayscale'].values[0])
        resultado = click_mouse(df, localizacion)
        if resultado == True:
            break
        else:
            print("Scrolling...")
        
    return resultado

def write_something(df):
    """
    Write the text of df column "escribir"
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    """
    pyautogui.write(df['escribir'].values[0], interval = df['s_btw_keys'].values[0])


# ===================================== Execute actions ==========================================
# ================================================================================================

def ejecutar_rpa(df, scroll=500, saltos=5, sleep=2):
    """
    Execute rpa from a dataframe
    
    :param df: dataframe from cargar_acciones()
    :ptype: pandas dataframe
    :param confidence: accuracy with which the function should locate the image on screen (0 - 1)
    :ptype: float
    :param grayscale: if True it gives a slight speedup to locateCenterOnScreen() (about 30%-ish)
    :ptype: boolen
    :param scroll: clicks to vertical scroll (up positive, down negative), to search_scroll_click()
    :ptype: int
    :param saltos: times to try loop scroll/search, to search_scroll_click()
    :ptype: int
    :param sleep: time to sleep before search, to search_scroll_click()
    :ptype: int
    """
    pasos = df.pasos.to_list()
    start_time = time.localtime()
    start_time_total = time.time()

    print("Ejecutando acción", df.loc[0, "accion"])
    print("Start time:", time.strftime("%d-%m-%Y %H:%M:%S", start_time))
    print("====================================")

    for paso in pasos:

        df_aux = df[df["pasos"] == paso]

        # Press button before
        press_button_before(df_aux)
        
        # Get location
        if df_aux['go_to_location'].values[0] == True:
            localizacion = (df_aux['loc_x'].values[0], df_aux['loc_y'].values[0])
        else:
            localizacion = pyautogui.locateCenterOnScreen(df_aux['ruta_jupyter'].values[0], 
                                                          confidence = df_aux['confidence'].values[0], 
                                                          grayscale = df_aux['grayscale'].values[0])
        
        # Drag or click
        if df_aux['drag'].values[0] == True:
            # Se realiza un drag
            resultado = drag_mouse(df_aux, localizacion)
        else:
            # Se realiza un click
            resultado = click_mouse(df_aux, localizacion)
        
        # Scroll
        if (resultado == False) and (df_aux['scroll'].values[0] == True):
            print("Scrolling...")
            resultado = search_scroll_click(df = df_aux, scroll = scroll, 
                                            saltos = saltos, sleep = sleep)
        
        # Can skip or not
        if (resultado == False) and (df_aux['can_skip'].values[0] == False):
            print("break at", paso, "!!!")
            break
        elif (resultado == False) and (df_aux['can_skip'].values[0] == True):
            print("Error en el paso:", paso, "no se ejecuta")
        
        # Write something    
        if df_aux['escribir'].values[0] != "0":
            time.sleep(1)
            write_something(df_aux)
        
        # Press button after
        press_button_after(df_aux)

        # Sleep
        if df_aux['sleep'].values[0] > sleep_tras_accion:
            print("Sleeping", df_aux['sleep'].values[0], "seconds...")

        time.sleep(df_aux['sleep'].values[0])
    
    end_time = time.localtime()
    end_time_total = time.time()
    total_time = end_time_total - start_time_total

    print("====================================")
    print("Total time action:", time.strftime("%H:%M:%S", time.gmtime(total_time))) 
    print("End time:", time.strftime("%d-%m-%Y %H:%M:%S", end_time))
    print("====================================")
      