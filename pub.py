import random
import time
from paho.mqtt import client as mqtt_client
import logging
from tkinter import Tk, Text, TOP, BOTH, X, N, LEFT, RIGHT, ttk, END
from tkinter.ttk import Frame, Label, Entry, Button
import threading
from tkinter.scrolledtext import ScrolledText
import ssl
from dotenv import load_dotenv
import os

load_dotenv()  # charge le fichier .env

# Récupération des variables
broker = "cac.campiserveur.com"
port = int(os.getenv("MQTT_PORT", 8886))  # valeur par défaut
#username = os.getenv("MQTT_USERNAME")
#password = os.getenv("MQTT_PASSWORD")
client_cert = "client_certificate_prod.pem"
client_key = "client_prod.pem"
ca_cert = "combined_ca_prod.pem"


"""
# Informations d'identification pour se connecter au broker MQTT
broker = 'birth01.campiserveur.com'
port = 8886  # Port pour la connexion TLS
username = 'admin'
password = '0123456789ab'
client_cert = "client_certificate_cac01.pem"
client_key = "client.pem"
ca_cert = "combined_ca.pem"
"""
def connect_mqtt(client_id):
    """
    Fonction pour se connecter au broker MQTT
    """
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(client_id)
   # client.username_pw_set(username, password)
   # Créer un contexte SSL sécurisé
    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")

    # Charger les certificats et la clé privée
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)

    # Configurer le client MQTT pour utiliser ce contexte SSL
    client.tls_set_context(context)
    client.tls_insecure_set(True)  # Active la vérification du certificat
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client, topic, my_hexdata, res):
    """
    Fonction pour publier un message sur un topic MQTT
    """
    if res == 'conf':
        result = client.publish(topic, my_hexdata, qos=1)
        status = result[0]
        print("Message envoyé", my_hexdata)
        print("Message topic=", topic)
        print("Message qos=", '1')
        if status == 0:
            print(f"Send `{result}` to topic `{topic}`")
        else:
            print(f"Failed to send message '{my_hexdata}' to topic {topic}")
    else:
        by = bytearray.fromhex(my_hexdata)
        result = client.publish(topic, by, qos=1)
        status = result[0]
        print("Message envoyé", my_hexdata)
        print("Topic=", topic)
        print("Qos=", '1')
        if status == 0:
            print(f"Send `{my_hexdata}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
    client.loop_stop()

def run(client_id, topic, my_hexdata, res):
    """Fonction principale pour exécuter la publication MQTT"""
    client = connect_mqtt(client_id)
    client.loop_start()
    publish(client, topic, my_hexdata, res)
