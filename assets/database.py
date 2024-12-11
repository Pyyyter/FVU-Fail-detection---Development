import pandas as pd
import subprocess

def cria_database(csv_path):
    colunas = ['ID', 'mission_name', 'image_path', 'situation', 'location']
    dataframe = pd.DataFrame(columns=colunas)
    dataframe.to_csv(csv_path, index=False, sep=';')  

def adicionar_ao_database(placa, csv_path):
    dataframe = pd.read_csv(csv_path, sep=';')
    new_index = len(dataframe)
    new_line = {
        'ID': new_index + 1,
        'mission_name': placa.mission_name,
        'image_path': placa.image_path,
        'situation': placa.qualidadeplaca,
        'location': placa.geolocation
    }
    dataframe = pd.concat([dataframe, pd.DataFrame([new_line])], ignore_index=True)
    dataframe.to_csv(csv_path, index=False, sep=';')      
 

def realizar_query(csv_path, comando):
    comando = f'csvsql --query "{comando}" {csv_path}'
    saida = subprocess.run(comando, shell=True, capture_output=True, text=True)
    # print(saida.stdout)
    return saida.stdout

def ler_database(csv_path):
    comando = 'select * from placas'
    saida = realizar_query(csv_path, comando)
    placas = []
    for placa in saida.split('\n'):
        placas.append(placa)
    return placas

def resgatar_missions(csv_path):
    comando = 'select distinct mission_name from placas'
    saida = realizar_query(csv_path, comando)
    missions = []
    for mission in saida.split('\n'):
        missions.append(mission)
    return missions

def resgatar_panels_from_mission(csv_path, mission_name):
    comando =  f"select * from placas where mission_name like '{mission_name}'"
    saida = realizar_query(csv_path, comando)
    return saida