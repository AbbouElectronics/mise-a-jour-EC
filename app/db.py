
import mysql.connector
import pandas as pd


def get_equipment_by_serial(serial):
    # Simule une recherche dans une base
    return {
        "serial": serial,
        "version": "0.34.0",
        "site": "Site A",
        "gestion": "Gestion 1"
    }


"""
def get_equipments_by_site(site_name):
    try:
        cnx = mysql.connector.connect(
            user='root',
            password='V5JpC2Wbiz7QV5JpC2Wbiz7Q',
            host='37.187.134.3',
            database='campihome'
        )
        cursor = cnx.cursor(dictionary=True)

        # Récupérer l'ID du site
        cursor.execute("SELECT s_id FROM sites WHERE s_name = %s", (site_name,))
        site = cursor.fetchone()

        if not site:
            print(f"⚠️ Aucun site trouvé pour : {site_name}")
            return []

        s_id = site['s_id']

        # Récupérer les centrales du site avec nom et version
    
        #query = 
       SELECT DISTINCT cs_mqtt_client_id, cl_name, cl_version
            FROM centrales
            JOIN cac_settings ON cl_id = cs_d_id
            JOIN buildings ON cl_b_id = b_id
            JOIN sites ON b_s_id = s_id
            WHERE (cl_cac_d_id IS NOT NULL OR cs_d_type = 3)
              AND s_id = %s
        cursor.execute(query, (s_id,))
        rows = cursor.fetchall()

        cursor.close()
        cnx.close()

        return [
            {
                "serial": row["cs_mqtt_client_id"],
                "name": row["cl_name"],
                "version": row["cl_version"]
            }
            for row in rows
        ]

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des équipements pour le site '{site_name}': {e}")
        return []
"""
def get_all_sites():
    try:
        """
        cnx = mysql.connector.connect(
            user='root',
            password='V5JpC2Wbiz7QV5JpC2Wbiz7Q',
            host='37.187.134.3',
            database='campihome'
        )
        """
        cnx = mysql.connector.connect(
            user='campihome',
            password='0xyLPT5nxwk5',
            host='164.132.114.42',
            database='campihome'
        )
        cursor = cnx.cursor()

        cursor.execute("SELECT s_name FROM sites ORDER BY s_name ASC")
        rows = cursor.fetchall()

        cursor.close()
        cnx.close()

        return [row[0] for row in rows]

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des sites : {e}")
        return []

def get_equipments_by_site(site_name):
    try:
        """
        cnx = mysql.connector.connect(
            user='root',
            password='V5JpC2Wbiz7QV5JpC2Wbiz7Q',
            host='37.187.134.3',
            database='campihome'
        )
        """
        cnx = mysql.connector.connect(
            user='campihome',
            password='0xyLPT5nxwk5',
            host='164.132.114.42',
            database='campihome'
        )
        cursor = cnx.cursor(dictionary=True)

        # Récupération de l’ID du site
        cursor.execute("SELECT s_id FROM sites WHERE s_name = %s", (site_name,))
        site = cursor.fetchone()
        if not site:
            print(f"⚠️ Aucun site trouvé pour : {site_name}")
            return []

        s_id = site['s_id']
        result = []

        # 1️⃣ Récupérer les centrales EC
        query_centrales = """
            SELECT DISTINCT cs_mqtt_client_id, cl_name, cl_version
            FROM centrales
            JOIN cac_settings ON cl_id = cs_d_id
            JOIN buildings ON cl_b_id = b_id
            JOIN sites ON b_s_id = s_id
            WHERE (cl_cac_d_id IS NOT NULL OR cs_d_type = 3)
              AND s_id = %s
        """
        cursor.execute(query_centrales, (s_id,))
        for row in cursor.fetchall():
            result.append({
                "serial": row["cs_mqtt_client_id"],
                "name": row["cl_name"],
                "version": row["cl_version"],
                "type": "centrale"
            })

        # 2️⃣ Récupérer les lecteurs associés
        query_lecteurs = """
            SELECT DISTINCT pcal_vuid,cs_mqtt_client_id, pcal_name, pcal_version
            FROM pcal
            JOIN cac_settings ON pcal_cac_d_id = cs_d_id
            JOIN buildings ON pcal_b_id = b_id
            JOIN sites ON b_s_id = s_id
            JOIN centrales ON b_id=cl_b_id
            WHERE s_id = %s
        """
        cursor.execute(query_lecteurs, (s_id,))
        for row in cursor.fetchall():
            result.append({
                "serial": row["pcal_vuid"],
                "centrale_serial": row["cs_mqtt_client_id"],
                "name": row["pcal_name"],
                "version": row["pcal_version"],
                "type": "lecteur"
            })

        cursor.close()
        cnx.close()
        return result

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des équipements pour le site '{site_name}': {e}")
        return []

#  récupérer les sites à partir d'une gestion

def get_sites_by_gestion(gestion_name):
    try:
        """
        cnx = mysql.connector.connect(
            user='root',
            password='V5JpC2Wbiz7QV5JpC2Wbiz7Q',
            host='37.187.134.3',
            database='campihome'
        )
        """
        cnx = mysql.connector.connect(
            user='campihome',
            password='0xyLPT5nxwk5',
            host='164.132.114.42',
            database='campihome'
        )
        cursor = cnx.cursor(dictionary=True)

        query = """
            SELECT s_id, s_name
            FROM sites
            JOIN societies ON sites.s_st_id = societies.st_id
            WHERE societies.st_name = %s
        """
        cursor.execute(query, (gestion_name,))
        results = cursor.fetchall()

        cursor.close()
        cnx.close()

        return results

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des sites de la gestion '{gestion_name}': {e}")
        return []


# récupérer tous les équipements associés à une gestion
"""
def get_equipments_by_gestion(gestion_name):
    try:
        sites = get_sites_by_gestion(gestion_name)
        if not sites:
            return []

        site_ids = tuple(site['s_id'] for site in sites)

        if not site_ids:
            return []

        cnx = mysql.connector.connect(
            user='root',
            password='V5JpC2Wbiz7QV5JpC2Wbiz7Q',
            host='37.187.134.3',
            database='campihome'
        )
        cursor = cnx.cursor(dictionary=True)

        format_strings = ','.join(['%s'] * len(site_ids))
        query = f
            SELECT DISTINCT cs_mqtt_client_id, cl_name, cl_version, s_name
            FROM centrales
            JOIN cac_settings ON cl_id = cs_d_id
            JOIN buildings ON cl_b_id = b_id
            JOIN sites ON b_s_id = s_id
            WHERE (cl_cac_d_id IS NOT NULL OR cs_d_type = 3)
              AND s_id IN ({format_strings})
    

        cursor.execute(query, site_ids)
        rows = cursor.fetchall()

        cursor.close()
        cnx.close()

        return [
            {
                "site": row["s_name"],
                "serial": row["cs_mqtt_client_id"],
                "name": row["cl_name"],
                "version": row["cl_version"]
            } for row in rows
        ]

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des équipements pour la gestion '{gestion_name}': {e}")
        return []
"""

def get_equipments_by_gestion(gestion_name):
    try:
        sites = get_sites_by_gestion(gestion_name)
        if not sites:
            return []

        site_ids = tuple(site['s_id'] for site in sites)

        if not site_ids:
            return []
        """
        cnx = mysql.connector.connect(
            user='root',
            password='V5JpC2Wbiz7QV5JpC2Wbiz7Q',
            host='37.187.134.3',
            database='campihome'
        )
        """
        cnx = mysql.connector.connect(
            user='campihome',
            password='0xyLPT5nxwk5',
            host='164.132.114.42',
            database='campihome'
        )
        cursor = cnx.cursor(dictionary=True)

        format_strings = ','.join(['%s'] * len(site_ids))

        result = []

        # 1️⃣ Récupérer les centrales EC
        query_centrales = f"""
            SELECT DISTINCT cs_mqtt_client_id, cl_name, cl_version, s_name
            FROM centrales
            JOIN cac_settings ON cl_id = cs_d_id
            JOIN buildings ON cl_b_id = b_id
            JOIN sites ON b_s_id = s_id
            WHERE (cl_cac_d_id IS NOT NULL OR cs_d_type = 3)
              AND s_id IN ({format_strings})
        """
        cursor.execute(query_centrales, site_ids)
        for row in cursor.fetchall():
            result.append({
                "serial": row["cs_mqtt_client_id"],
                "name": row["cl_name"],
                "version": row["cl_version"],
                "site": row["s_name"],
                "type": "centrale"
            })

        # 2️⃣ Récupérer les lecteurs associés
        query_lecteurs = f"""
            SELECT DISTINCT cs_mqtt_client_id,pcal_vuid, pcal_name, pcal_version, s_name
            FROM pcal
            JOIN cac_settings ON pcal_cac_d_id = cs_d_id
            JOIN buildings ON pcal_b_id = b_id
            JOIN sites ON b_s_id = s_id
            WHERE s_id IN ({format_strings})
        """
        cursor.execute(query_lecteurs, site_ids)
        for row in cursor.fetchall():
            result.append({
                "serial": row["pcal_vuid"],
                "name": row["pcal_name"],
                "centrale_serial": row["cs_mqtt_client_id"],
                "version": row["pcal_version"],
                "site": row["s_name"],
                "type": "lecteur"
            })

        cursor.close()
        cnx.close()
        return result

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des équipements pour la gestion '{gestion_name}': {e}")
        return []

def get_all_gestions():
    try:
        """
        cnx = mysql.connector.connect(
            user='root',
            password='V5JpC2Wbiz7QV5JpC2Wbiz7Q',
            host='37.187.134.3',
            database='campihome'
        )
        """
        cnx = mysql.connector.connect(
            user='campihome',
            password='0xyLPT5nxwk5',
            host='164.132.114.42',
            database='campihome'
        )
        cursor = cnx.cursor()
        cursor.execute("SELECT st_name FROM societies")
        gestions = [row[0] for row in cursor.fetchall()]
        cursor.close()
        cnx.close()
        return gestions
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des gestions : {e}")
        return []
    
def get_parent_centrale_for_lecteur(lecteur_serial):
    # Exemple : tu fais une requête SQL pour retrouver la centrale associée
    pass
    return row[0] if row else None   

"""
def get_centrales_with_pcal(limit=10):
    try:
        cnx = mysql.connector.connect(
            user='api_provisioning',
            password='QPdTUdg',
            host='37.111.25.141',
            port='3307',
            database='api_provisioning_db'
        )
        cursor = cnx.cursor()

        query = 
            SELECT serial, pcal_serial 
            FROM devices 
            WHERE serial LIKE '1101-%' 
              AND pcal_serial IS NOT NULL 
              AND pcal_serial != ''
        

        if limit:
            query += " LIMIT %s"
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)

        result = []
        for row in cursor.fetchall():
            result.append({
                "centrale_serial": row[0],
                "lecteur_serial": row[1]
            })

        cursor.close()
        cnx.close()
        return result

    except Exception as e:
        print(f"[Erreur DB] {e}")
        return []

"""
def get_serials_from_csv(file_path: str, limit: int = None) -> list[tuple[str, str]]:
    import pandas as pd

    try:
        df = pd.read_csv(file_path, sep=';')
        df.columns = df.columns.str.strip()

        if 'centrale_serial' not in df.columns or 'lecteur_serial' not in df.columns:
            print(f"[Erreur CSV] Colonnes trouvées : {list(df.columns)}")
            print("[Erreur CSV] Les colonnes 'centrale_serial' et 'lecteur_serial' sont requises.")
            return []

        df = df.dropna(subset=['centrale_serial', 'lecteur_serial'])

        if limit is not None and isinstance(limit, int):
            df = df.head(limit)

        # Retourne une liste de tuples (centrale_serial, lecteur_serial)
        return list(zip(df['centrale_serial'], df['lecteur_serial']))

    except Exception as e:
        print(f"[Erreur CSV] {e}")
        return []