import cv2 as cv
from PIL import Image, ImageDraw
import os
from natsort import natsorted
import numpy as np
from scipy.ndimage import label


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


