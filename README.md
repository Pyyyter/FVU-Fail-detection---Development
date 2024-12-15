# API para Detecção de Defeitos em Placas Solares com YOLO

Esta API foi desenvolvida para processar imagens de placas solares e detectar defeitos utilizando o modelo YOLO. Ela suporta o upload de arquivos em formato `.zip` contendo imagens e retorna os resultados das análises em JSON ou em um arquivo CSV.

---

## 🔧 Funcionalidades

- **Processamento de Imagens:**
  - Suporta imagens nos formatos `.JPG`, `.JPEG` e `.PNG` com a terminação `_T`.
- **Detecção de Defeitos:**
  - Identifica hotspots em painéis solares.
  - Classifica defeitos como:
    - Circuito aberto.
    - Curto-circuito.
    - Células com defeito(s).
    - Sem defeitos.
- **Recorte de Imagens:**
  - Salva os recortes das regiões detectadas.
- **Geração de CSV:**
  - Exporta os resultados para um arquivo CSV.
- **Metadados EXIF:**
  - Extrai informações de geolocalização das imagens, se disponíveis.

---

## ↩️ Modelo do retorno das placas de uma missão:

```json
[
    {
        "ID": 1.0,
        "mission_name": "Iguaba",
        "image_path": "recortesIguaba/DJI_20241003122836_0007_T_BOX1",
        "situation": "Sem Defeitos",
        "location": {
            "latitude": "(22.0, 54.0, 24.8587)",
            "longitude": "(43.0, 7.0, 58.3923)"
        }
    },
    {
        "ID": 2.0,
        "mission_name": "Iguaba",
        "image_path": "recortesIguaba/DJI_20241003122836_0007_T_BOX2",
        "situation": "Sem Defeitos",
        "location": {
            "latitude": "(22.0, 54.0, 24.8587)",
            "longitude": "(43.0, 7.0, 58.3923)"
        }
    }
]

```
---

## Uso

Para enviar um arquivo ZIP contendo imagens para a API, você pode usar o comando `curl` no terminal.

### Enviar arquivo ZIP

```bash
curl -X POST -F "file=@seu_path.zip" http://localhost:5000/upload-zip/$nome_da_missão
```

### Retornar todas as missões

```bash
curl -X GET http://127.0.0.1:5000/database/missions
```

### Retornar todas as placas de uma missão

```bash
curl -X GET http://127.0.0.1:5000/database/${mission_name}
```
