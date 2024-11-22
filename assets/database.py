import pandas as pd
import csvkit  
from placa import Placa
import os
import subprocess

def cria_database(csv_path):
    colunas = ['mission_name', 'image_path', 'situation', 'location']
    dataframe = pd.DataFrame(columns=colunas)
    dataframe.to_csv('placas')

def adicionar_ao_database(placa, csv_path):
    dataframe = pd.read_csv(csv_path)
    size = len(dataframe)
    new_line = {'mission_name': placa.mission_name, 'image_path' : placa.image_path, 'situation' : placa.situation, 'location' : placa.location}
    dataframe.loc[size] = new_line
    dataframe.to_csv('placas.csv')

def realizar_query(csv_path, comando):
    comando = f'csvsql --query "{comando}" {csv_path}'
    saida = subprocess.run(comando, shell=True, capture_output=True, text=True)
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
        print(mission)
        missions.append(mission)
    return missions

def resgatar_panels_from_mission(csv_path, mission_name):
    comando =  f'select * from placas where mission_name = "{mission_name}"'
    saida = realizar_query(csv_path, comando)
    return saida.stdout
    

# comando = 'select * from placas'
# path = 'placas.csv'
# #saida = realizar_query(path, comando)          
# placas = resgatar_missions(path)

