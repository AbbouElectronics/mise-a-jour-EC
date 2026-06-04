
import threading
import random
from sub import sub  # Correction d'import

def start_mqtt_listener(topic, mode="update"):
    def run_sub():
        client_id = f"flask-mqtt-{random.randint(0, 9999)}"
        sub(client_id, topic, mode)

    mqtt_thread = threading.Thread(target=run_sub)
    mqtt_thread.daemon = True
    mqtt_thread.start()
