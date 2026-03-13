from openpyxl import load_workbook
from django.db import transaction
from catalog.models import Product
from .models import Receipt, ReceiptDetail


class ReceiptImportError(Exception):
    pass


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


@transaction.atomic
def importar_recepcion_desde_excel(*, archivo, proveedor, numero_documento, fecha_documento, usuario):
    try:
        wb = load_workbook(archivo)
        ws = wb.active
    except Exception as e:
        raise ReceiptImportError(f"No fue posible leer el archivo Excel: {e}")

    encabezados = [normalizar_texto(cell.value).lower() for cell in ws[1]]

    columnas_esperadas = ["sku", "codigo_barra", "nombre", "cantidad"]
    faltantes = [col for col in columnas_esperadas if col not in encabezados]
    if faltantes:
        raise ReceiptImportError(
            f"Faltan columnas obligatorias en el Excel: {', '.join(faltantes)}"
        )

    idx = {nombre: encabezados.index(nombre) for nombre in columnas_esperadas}

    recepcion = Receipt.objects.create(
        proveedor=proveedor,
        numero_documento=numero_documento,
        fecha_documento=fecha_documento,
        archivo=archivo,
        estado=Receipt.Status.BORRADOR,
        creado_por=usuario,
    )

    filas_importadas = 0
    errores = []

    for nro_fila, row in enumerate(ws.iter_rows(min_row=2), start=2):
        sku = normalizar_texto(row[idx["sku"]].value)
        codigo_barra = normalizar_texto(row[idx["codigo_barra"]].value)
        nombre = normalizar_texto(row[idx["nombre"]].value)
        cantidad_valor = row[idx["cantidad"]].value

        if not sku and not codigo_barra:
            continue

        try:
            cantidad = int(cantidad_valor)
            if cantidad <= 0:
                raise ValueError
        except Exception:
            errores.append(f"Fila {nro_fila}: cantidad inválida.")
            continue

        producto = None

        if codigo_barra:
            producto = Product.objects.filter(
                codigo_barra=codigo_barra).first()

        if not producto and sku:
            producto = Product.objects.filter(sku=sku).first()

        if not producto:
            errores.append(
                f"Fila {nro_fila}: no se encontró producto para SKU '{sku}' o código '{codigo_barra}'."
            )
            continue

        ReceiptDetail.objects.create(
            recepcion=recepcion,
            producto=producto,
            cantidad_esperada=cantidad,
            cantidad_recibida=0,
            observacion=nombre
        )
        filas_importadas += 1

    if filas_importadas == 0:
        raise ReceiptImportError(
            "No se importó ninguna fila válida. Revisa el archivo."
        )

    return recepcion, filas_importadas, errores
