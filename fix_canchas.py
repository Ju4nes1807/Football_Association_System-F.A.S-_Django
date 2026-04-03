import time
from inscripciones.models import Cancha
from inscripciones.utils import geodificar_direccion

def run():
    for c in Cancha.objects.filter(_latitud__isnull=True):

        lat, lng = geodificar_direccion(c._direccion_exacta)

        if lat and lng:
            c._latitud = lat
            c._longitud = lng
            c.save()
            print(f"OK: {c._nombre_escenario}")
        else:
            print(f"ERROR: {c._nombre_escenario} -> {c._direccion_exacta}")

        time.sleep(1.2)