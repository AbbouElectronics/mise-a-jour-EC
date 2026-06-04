
import random
import time
from pub import run  # Correction de l'import
import threading
import ssl
import time
import paho.mqtt.client as mqtt
import os 
import csv

def publish_update_message(serial, version):
    token_time = int(time.time() * 1000)
    
    topic = f'{serial}/update/{token_time}'
    topic_mise_a_jour = f'+/{serial}/update/{token_time}'
    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    fw_version = f"fw_version={version}"
    #fw_version = f"reboot"
    """
    topic = f'{serial}/config/set/{token_time}'
    topic_mise_a_jour = f'+/{serial}/config/get/{token_time}'
    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    fw_version = f"alarm_include=5:0x184"
    """
    run(client_id, topic, fw_version, 'conf')  # Appel de la fonction MQTT de publication

    print(f"[MQTT] Envoi de la mise à jour : {serial} → {version}")
    return topic_mise_a_jour  # Retour du vrai topic utilisé

def publish_connect_pcal_message (serial):
    topic = f'{serial}/vigik/system/reboot'
    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    run(client_id, topic,' ', 'conf')  # Appel de la fonction MQTT de publicatio

def publish_disconnect_pcal_message (centrale_serial ,lecteur_serial):
    topic_config= f'{lecteur_serial}/config/set'
    topic_disconnect = f'{centrale_serial}/vigik/system/disconnect'
    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    run(client_id, topic_config,'mqtt_always_on=0', 'conf')  # Appel de la fonction MQTT de publicatio
    run(client_id, topic_disconnect,' ', 'conf') 
"""
def publish_get_info_lecteur(lecteur_serial):
    username = "admin"
    password = "0123456789ab"
    client_cert = "client_certificate_prod.pem"
    client_key = "client_prod.pem"
    ca_cert = "combined_ca_prod.pem"
    broker = "cac.campiserveur.com"
    port = int(os.getenv("MQTT_PORT", 8886))  # valeur par défaut
    response = {"received": False, "data": None}
    event = threading.Event()

    topic_sub = f"+/{lecteur_serial}/config/#"
    topic_pub = f"{lecteur_serial}/config/get"
    payload = "v2mv_cs"

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(topic_sub)
            run("abdel", topic_pub, payload, "conf")
        else:
            response["data"] = f"Erreur connexion MQTT rc={rc}"
            event.set()

    def on_message(client, userdata, msg):
        try:
            response["received"] = True
            response["data"] = {
                "topic": msg.topic,
                "payload": msg.payload.decode(errors="ignore")
            }
            event.set()
        except Exception as e:
            response["data"] = str(e)
            event.set()

    client = mqtt.Client()
    client.username_pw_set(username, password)

    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)

    client.tls_set_context(context)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port)
    client.loop_start()

    event.wait(timeout=40)

    client.loop_stop()
    client.disconnect()

    if response["received"]:
        return response["data"]
    else:
        return {
            "message": "Aucune réponse reçue du lecteur après 40 secondes",
            "topic_envoye": topic_pub,
            "payload_envoye": payload
        }
"""

def publish_get_info_lecteur(lecteur_serial):
    username = "admin"
    password = "0123456789ab"

    client_cert = "client_certificate_prod.pem"
    client_key = "client_prod.pem"
    ca_cert = "combined_ca_prod.pem"

    broker = "cac.campiserveur.com"
    port = int(os.getenv("MQTT_PORT", 8886))

    responses = {}
    event = threading.Event()

    topic_sub = f"+/{lecteur_serial}/config/#"
    topic_pub = f"{lecteur_serial}/config/get"

    params = ["v2mv_cs", "v2mv_ver"]

    def publish_params():
        time.sleep(2)

        for param in params:
            print(f"📤 Envoi : {param} -> {topic_pub}")
            client.publish(topic_pub, param, qos=1)
            time.sleep(1)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Client MQTT connecté")
            print("📡 Subscribe :", topic_sub)
            client.subscribe(topic_sub, qos=1)

            threading.Thread(target=publish_params).start()
        else:
            print(f"❌ Erreur connexion MQTT rc={rc}")
            event.set()

    def on_message(client, userdata, msg):
        payload_recu = msg.payload.decode(errors="ignore").strip()
        topic_recu = msg.topic

        print("📥 Reçu :", topic_recu, payload_recu)

        if payload_recu.startswith("v2mv_cs="):
            responses["v2mv_cs"] = {
                "param": "v2mv_cs",
                "value": payload_recu.replace("v2mv_cs=", ""),
                "topic": topic_recu,
                "payload": payload_recu
            }

        elif payload_recu.startswith("v2mv_ver="):
            responses["v2mv_ver"] = {
                "param": "v2mv_ver",
                "value": payload_recu.replace("v2mv_ver=", ""),
                "topic": topic_recu,
                "payload": payload_recu
            }

        if "v2mv_cs" in responses and "v2mv_ver" in responses:
            event.set()

    client = mqtt.Client(client_id=f"info-lecteur-{int(time.time() * 1000)}")
    client.username_pw_set(username, password)

    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)

    client.tls_set_context(context)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port)
    client.loop_start()

    event.wait(timeout=40)

    client.loop_stop()
    client.disconnect()

    result = []

    for param in params:
        if param in responses:
            result.append(responses[param])
        else:
            result.append({
                "param": param,
                "value": "Aucune réponse reçue",
                "topic": topic_pub,
                "payload": ""
            })

    return result


def read_centrales_lecteurs_csv(csv_path):
    pairs = []

    with open(csv_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=";")

        for row in reader:
            centrale_serial = row.get("centrale_serial", "").replace('"', '').strip()
            lecteur_serial = row.get("lecteur_serial", "").replace('"', '').strip()

            if centrale_serial and lecteur_serial:
                pairs.append({
                    "centrale_serial": centrale_serial,
                    "lecteur_serial": lecteur_serial
                })

    return pairs

"""
def publish_get_infos_lecteurs_from_excel(csv_path):
    username = "admin"
    password = "0123456789ab"

    client_cert = "client_certificate_prod.pem"
    client_key = "client_prod.pem"
    ca_cert = "combined_ca_prod.pem"

    broker = "cac.campiserveur.com"
    port = int(os.getenv("MQTT_PORT", 8886))

    pairs = read_centrales_lecteurs_csv(csv_path)

    if not pairs:
        return []

    params = ["v2mv_cs", "v2mv_ver"]
    responses = {}
    event = threading.Event()

    expected_count = len(pairs) * len(params)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ MQTT connecté pour traitement Excel")

            for pair in pairs:
                lecteur_serial = pair["lecteur_serial"]
                topic_sub = f"+/{lecteur_serial}/config/#"
                print("📡 Subscribe :", topic_sub)
                client.subscribe(topic_sub, qos=1)

            def worker():
                print("🔄 Reconnexion de tous les lecteurs...")

                for pair in pairs:
                    centrale_serial = pair["centrale_serial"]
                    lecteur_serial = pair["lecteur_serial"]

                    print(f"🔄 Reconnect lecteur {lecteur_serial} via centrale {centrale_serial}")
                    publish_connect_pcal_message(centrale_serial)
                    time.sleep(0.3)

                print("⏳ Attente 60 secondes avant récupération infos...")
                time.sleep(60)

                print("📤 Envoi des demandes v2mv_cs et v2mv_ver...")

                for pair in pairs:
                    lecteur_serial = pair["lecteur_serial"]
                    topic_pub = f"{lecteur_serial}/config/get"

                    for param in params:
                        print(f"📤 {lecteur_serial} -> {param}")
                        client.publish(topic_pub, param, qos=1)
                        time.sleep(0.3)

            threading.Thread(target=worker).start()

        else:
            print(f"❌ Erreur connexion MQTT rc={rc}")
            event.set()

    def on_message(client, userdata, msg):
        payload_recu = msg.payload.decode(errors="ignore").strip()
        topic_recu = msg.topic

        print("📥 Reçu :", topic_recu, payload_recu)

        for pair in pairs:
            lecteur_serial = pair["lecteur_serial"]

            if lecteur_serial in topic_recu:
                for param in params:
                    if payload_recu.startswith(param + "="):
                        key = f"{lecteur_serial}_{param}"
                        value = payload_recu.replace(param + "=", "")

                        responses[key] = {
                            "lecteur_serial": lecteur_serial,
                            "param": param,
                            "value": value,
                            "topic": topic_recu,
                            "payload": payload_recu
                        }

        if len(responses) >= expected_count:
            event.set()

    client = mqtt.Client(client_id=f"excel-info-{int(time.time() * 1000)}")
    client.username_pw_set(username, password)

    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)

    client.tls_set_context(context)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port)
    client.loop_start()

    event.wait(timeout=150)

    client.loop_stop()
    client.disconnect()

    results = []

    for pair in pairs:
        centrale_serial = pair["centrale_serial"]
        lecteur_serial = pair["lecteur_serial"]

        cs_key = f"{lecteur_serial}_v2mv_cs"
        ver_key = f"{lecteur_serial}_v2mv_ver"

        v2mv_cs = responses.get(cs_key, {}).get("value", "Aucune réponse")
        v2mv_ver = responses.get(ver_key, {}).get("value", "Aucune réponse")

        if v2mv_cs != "Aucune réponse" and v2mv_ver != "Aucune réponse":
            status = "✅ OK"
        elif v2mv_cs != "Aucune réponse" or v2mv_ver != "Aucune réponse":
            status = "⚠️ Réponse partielle"
        else:
            status = "❌ Aucune réponse"

        results.append({
            "centrale_serial": centrale_serial,
            "lecteur_serial": lecteur_serial,
            "v2mv_cs": v2mv_cs,
            "v2mv_ver": v2mv_ver,
            "status": status
        })

    return results
"""
def publish_get_infos_lecteurs_from_excel(csv_path):
    pairs = read_centrales_lecteurs_csv(csv_path)

    all_results = []

    if not pairs:
        return all_results

    for batch_index, batch_pairs in enumerate(chunk_list(pairs,50), start=1):
        print(f"📦 Traitement lot {batch_index} : {len(batch_pairs)} lecteurs")

        batch_results = publish_get_infos_for_batch(batch_pairs)

        all_results.extend(batch_results)

    return all_results

def chunk_list(items, size=50):
    for i in range(0, len(items), size):
        yield items[i:i + size]

def publish_get_infos_for_batch(pairs):
    username = "admin"
    password = "0123456789ab"

    client_cert = "client_certificate_prod.pem"
    client_key = "client_prod.pem"
    ca_cert = "combined_ca_prod.pem"

    broker = "cac.campiserveur.com"
    port = int(os.getenv("MQTT_PORT", 8886))

    params = ["v2mv_cs", "v2mv_ver"]
    responses = {}
    event = threading.Event()

    expected_count = len(pairs) * len(params)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ MQTT connecté pour un lot")

            for pair in pairs:
                lecteur_serial = pair["lecteur_serial"]
                client.subscribe(f"+/{lecteur_serial}/config/#", qos=1)

            def worker():
                print("🔄 Reconnexion du lot...")

                for pair in pairs:
                    publish_connect_pcal_message(pair["centrale_serial"])
                    time.sleep(0.3)

                print("⏳ Attente 60 secondes...")
                time.sleep(60)

                print("📡 Récupération infos du lot...")

                for pair in pairs:
                    lecteur_serial = pair["lecteur_serial"]
                    topic_pub = f"{lecteur_serial}/config/get"

                    for param in params:
                        client.publish(topic_pub, param, qos=1)
                        time.sleep(0.3)

            threading.Thread(target=worker).start()

        else:
            print(f"❌ Erreur MQTT rc={rc}")
            event.set()

    def on_message(client, userdata, msg):
        payload = msg.payload.decode(errors="ignore").strip()
        topic = msg.topic

        for pair in pairs:
            lecteur_serial = pair["lecteur_serial"]

            if lecteur_serial in topic:
                for param in params:
                    if payload.startswith(param + "="):
                        responses[f"{lecteur_serial}_{param}"] = payload.replace(param + "=", "")

        if len(responses) >= expected_count:
            event.set()

    client = mqtt.Client(client_id=f"batch-info-{int(time.time() * 1000)}")
    client.username_pw_set(username, password)

    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)

    client.tls_set_context(context)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port)
    client.loop_start()

    event.wait(timeout=120)

    client.loop_stop()
    client.disconnect()

    results = []

    for pair in pairs:
        centrale_serial = pair["centrale_serial"]
        lecteur_serial = pair["lecteur_serial"]

        v2mv_cs = responses.get(f"{lecteur_serial}_v2mv_cs", "Aucune réponse")
        v2mv_ver = responses.get(f"{lecteur_serial}_v2mv_ver", "Aucune réponse")

        if v2mv_cs != "Aucune réponse" and v2mv_ver != "Aucune réponse":
            status = "✅ OK"
        elif v2mv_cs != "Aucune réponse" or v2mv_ver != "Aucune réponse":
            status = "⚠️ Réponse partielle"
        else:
            status = "❌ Aucune réponse"

        results.append({
            "centrale_serial": centrale_serial,
            "lecteur_serial": lecteur_serial,
            "v2mv_cs": v2mv_cs,
            "v2mv_ver": v2mv_ver,
            "status": status
        })

    return results