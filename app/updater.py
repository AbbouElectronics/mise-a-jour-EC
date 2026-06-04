
import time
from app.mqtt_client import publish_update_message
from mqtt_launcher import start_mqtt_listener
from app.db import get_equipment_by_serial

def check_and_update_equipment(serial, target_version):
    equipment = get_equipment_by_serial(serial)
    current_version = equipment.get("version")

    if current_version < target_version:
        # 1. Envoyer la mise à jour et récupérer le topic
        
        topic = publish_update_message(serial, target_version)

        # 2. Lancer l’écoute sur ce topic
        start_mqtt_listener(topic, mode="update")

        return {
            "success": True,
            "message": f"Mise à jour envoyée à l’équipement {serial} vers la version {target_version}"
        }
    else:
        return {
            "success": False,
            "message": f"L’équipement {serial} est déjà à jour (version actuelle : {current_version})"
        }
