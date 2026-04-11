import barcode
from barcode.writer import ImageWriter
import os


def generar_codigo_barra(codigo, nombre_archivo):
    ruta = os.path.join("media", "barcodes")
    os.makedirs(ruta, exist_ok=True)
    code128 = barcode.get("code128", codigo, writer=ImageWriter())
    filename = os.path.join(ruta, nombre_archivo)
    return code128.save(filename) + ".png"
