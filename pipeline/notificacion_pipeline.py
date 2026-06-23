import time
import json
import logging
import joblib
from pipeline.db import insert_notification, insert_error
from pathlib import Path
import random

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

EVENTOS_VALIDOS = ["like", "comentario", "seguidor"]
# PALABRAS_OFENSIVAS = ["malo", "feo", "tonto", "idiota", "estúpido", "imbécil", "pendejo", "gilipollas",
#                       "cretino", "tarado", "zopenco", "bobo", "bruto", "estúpida", "pendeja", "cretina",
#                       "tarada", "zopenca", "boba", "bruta", "aweonao", "reculiao", "maricón", "maricon", "maricona", "hijo de puta", "hija de puta"]

#Cargar el modelo de clasificación de comentarios ofensivos
BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_MODELO_OFENSIVO = BASE_DIR / "modelosML" / "modelo_ofensivo_svm.pkl"
RUTA_MODELO_RELEVANCIA = BASE_DIR / "modelosML" / "modelo_relevancia_rf.pkl"


modelo_ofensivo_svm = joblib.load(RUTA_MODELO_OFENSIVO)

modelo_relevancia_rf = joblib.load(RUTA_MODELO_RELEVANCIA)

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
    
    prediccion = modelo_ofensivo_svm.predict([mensaje])[0]
    probabilidad = modelo_ofensivo_svm.predict_proba([mensaje])[0][1]

    resultado = "Ofensivo" if prediccion == 1 else "No ofensivo"

    print("Mensaje:", mensaje)
    print("Clasificación:", resultado)
    print(f"Probabilidad de ser ofensivo: {probabilidad:.2%}")
    
    if resultado == "Ofensivo":
        raise ValueError(f"No se puede enviar el comentario ofensivo: {mensaje}.")
    
    #Log, para ver la probabilidad de ser ofensivo y la clasificación del mensaje
    logging.info(f"[VALIDACIÓN] Mensaje: {mensaje} | Clasificación: {resultado} | Probabilidad de ser ofensivo: {probabilidad:.2%}")


def validar_relevancia_evento(eventos_homologos, seguidores_emisor, is_follow):
    if seguidores_emisor >490000:
        prediccion = modelo_relevancia_rf.predict([[eventos_homologos, seguidores_emisor, 1]])[0]
    else:
        prediccion = modelo_relevancia_rf.predict([[eventos_homologos, seguidores_emisor, is_follow]])[0]
    probabilidad = modelo_relevancia_rf.predict_proba([[eventos_homologos, seguidores_emisor, is_follow]])[0][1]

    resultado = "relevante" if prediccion == 1 else "no relevante"
    
    print(f"Eventos homologos: {eventos_homologos}, Seguidores emisor: {seguidores_emisor}, Is follow: {is_follow}")
    print("Clasificación:", resultado)
    print(f"Probabilidad de ser relevante: {probabilidad:.2%}")
    
    if resultado == "no relevante":
        raise ValueError(f"El evento no es relevante: {eventos_homologos}.")
    
    logging.info(f"[VALIDACIÓN] Evento: {eventos_homologos} | Clasificación: {resultado} | Probabilidad de ser relevante: {probabilidad:.2%}")


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
        "tipo_evento",
        "eventos_homologos",
        "seguidores_emisor",
        "is_follow"
    ]
    

    for campo in campos_requeridos:
        if campo not in evento or evento[campo] is None or evento[campo] == "":
            raise ValueError(f"Falta el campo obligatorio: {campo}")
        
    if not isinstance(evento.get("eventos_homologos"), int):
        raise ValueError("El campo 'eventos_homologos' debe ser un entero.")

    if not isinstance(evento.get("seguidores_emisor"), int):
        raise ValueError("El campo 'seguidores_emisor' debe ser un entero.")

    #is_follow debe ser convertido a booleano, ya que puede llegar como string desde la API
    is_follow = evento.get("is_follow")
    if isinstance(is_follow, str):
        is_follow = is_follow.lower() == "true"

    if not isinstance(is_follow, bool):
        raise ValueError("El campo 'is_follow' debe ser un booleano.")

    # Validar que los campos numéricos no sean negativos
    if evento.get("eventos_homologos") < 0:
        raise ValueError("El campo 'eventos_homologos' no puede ser negativo.")

    if evento.get("seguidores_emisor") < 0:
        raise ValueError("El campo 'seguidores_emisor' no puede ser negativo.")

    if evento.get("is_follow") is None:
        raise ValueError("El campo 'is_follow' no puede ser None.")

    tipo_evento = evento["tipo_evento"].strip().lower()


    if tipo_evento not in EVENTOS_VALIDOS:
        raise ValueError(f"Tipo de evento no válido: {tipo_evento}")

    else:
        
        #Ahora agregar eventos_homologos, seguidores_emisor e is_follow al evento para que puedan ser usados en la validación de relevancia del evento
        eventos_homologos = evento.get("eventos_homologos", 0)
        seguidores_emisor = evento.get("seguidores_emisor", 0)
        is_follow = evento.get("is_follow", False)
            
        if tipo_evento == "comentario":
            mensaje = evento.get("mensaje", "").strip()

            if mensaje == "":
                raise ValueError("El comentario no puede estar vacío.")

            validar_comentario_ofensivo(mensaje)
            
            #Rnadom para generar eventos homologos, seguidores del emisor y si el emisor sigue al receptor, para validar la relevancia del evento
            # eventos_homologos = random.randint(0, 100000)
            # seguidores_emisor = random.randint(0, 100000)
            # is_follow = random.choice([True, False])
            validar_relevancia_evento(eventos_homologos, seguidores_emisor, is_follow)
        
        elif tipo_evento == "like":
            #Random para generar eventos homologos, seguidores del emisor y si el emisor sigue al receptor, para validar la relevancia del evento
            # eventos_homologos = random.randint(0, 100000)
            # seguidores_emisor = random.randint(0, 100000)
            # is_follow = random.choice([True, False])
            validar_relevancia_evento(eventos_homologos, seguidores_emisor, is_follow)
        
        elif tipo_evento == "seguidor":
            #Random para generar eventos homologos, seguidores del emisor y si el emisor sigue al receptor, para validar la relevancia del evento
            # eventos_homologos = random.randint(0, 100000)
            # seguidores_emisor = random.randint(0, 100000)
            validar_relevancia_evento(eventos_homologos, seguidores_emisor, is_follow)
        
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
