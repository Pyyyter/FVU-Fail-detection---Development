import os
import csv
import zipfile
from io import BytesIO
from flask import Flask, request, jsonify
from PIL import Image, ExifTags
from PIL.TiffImagePlugin import IFDRational

from ultralytics import YOLO
from assets.auxiliar import count_and_pos_hotspot, bouding_box
from assets.placa import Placa
from assets.database import adicionar_ao_database, realizar_query, ler_database, resgatar_missions, resgatar_panels_from_mission

app = Flask(__name__)

# Classe para carregar e usar o modelo YOLO
class YOLOPredictor:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def predict(self, image):
        return self.model.predict(image)

# Classe para processar imagens usando YOLO e análise de qualidade
class ImageProcessor:
    def __init__(self, model_path):
        self.yolo_predictor = YOLOPredictor(model_path)

    def process_images(self, images, mission_name):
        placa_matrix = []
        for img_data in images:
            image = Image.open(BytesIO(img_data['data']))
            metadata = extract_metadata(image)
            geolocation = metadata.get("GPSInfo")
            image_path = img_data['image_path']
            if geolocation:
                reformatted = {
                    geolocation[1]: geolocation[2],  # Latitude
                    geolocation[3]: geolocation[4]   # Longitude
                }

            # Previsão com YOLO
            results = self.yolo_predictor.predict(image)

            # Processar recortes e obter resultados
            paineis_detectados = self.extract_placas_from_predictions(image, results, reformatted, image_path, mission_name)

            # Adicionar à matriz
            placa_matrix.append([Placa(reformatted, image, image_path).to_dict(), paineis_detectados])

        return placa_matrix, paineis_detectados

    def extract_placas_from_predictions(self, image, results, geolocation, image_path, mission_name):
        recortes = []
        base_name = os.path.splitext(os.path.basename(image_path))[0]  # Nome base da imagem (sem extensão)
        output_dir = "recortes" + mission_name  # Pasta onde os recortes serão salvos

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Loop para cada bounding box detectada
        for idx, box in enumerate(results[0].boxes.xyxy, start=1):
            x1, y1, x2, y2 = map(int, box)
            cropped_img = image.crop((x1, y1, x2, y2))
            
            # Nome do recorte baseado na imagem original
            cropped_name = f"{base_name}_BOX{idx}.jpg"
            cropped_path = os.path.join(output_dir, cropped_name)
            
            # Salvar o recorte
            cropped_img.save(cropped_path)
            
            # Criar um objeto Placa e detectar defeito
            painel = Placa(geolocation=geolocation, image=cropped_img, image_path=cropped_path, mission_name=mission_name)

            detecta_defeito(painel)

            print(painel.to_dict())

            # Adicionar ao database
            adicionar_ao_database(painel, 'database.csv')

            # Adicionar o placa processado à lista de recortes
            recortes.append(painel.to_dict())
        
        return recortes

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

import json

def make_json_serializable(data):
    """Recursivamente converte objetos não serializáveis em tipos compatíveis com JSON."""
    if isinstance(data, dict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(v) for v in data]
    elif hasattr(data, "denominator"):  # Detecta IFDRational
        return float(data) if data.denominator != 0 else None
    elif isinstance(data, (int, float, str, type(None))):
        return data
    else:
        return str(data)  # Converte valores não suportados em string


def detecta_defeito(placa, rgb_limite=200, dimensoes_limite=0.95):
    quant_hotspots, pos_hotspots = count_and_pos_hotspot(placa, rgb_limite)
    tamanhos_bounding_box = bouding_box(placa, pos_hotspots, quant_hotspots)

    placa_path = placa.image_path[:-4]

    if quant_hotspots[placa_path] == 0:
        placa.situation("Sem defeitos")

    elif quant_hotspots[placa_path] >= 1:
        imagem = placa.image
        largura_imagem, altura_imagem = imagem.size
        
        largura_bb = tamanhos_bounding_box[placa_path][1]['largura']
        altura_bb = tamanhos_bounding_box[placa_path][1]['altura']

        for i in range(1, len(pos_hotspots[placa_path]) + 1):
            altura_bb = max(altura_bb, tamanhos_bounding_box[placa_path][i]['altura'])
            largura_bb = max(largura_bb, tamanhos_bounding_box[placa_path][i]['largura'])

        if altura_bb >= (dimensoes_limite * altura_imagem) and largura_bb >= (dimensoes_limite * largura_imagem):
            placa.situation("Circuito aberto")
        elif altura_bb >= (dimensoes_limite * altura_imagem) or largura_bb >= (dimensoes_limite * largura_imagem):
            placa.situation("Curto circuito")
        else:
            placa.situation(f"{quant_hotspots[placa_path]} celula(s) com defeito(s)")

def save_to_csv(placa_matrix, csv_filename='resultado.csv'):
    """Salvar a matriz de placas em um arquivo CSV."""
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Cabeçalho
        writer.writerow(["Image Path", "Detected Panels"])
        
        # Escrever cada linha da matriz
        for placa_info, paineis in placa_matrix:
            image_path = placa_info.get('image_path', 'N/A')
            writer.writerow([image_path, paineis])

def process_uploaded_files(zip_file, mission_name):
    """Processar arquivos enviados em um arquivo .zip."""
    images = []

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.endswith(('_T.JPG', '_T.PNG', '_T.JPEG', '_T.jpg', '_T.png', '_T.jpeg')):
                with zip_ref.open(file_name) as file:
                    images.append({
                        'image_path': file_name,
                        'data': file.read(),
                    })

    processor = ImageProcessor(model_path="assets/best.pt")
    placa_matrix, paineis_processados = processor.process_images(images, mission_name)
    
    # Salvar a matriz em um CSV
    save_to_csv(placa_matrix)

    return placa_matrix, paineis_processados

# API para upload de arquivo .zip
@app.route('/upload-zip/<mission_name>', methods=['POST'])
def upload_zip(mission_name):
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    zip_file = request.files['file']
    placa_matrix = process_uploaded_files(zip_file, mission_name=mission_name)

    paineis_processados_serializaveis = make_json_serializable(placa_matrix)

    response = {
        "mission_name": mission_name,
        "processed_panels": paineis_processados_serializaveis
    }
    return jsonify(response)

@app.route('/database/<mission_name>', methods=['GET'])
def get_database(mission_name):

    placas = resgatar_panels_from_mission('database.csv', mission_name)
    return jsonify(placas)

if __name__ == "__main__":
    app.run(debug=True)
