from flask import Flask, render_template, request, redirect, url_for, flash
from app.db import get_equipment_by_serial, get_equipments_by_site , get_all_sites ,get_serials_from_csv,get_equipments_by_gestion , get_all_gestions  
from mqtt_launcher import start_mqtt_listener  # 🔁 à créer
import json
import time
from app.mqtt_client import publish_update_message , publish_connect_pcal_message , publish_disconnect_pcal_message ,publish_get_infos_lecteurs_from_excel
from app.updater import check_and_update_equipment
from sub_batch import * 
import os
import json
from flask import jsonify
from pub import *
from dotenv import load_dotenv
import os
from flask_socketio import SocketIO
import ssl
import threading
import paho.mqtt.client as mqtt

load_dotenv()  # charge le fichier .env

broker = "cac.campiserveur.com"
port = int(os.getenv("MQTT_PORT", 8886))  # valeur par défaut
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
client_cert = "client_certificate_prod.pem"
client_key = "client_prod.pem"
ca_cert = "combined_ca_prod.pem"




app = Flask(__name__, template_folder="app/templates")
app.secret_key = 'secret_key_here'
socketio = SocketIO(app)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        serial = request.form['serial']
        target_version = request.form['target_version']

        result = check_and_update_equipment(serial, target_version)
        flash(result['message'], 'success' if result['success'] else 'error')
        return redirect(url_for('update'))

    return render_template('update.html')

@app.route('/update/serial', methods=['GET', 'POST'])
def update_serial():
    if request.method == 'POST':
        serial = request.form['serial']
        target_version = request.form['target_version']

        # Progression à 0%
        with open("progression.json", "w") as f:
            json.dump({"serial": serial, "progress": 0}, f)

        # Lancer écoute MQTT (en arrière-plan)
        topic = f"+/{serial}/update/#"
        start_mqtt_listener(topic, mode="update")

        # Envoie la mise à jour
        result = check_and_update_equipment(serial, target_version)
        print(result)
        # Redirige vers la page avec barre de progression
        return redirect(url_for('progress_page'))

    return render_template('update_serial.html')

@app.route('/progress')
def progress_page():
    return render_template('progress_bar.html')

@app.route('/api/progress')
def api_progress():
    try:
        with open("progression.json", "r") as f:
            data = json.load(f)
            return data
    except:
        return {"serial": "", "progress": 0}
@app.route('/update/batch', methods=['GET', 'POST'])
def update_batch():
    results = []
    serials = []

    if request.method == 'POST':
        serials_raw = request.form['serials']
        target_version = request.form['target_version']
        serials = [s.strip() for s in serials_raw.strip().splitlines() if s.strip()]
        topics = []

        for serial in serials:
            reset_progress(serial)
            topic = publish_update_message(serial, target_version)
            topics.append(topic)
            results.append({
                "serial": serial,
                "message": f"Mise à jour envoyée à l’équipement {serial} vers la version {target_version}"
            })

        # ✅ Lancer run_batch() dans un thread non-bloquant
        threading.Thread(target=run_batch, args=(topics,)).start()

    return render_template('update_batch.html', results=results, serials=serials)
"""
@app.route('/api/progress/<serial>')
def get_progress(serial):
    filename = f"progression_{serial}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            return jsonify(data)
    else:
        return jsonify({"serial": serial, "progress": 0})
 """ 
@app.route('/api/progress/<serial>')
def get_progress(serial):
    conn = sqlite3.connect("progressions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT progress FROM progressions WHERE serial = ?", (serial,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"serial": serial, "progress": row[0]})
    else:
        return jsonify({"serial": serial, "progress": 0})
def reset_progress(serial):
    try:
        conn = sqlite3.connect("progressions.db")
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE progressions SET progress = 0, updated_at = ?
            WHERE serial = ?
        """, (datetime.utcnow(), serial))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erreur de réinitialisation de la progression : {e}")
@app.route('/update/site', methods=['GET', 'POST'])
def update_by_site():
    results = []
    serials = []

    all_sites = get_all_sites()
    selected_serials = request.form.getlist("selected_serials")
    site = request.form.get('site')
    target_version = request.form.get('target_version')

    if request.method == 'POST' and selected_serials:
        topics = []

        for serial in selected_serials:
            serials.append(serial)
            reset_progress(serial)
            topic = publish_update_message(serial, target_version)
            topics.append(topic)

            results.append({
                "serial": serial,
                "message": f"Mise à jour envoyée à l’équipement {serial}"
            })

        threading.Thread(target=run_batch, args=(topics,)).start()

    return render_template('update_site.html', all_sites=all_sites, results=results, serials=serials)

@app.route("/api/site-centrales", methods=["POST"])
def api_get_site_centrales():
    try:
        site_names = request.json.get("sites", [])  # c’est déjà une liste
        print("🔍 Sites reçus :", site_names)
        all_equipment = []
        for name in site_names:
            equip = get_equipments_by_site(name.strip())  # just strip les noms
            all_equipment.extend(equip)
        return jsonify(all_equipment)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/gestion-centrales/<gestion_name>')
def api_get_gestion_centrales(gestion_name):
    try:
        équipements = get_equipments_by_gestion(gestion_name)
        return jsonify(équipements)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/update/gestion', methods=['GET', 'POST'])
def update_by_gestion():
    results = []
    serials = []
    all_gestions = get_all_gestions()

    if request.method == 'POST':
        gestion = request.form.get('gestion')
        target_version = request.form.get('target_version')
        selected_serials = request.form.getlist('selected_serials')

        if gestion and target_version and selected_serials:
            topics = []
            for serial in selected_serials:
                serials.append(serial)
                reset_progress(serial)
                topic = publish_update_message(serial, target_version)
                topics.append(topic)
                results.append({
                    "serial": serial,
                    "message": f"Mise à jour envoyée à l’équipement {serial}"
                })

            # Exécution du traitement en arrière-plan
            threading.Thread(target=run_batch, args=(topics,)).start()

    return render_template("update_gestion.html", all_gestions=all_gestions, results=results, serials=serials)


@app.route('/api/gestion-centrales-multi')
def api_get_centrales_multi():
    gestions_param = request.args.get('gestions', '')
    if not gestions_param:
        return jsonify([])

    gestion_list = [g.strip() for g in gestions_param.split(',') if g.strip()]
    all_equipments = []

    for gestion in gestion_list:
        try:
            équipements = get_equipments_by_gestion(gestion)
            all_equipments.extend(équipements)
        except Exception as e:
            print(f"❌ Erreur pour la gestion '{gestion}' : {e}")

    return jsonify(all_equipments)


@app.route('/api/ping/<serial>')
def ping_device(serial):
    token_time = int(time.time() * 1000)
    status = {"received": False}
    event = threading.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(f"+/{serial}/system/#")
        else:
            print(f"Erreur de connexion MQTT : {rc}")

    def on_message(client, userdata, msg):
        if msg.topic == f"baticonnect/{serial}/system/{token_time}":
            if b"status=1" in msg.payload:
                status["received"] = True
                event.set()
        elif msg.topic == f"sac/{serial}/system/":
            if b"status=1" in msg.payload:
                status["received"] = True
                event.set()
    # MQTT Configuration
    """
    broker_address = 'birth01.campiserveur.com'
    port = 8886
    username = 'admin'
    password = '0123456789ab'
    client_cert = "client_certificate_sub.pem"
    client_key = "client_sub.pem"
    ca_cert = "combined_ca.pem"
    """

    client = mqtt.Client()

    #client.username_pw_set(username, password=password)
    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)
    client.tls_set_context(context)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(broker_address, port)
        client.loop_start()
       
        # Envoi du message de test
        run("abdel", f"{serial}/system/{token_time}", "status_refresh","conf")

        # Attente d'une réponse pendant 40 secondes max
        event.wait(timeout=40)
    finally:
        client.loop_stop()
        client.disconnect()

    return jsonify({"status": "✅ Connecté" if status["received"] else "❌ Non connecté"})


@app.route("/api/reconnect-lecteur", methods=["POST"])
def reconnect_lecteur():
    data = request.json
    centrale_serial = data.get("centrale_serial")
    lecteur_serial = data.get("lecteur_serial")
    
    if not centrale_serial:
        return jsonify(success=False, error="Numéro de série centrale manquant")

    try:
        
        publish_connect_pcal_message (centrale_serial)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route("/api/disconnect-lecteur", methods=["POST"])
def disconnect_lecteur():
    data = request.get_json()
    lecteur_serial = data.get("lecteur_serial")
    centrale_serial = data.get("centrale_serial")

    if not lecteur_serial or not centrale_serial:
        return jsonify({"success": False, "error": "Numéros de série manquants"}), 400

    try:
        publish_disconnect_pcal_message(centrale_serial, lecteur_serial)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ===============================
# ✅ DB INIT
# ===============================
def init_db():
    conn = sqlite3.connect("auto_updates.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial TEXT,
            type TEXT,
            version TEXT,
            timestamp TEXT,
            updated INTEGER DEFAULT 0,
            applied INTEGER DEFAULT 0,
            retry_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ===============================
# ✅ UTILS
# ===============================
def get_type_from_serial(serial):
    if serial.startswith("1101-") or serial.startswith("1001-"):
        return "centrale"
    elif len(serial) == 32 and serial.isalnum():
        return "lecteur"
    return "inconnu"

def extract_serial(topic):
    parts = topic.split("/")
    if len(parts) >= 2:
        return parts[1]
    return "inconnu"

def save_update(serial, category, version, updated):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("auto_updates.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO updates (serial, type, version, timestamp, updated)
        VALUES (?, ?, ?, ?, ?)
    """, (serial, category, version, now, int(updated)))
    conn.commit()
    conn.close()

def mark_update_applied(serial):
    conn = sqlite3.connect("auto_updates.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE updates SET applied = 1 WHERE serial = ? AND updated = 1
    """, (serial,))
    conn.commit()
    conn.close()

def can_retry_update(serial, max_retries=5):
    conn = sqlite3.connect("auto_updates.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM updates WHERE serial = ? AND updated = 1", (serial,))
    count = cursor.fetchone()[0]

    conn.close()
    return count < max_retries

def update_exists(serial):
    conn = sqlite3.connect("auto_updates.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM updates WHERE serial = ? AND updated = 1", (serial,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


@app.route("/update/auto")
def update_auto():
    return render_template("update_auto.html")

@app.route("/api/start-mqtt-listener", methods=["POST"])
def start_mqtt_listener():
    threading.Thread(target=start_mqtt_watch).start()
    return jsonify({"status": "started"})

@app.route("/api/stop-mqtt-listener", methods=["POST"])
def stop_mqtt_listener():
    global mqtt_client_ref
    if mqtt_client_ref:
        try:
            mqtt_client_ref.loop_stop()
            mqtt_client_ref.disconnect()
            mqtt_client_ref = None
            return jsonify({"status": "stopped"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "no_client"})
def start_mqtt_watch():
    global mqtt_client_ref

    from app.mqtt_client import read_centrales_lecteurs_csv

    # Charge le mapping centrale → lecteurs depuis le CSV
    centrale_to_lecteurs = {}
    try:
        pairs = read_centrales_lecteurs_csv("centrales_lecteurs.csv")
        for p in pairs:
            c, l = p["centrale_serial"], p["lecteur_serial"]
            centrale_to_lecteurs.setdefault(c, []).append(l)
        print(f"[AUTO] CSV chargé : {len(pairs)} paires centrale/lecteur")
    except Exception as e:
        print(f"[AUTO] Erreur chargement CSV : {e}")

    # Ensemble des serials en attente de fw_version
    pending = set()

    def reconnect_lecteurs_for_centrale(mqtt_client, centrale_serial):
        """Reconnecte les lecteurs d'une centrale et demande leur version."""
        lecteurs = centrale_to_lecteurs.get(centrale_serial, [])
        if not lecteurs:
            return

        time.sleep(5)
        print(f"[AUTO] Reconnexion lecteurs de centrale {centrale_serial}")
        publish_connect_pcal_message(centrale_serial)

        for l in lecteurs:
            pending.add(l)

        # Laisse le temps au lecteur de se connecter via la centrale
        time.sleep(20)

        for l in lecteurs:
            if l in pending:
                print(f"[AUTO] Demande fw_version lecteur {l}")
                mqtt_client.publish(f"{l}/system", "status_refresh", qos=0)

    def emit_alert(serial, category, payload, mise_a_jour):
        socketio.emit("mqtt_alert", {
            "serial": serial,
            "type": category,
            "version": payload,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mise_a_jour": mise_a_jour
        })

    def on_message(client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode().strip()
        serial = extract_serial(topic)
        category = get_type_from_serial(serial)
        seuil = "1.3.8" if category == "centrale" else "1.4.11"
        target_version = "1.3.8" if category == "centrale" else "1.4.10"

        if topic.endswith("connected") and payload == "1":
            pending.add(serial)
            client.publish(f"{serial}/system", "status_refresh", qos=0)
            print(f"[AUTO] Connexion détectée : {serial} ({category})")

            # Si c'est une centrale, reconnecte ses lecteurs en arrière-plan
            if category == "centrale" and serial in centrale_to_lecteurs:
                threading.Thread(
                    target=reconnect_lecteurs_for_centrale,
                    args=(client, serial),
                    daemon=True
                ).start()

        elif topic.endswith("fw_version"):
            if serial not in pending:
                # Lecteur non marqué "pending" mais fw_version reçu : on traite quand même
                # (cas où le connected n'a pas été capté)
                if category == "lecteur":
                    pending.add(serial)
                else:
                    return

            pending.discard(serial)
            print(f"[AUTO] fw_version reçu : {serial} ({category}) = {payload}")

            if payload < seuil:
                if can_retry_update(serial):
                    publish_update_message(serial, target_version)
                    save_update(serial, category, payload, True)
                    emit_alert(serial, category, payload, True)
                    print(f"[AUTO] Mise à jour envoyée : {serial} → {target_version}")
                else:
                    emit_alert(serial, category, payload, "bloquée")
                    print(f"[AUTO] Mise à jour bloquée (5 essais max) : {serial}")
            elif payload == seuil and update_exists(serial):
                mark_update_applied(serial)
                emit_alert(serial, category, payload, "appliquée")
                print(f"[AUTO] Mise à jour confirmée appliquée : {serial}")

    client = mqtt.Client()
    client.username_pw_set(username, password)
    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT:@SECLEVEL=1")
    context.load_cert_chain(certfile=client_cert, keyfile=client_key)
    context.load_verify_locations(cafile=ca_cert)
    client.tls_set_context(context)
    client.tls_insecure_set(False)

    client.on_message = on_message
    client.connect(broker, port)
    client.subscribe("+/+/connected", qos=1)
    client.subscribe("+/+/fw_version", qos=1)

    # Souscrit aussi directement aux topics lecteurs connus pour ne rien rater
    for lecteur_list in centrale_to_lecteurs.values():
        for lecteur_serial in lecteur_list:
            client.subscribe(f"+/{lecteur_serial}/fw_version", qos=1)
            client.subscribe(f"+/{lecteur_serial}/connected", qos=1)

    mqtt_client_ref = client
    client.loop_forever()
@app.route("/api/reconnect-lecteurs_auto", methods=["POST"])
def reconnect_lecteurs_auto():
    try:
        data = request.get_json()
        nombre = int(data.get("nombre", 0))  # nombre de centrales à traiter

        if nombre <= 0:
            return jsonify({"status": "error", "message": "Nombre invalide"}), 400

        pairs = get_serials_from_csv("centrales_lecteurs.csv", nombre)

        if not pairs:
            return jsonify({"status": "error", "message": "Aucune centrale trouvée"}), 404

        for centrale_serial, lecteur_serial in pairs:
            # Reconnexion du lecteur via la centrale
            publish_connect_pcal_message(centrale_serial)

            # Envoi du message "status_refresh" au lecteur
            token_time = int(time.time() * 1000)
            run("abdel", f"{lecteur_serial}/system/{token_time}", "status_refresh", "conf")

        return jsonify({
            "status": "success",
            "message": f"{len(pairs)} centrales traitées"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route("/lecteur/info")
def lecteur_info_page():
    return render_template("lecteur_info.html")
@app.route("/api/lecteur/info", methods=["POST"])
def get_info_lecteur():
    data = request.get_json()
    lecteur_serial = data.get("lecteur_serial")

    if not lecteur_serial:
        return jsonify({
            "success": False,
            "error": "Numéro de série lecteur manquant"
        }), 400

    try:
        infos = publish_get_info_lecteur(lecteur_serial)
        return jsonify({
            "success": True,
            "infos": infos
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/lecteurs/info-excel", methods=["POST"])
def get_infos_lecteurs_excel():
    try:
        results = publish_get_infos_lecteurs_from_excel("centrales_lecteurs.csv")
        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    socketio.run(app, debug=True)




