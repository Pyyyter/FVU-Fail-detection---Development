class Placa:
    def __init__(self, geolocation, image=None, image_path=None, mission_name=None):
        self.geolocation = geolocation
        self.image = image
        self.mission_name = mission_name
        self.image_path = image_path
        self.qualidadeplaca = None

    def situation(self, status):
        """Define a qualidade do placa com base na situação detectada."""
        self.qualidadeplaca = status

    def to_dict(self):
        """Converte o objeto placa em um dicionário para resposta JSON."""
        return {
            "geolocation": self.geolocation,
            "qualidadeplaca": self.qualidadeplaca,
            "image_path": self.image_path,
            "mission_name": self.mission_name
        }