import paho.mqtt.client as mqtt
import time
import binascii
import random
import zlib
import ssl
import json
import threading
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # charge le fichier .env
broker_address = "cac.campiserveur.com"
port = int(os.getenv("MQTT_PORT", 8886))  # valeur par défaut
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
client_cert = "client_certificate_prod.pem"
client_key = "client_prod.pem"
ca_cert = "combined_ca_prod.pem"

def zlibt_decompress(trame_compresses):
    try:
        decompressor = zlib.decompressobj(wbits=10)
        return decompressor.decompress(trame_compresses) + decompressor.flush()
    except Exception as e:
        print(f"Erreur lors de la décompression : {e}")
        return None
"""
def save_progress_to_file(serial, progress):
    try:
        with open(f"progression_{serial}.json", "w") as f:
            json.dump({"serial": serial, "progress": int(progress)}, f)
    except Exception as e:
        print(f"❌ Erreur enregistrement progression {serial} : {e}")
"""
def save_progress_to_file(serial, progress):
    try:
        conn = sqlite3.connect("progressions.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progressions (
                serial TEXT PRIMARY KEY,
                progress INTEGER,
                updated_at TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO progressions (serial, progress, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(serial) DO UPDATE SET
                progress = excluded.progress,
                updated_at = excluded.updated_at
        """, (serial, int(progress), datetime.utcnow()))
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        if "database or disk is full" in str(e).lower():
            print(f"💾 Erreur disque plein — impossible de sauvegarder la progression pour {serial}")
        else:
            print(f"❌ Erreur SQLite : {e}")
    except Exception as e:
        print(f"❌ Erreur d'enregistrement dans SQLite : {e}")

def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode('utf-8', errors='ignore').strip()

    if payload.startswith("progress="):
        progress_value = payload.replace("progress=", "")
        parts = topic.split("/")
        serial = parts[1] if len(parts) > 1 else "inconnu"
        save_progress_to_file(serial, progress_value)
        print(f"[{serial}] ➤ Progression {progress_value}%")

    elif topic.endswith("fw_version"):
        print(f"✅ [{topic}] Mise à jour terminée : {payload}")

def listen_to_topic(topic):
    client_id = f"mqtt-batch-{random.randint(1000, 9999)}"
    client = mqtt.Client(client_id)
    client.username_pw_set(username, password)

    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)
    client.tls_set_context(context)
    client.tls_insecure_set(False)

    client.on_message = on_message

    try:
        client.connect(broker_address, port)
        client.subscribe(topic, qos=1)
        client.loop_start()
        print(f"📡 Abonné à : {topic}")
        time.sleep(150)
        client.loop_stop()
        client.disconnect()
        print(f"🛑 Fin de l'écoute : {topic}")
    except Exception as e:
        print(f"❌ Erreur abonnement {topic} : {e}")

def run_batch(topics):
    threads = []
    for topic in topics:
        thread = threading.Thread(target=listen_to_topic, args=(topic,))
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()
