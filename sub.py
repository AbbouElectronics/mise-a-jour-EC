import paho.mqtt.client as mqtt
import time
import binascii
import random
import zlib
import ssl
import json
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()  # charge le fichier .env

# Récupération des variables
broker = "cac.campiserveur.com"
port = int(os.getenv("MQTT_PORT", 8886))  # valeur par défaut
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
client_cert = "client_certificate_prod.pem"
client_key = "client_prod.pem"
ca_cert = "combined_ca_prod.pem"

def zlibt_decompress(trame_compresses):
    try:
        decompressor = zlib.decompressobj(wbits=10)
        trame_decompresses = decompressor.decompress(trame_compresses) + decompressor.flush()
        return trame_decompresses
    except Exception as e:
        print(f"Erreur lors de la décompression : {e}")
        return None
"""
broker_address = 'birth01.campiserveur.com'
port = 8886
username = 'admin'
password = '0123456789ab'
client_cert = "client_certificate_sub.pem"
client_key = "client_sub.pem"
ca_cert = "combined_ca.pem"
"""
"""
def save_progress_to_file(serial, progress):
    try:
        with open("progression.json", "w") as f:
            json.dump({"serial": serial, "progress": int(progress)}, f)
    except Exception as e:
        print(f"❌ Erreur d'enregistrement de la progression : {e}")
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
    except Exception as e:
        print(f"❌ Erreur d'enregistrement dans SQLite : {e}")

        
def on_message_config(client, userdata, message):
    trame = message.payload
    trame_hex = binascii.hexlify(trame)
    try:
        with open('testsub.txt', 'a') as file_recu:
            if trame_hex[0:2] == b'28':
                trame = zlibt_decompress(trame)
                file_recu.write(str(trame) + '\n')
            else:
                file_recu.write(str(trame) + '\n')
    except Exception as e:
        print(f'Erreur lors de l\'écriture dans testsub.txt: {e}')

    print("message received", trame)
    print("message topic=", message.topic)
    print("message qos=", message.qos)
    print("message retain flag=", message.retain)

def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode('utf-8', errors='ignore').strip()

    if payload.startswith("progress="):
        progress_value = payload.replace("progress=", "")
        print(f"🔄 Progression : {progress_value}% (Topic: {topic})")

        parts = topic.split("/")
        serial = parts[1] if len(parts) > 1 else "inconnu"
        save_progress_to_file(serial, progress_value)

        with open('progression.log', 'a') as log_file:
            log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {serial} - Progression: {progress_value}%\n")

    elif topic.endswith("fw_version"):
        print(f"✅ Mise à jour terminée — Version : {payload}")
        with open('progression.log', 'a') as log_file:
            log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Version finale : {payload}\n")

    else:
        trame = message.payload
        trame_hex = binascii.hexlify(trame)
        try:
            with open('testsub.txt', 'a') as file_recu:
                if trame_hex[0:2] == b'28':
                    trame = zlibt_decompress(trame)
                    trame = binascii.hexlify(trame).decode('utf-8')
                    file_recu.write(trame)
                else:
                    trame = trame_hex.decode('utf-8')
                    file_recu.write(trame)
        except Exception as e:
            print(f'Erreur lors de l\'écriture dans testsub.txt: {e}')

        print("message received", trame)
        print("message topic=", message.topic)
        print("message qos=", message.qos)
        print("message retain flag=", message.retain)

def sub(client_id, topic, met):
    client = mqtt.Client(client_id)
    client.username_pw_set(username, password=password)

    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)
    client.tls_set_context(context)
    client.tls_insecure_set(False)

    if met == 'config':
        client.on_message = on_message_config
    else:
        client.on_message = on_message

    print("Connecting to broker")
    try:
        client.connect(broker_address, port)
    except Exception as e:
        print("Erreur de connexion au broker MQTT:", str(e))
        return

    print("Subscribing to topic", topic)
    client.subscribe(topic, qos=1)
    client.loop_start()

    # Boucle d'attente : on écoute pendant 40 secondes
    timeout = 120
    for i in range(timeout):
        time.sleep(1)

    client.loop_stop()
    client.disconnect()
    print("🛑 Fin de l'écoute MQTT")

def run(topic, met):
    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    sub(client_id, topic, met)
