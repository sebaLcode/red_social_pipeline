import time
import json
import logging

from pipeline.db import insert_notification, insert_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

EVENTOS_VALIDOS = ["like", "comentario", "seguidor"]
PALABRAS_OFENSIVAS = ["malo", "feo", "tonto", "idiota", "estúpido", "imbécil", "pendejo", "gilipollas",
                      "cretino", "tarado", "zopenco", "bobo", "bruto", "estúpida", "pendeja", "cretina",
                      "tarada", "zopenca", "boba", "bruta", "aweonao", "reculiao", "maricón", "maricon", "maricona", "hijo de puta", "hija de puta"]

"""
    Función para ingesta.
    Recibe el evento enviado por la API o por Airflow.
"""
def ingesta_evento(evento):
    logging.info(f"[INGESTA] Evento recibido: {evento}")
    return evento

"""
    Valida que el mensaje del comentario no contenga palabras ofensivas.
    Si se detecta una palabra ofensiva, se lanza una excepción para evitar que el comentario sea procesado y se registre un error en la tabla de errores.
"""
def validar_comentario_ofensivo(mensaje):
    mensaje_normalizado = mensaje.lower()

    for palabra in PALABRAS_OFENSIVAS:
        if palabra in mensaje_normalizado:
            raise ValueError(f"No se puede enviar el comentario: \"{mensaje}\" , contiene palabras ofensivas.")


"""
    Función para validación estructural y semántica.
    Verifica que existan los campos obligatorios y que el tipo de evento sea válido.
"""
def validar_evento(evento):
    if not isinstance(evento, dict):
        raise ValueError("El evento debe ser un diccionario.")

    campos_requeridos = [
        "evento_id",
        "usuario_origen",
        "usuario_destino",
        "tipo_evento"
    ]

    for campo in campos_requeridos:
        if campo not in evento or evento[campo] is None or evento[campo] == "":
            raise ValueError(f"Falta el campo obligatorio: {campo}")

    tipo_evento = evento["tipo_evento"].strip().lower()

    if tipo_evento not in EVENTOS_VALIDOS:
        raise ValueError(f"Tipo de evento no válido: {tipo_evento}")

    if tipo_evento == "comentario":
        mensaje = evento.get("mensaje", "").strip()

        if mensaje == "":
            raise ValueError("El comentario no puede estar vacío.")

        validar_comentario_ofensivo(mensaje)
    logging.info(f"[VALIDACIÓN] Evento validado correctamente: {evento['evento_id']}")

    return evento


"""
    Función para la limpieza y transformación.
    Limpia los datos recibidos y genera el mensaje de notificación.
"""
def transformar_evento(evento):
    evento_id = evento["evento_id"].strip()
    usuario_origen = evento["usuario_origen"].strip()
    usuario_destino = evento["usuario_destino"].strip()
    tipo_evento = evento["tipo_evento"].strip().lower()

    texto_comentario = evento.get("mensaje", "").strip()

    if tipo_evento == "like":
        mensaje = f"{usuario_origen} le dió like a tu publicación."
    elif tipo_evento == "comentario":
        if texto_comentario:
            mensaje = f"{usuario_origen} comentó en tu publicación: {texto_comentario}"
        else:
            mensaje = f"{usuario_origen} comentó en tu publicación."
    elif tipo_evento == "seguidor":
        mensaje = f"{usuario_origen} comenzó a seguirte."
    else:
        raise ValueError(f"Tipo de evento no reconocido: {tipo_evento}")

    notificacion = {
        "evento_id": evento_id,
        "usuario_origen": usuario_origen,
        "usuario_destino": usuario_destino,
        "tipo_evento": tipo_evento,
        "mensaje": mensaje
    }

    logging.info(f"[TRANSFORMACIÓN] Notificación generada: {notificacion}")

    return notificacion

"""
    Función para la carga.
    Guarda la notificación generada en la base de datos.
"""
def cargar_notificacion(notificacion, tiempo_inicio):
    latencia_ms = round((time.time() - tiempo_inicio) * 1000, 2)

    insert_notification(
        notificacion["evento_id"],
        notificacion["usuario_origen"],
        notificacion["usuario_destino"],
        notificacion["tipo_evento"],
        notificacion["mensaje"],
        latencia_ms
    )

    notificacion["latencia_ms"] = latencia_ms
    notificacion["status"] = "cargada"

    logging.info(f"[CARGA] Notificación cargada en BD: {notificacion}")

    return notificacion


"""
    Función para ejecutar el pipeline completo:
    1. Ingesta
    2. Validación
    3. Transformación
    4. Carga

Si ocurre un error, se registra en la tabla errores.
"""
def ejecutar_pipeline(evento):
    tiempo_inicio = time.time()

    try:
        evento_ingestado = ingesta_evento(evento)
        evento_validado = validar_evento(evento_ingestado)
        notificacion = transformar_evento(evento_validado)
        resultado = cargar_notificacion(notificacion, tiempo_inicio)

        return {
            "status": "exito",
            "mensaje": "Evento procesado correctamente",
            "notificacion": resultado
        }

    except Exception as e:
        evento_id = evento.get("evento_id", "desconocido")
        detalle_error = str(e)
        mensaje_error = f"Error en pipeline para evento {evento_id}: {detalle_error}"

        logging.error(f"[ERROR] {mensaje_error}")

        insert_error(
            evento_id,
            mensaje_error,
            json.dumps(evento, ensure_ascii=False)
        )

        if detalle_error == "No se puede enviar el comentario ofensivo.":
            return {
                "status": "error",
                "mensaje": "No se puede enviar el comentario ofensivo."
            }

        return {
            "status": "error",
            "mensaje": mensaje_error,
            "detalles": detalle_error
        }