import cv2 as cv
from PIL import Image, ImageDraw
import os
from natsort import natsorted
import numpy as np
from scipy.ndimage import label
from math import dist as distancia_euclidiana, radians, cos



def cria_matriz_imagem(placa):
    new_matriz = []
    matriz_imagem = np.asarray(placa.image)
    for i, linha in enumerate(matriz_imagem):
        new_matriz.append([])
        for pixel in linha:
            new_matriz[i].append(pixel[0])
    return np.array(new_matriz)


def count_pixels_brancos(placa, rgb_limite):
    pixels_brancos_e_notBrancos_placas = {}
    imagem = placa.image
    matriz_imagem = np.asarray(imagem)
    branco = 0
    not_branco = 0

    matriz_imagem = np.asarray(imagem)
    for linha in matriz_imagem:
        for pixel in linha:
            if pixel[0] > rgb_limite:
                branco +=1 
            elif pixel[0] <= rgb_limite:
                not_branco += 1
    pixels_brancos_e_notBrancos_placas[placa[:-4]] = [branco, not_branco]
    return pixels_brancos_e_notBrancos_placas

def count_and_pos_hotspot(placa, rgb_limite):

    quant_hotspots = {}
    pos_hotspots = {}
    new_matriz = cria_matriz_imagem(placa)

    matriz_verificadora = new_matriz > rgb_limite
    padrao = np.array([[0, 1, 0],
                    [1, 1, 1],
                    [0, 1, 0]]) 
    labeled_array, clusters = label(matriz_verificadora, structure=padrao)
    quant_hotspots[placa.image_path[:-4]] = clusters


    cluster_info = {}
    for cluster in range(1, clusters + 1):
        cluster_positions = np.argwhere(labeled_array == cluster)
        
        top_left = cluster_positions.min(axis=0)
        bottom_right = cluster_positions.max(axis=0)

        top_left = (top_left[1], top_left[0])
        bottom_right = (bottom_right[1], bottom_right[0])

        
        cluster_info[cluster] = {
            "top_left": tuple(top_left),
            "top_right": (top_left[0], bottom_right[1]),
            "bottom_left": (bottom_right[0], top_left[1]),
            "bottom_right": tuple(bottom_right)
        }
    
    if cluster_info != {} :
        pos_hotspots[placa.image_path[:-4]] = cluster_info
    
    return quant_hotspots, pos_hotspots
        

def bouding_box(placa, pos_hotspots, quant_hotspots):

    tamanhos_bounding_box = {}
    placa = placa.image_path[:-4]

    tamanhos_bounding_box[placa] = {} 
    if quant_hotspots[placa] > 0:
        for i in range(1, len(pos_hotspots[placa])+1):
            tamanhos_bounding_box[placa][i] = {}
            altura = abs(pos_hotspots[placa][i]['top_left'][1] - pos_hotspots[placa][i]['bottom_right'][1])
            largura = abs(pos_hotspots[placa][i]['bottom_right'][0] - pos_hotspots[placa][i]['top_left'][0])

            tamanhos_bounding_box[placa][i]['altura'] = altura
            tamanhos_bounding_box[placa][i]['largura'] = largura
    return tamanhos_bounding_box

#função de extrair metadados do gabriel
def extract_metadata(image):
    """Extrair metadados EXIF da imagem e converter para tipos serializáveis."""
    if image._getexif() is None:
        return {}
    metadata = {}
    for k, v in image._getexif().items():
        tag_name = ExifTags.TAGS.get(k, k)
        try:
            if isinstance(v, (list, tuple)):
                v = [
                    float(x) if hasattr(x, "denominator") and x.denominator != 0 else None
                    for x in v
                ]
            elif hasattr(v, "denominator") and v.denominator != 0:
                v = float(v)
            elif hasattr(v, "denominator") and v.denominator == 0:
                v = None
            metadata[tag_name] = v
        except Exception as e:
            metadata[tag_name] = str(v)  # Converte valores não processáveis para string
    return metadata

#função de converter grau, metro e segundo para decimal
def dms_to_dd(hemisferio, d, m, s):
    dd = d + float(m)/60 + float(s)/3600
    if hemisferio == 'W' or hemisferio == 'S':
        return -dd
    elif hemisferio == 'E' or hemisferio == 'N':
        return dd
    

#calcula o tamanho de 1 pixel da imagem em metros
def calcula_tamanho_1_pixel(altitude, abertura_lente, imagem):
    
    altitude_relativa = altitude
    cos_abertura_lente = cos(radians(abertura_lente/2))

    pixels_horizontal, pixels_vertical = imagem.size
    distancia_drone_margem_imagem = abs(altitude_relativa * cos_abertura_lente)
    distancia_margem_a_margem = 2*distancia_drone_margem_imagem
    pixel_em_metros = distancia_margem_a_margem/pixels_horizontal

    return pixel_em_metros


#distancia do drone até o o centro da placa (no 2d, sem altura), calculado em pixels 
def calcula_distancia_centro_placa(imagem, coordenadas_placa, pixel_em_metros):

    coordenadas_drone = (imagem.size[0]/2, imagem.size[1]/2)
    distancia_centro_placa = distancia_euclidiana(coordenadas_placa, coordenadas_drone)
    distancia_centro_placa_metros = distancia_centro_placa * pixel_em_metros

    return distancia_centro_placa_metros


#converte as coordenadas do centro da imagem de grau, minuto e segundo para decimal e calcula a coordenada da placa  
def calcula_coordenadas_geograficas_placa(hemisferio_latitude, hemisferio_longitude, latitude, longitude, distancia_centro_placa_metros):

    raio_terra = 6378137

    latitude_decimal = dms_to_dd(hemisferio_latitude, latitude[0], latitude[1], latitude[2])
    longitude_decimal = dms_to_dd(hemisferio_longitude, longitude[0], longitude[1], longitude[2])

    variação_latitude = distancia_centro_placa_metros/raio_terra
    variação_longitude = distancia_centro_placa_metros/(raio_terra * cos(latitude_decimal))

    latitude_placa = latitude_decimal + variação_latitude
    longitude_placa = longitude_decimal + variação_longitude

    return latitude_placa, longitude_placa


#Une todas as funções do calculo das coordenadas em uma só
def calcula_coordenadas_geograficas(imagem):
    abertura_lente = 73.7 #do próprio drone 
    metadados = extract_metadata(imagem)
    altitude = metadados['GPSInfo'][6] - 22.3 #referente à altitude (altura do drone a partir do nível do mar)
    pixel_em_metros = calcula_tamanho_1_pixel(altitude, abertura_lente, imagem)


    coordenadas_placa = (611, 182) #deve ser pega no loop da função extract_placas_from_predictions
    distancia_centro_placa_metros = calcula_distancia_centro_placa(imagem, coordenadas_placa, pixel_em_metros)

    hemisferio_latitude = metadados['GPSInfo'][1]
    latitude = metadados['GPSInfo'][2]
    hemisferio_longitude = metadados['GPSInfo'][3]
    longitude = metadados['GPSInfo'][4]

    nova_latitude, nova_longitude = calcula_coordenadas_geograficas_placa(hemisferio_latitude, hemisferio_longitude, latitude, longitude)
    return nova_latitude, nova_longitude
    


