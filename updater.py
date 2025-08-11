#!/usr/bin/env python3
"""
Minecraft Server Auto-Updater für Ubuntu
Automatisches Update-System für Purpur Server und Plugins
"""

import os
import sys
import json
import time
import shutil
import hashlib
import logging
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Konfiguration
CONFIG = {
    "server_path": "/home/zfzfg/minecraftserver/purpur2",
    "plugins_dir": "/home/zfzfg/minecraftserver/purpur2/plugins",
    "plugins_old_dir": "/home/zfzfg/minecraftserver/purpur2/pluginsold",
    "plugin_errors_dir": "/home/zfzfg/minecraftserver/purpur2/pluginerrors",
    "minecraft_version": "1.21.8",  # Anpassbare Minecraft-Version
    "check_interval": 36000,  # 10 Stunden in Sekunden
    "log_file": "/home/zfzfg/minecraftserver/purpur2/updater.log",
    "state_file": "/home/zfzfg/minecraftserver/purpur2/updater_state.json"
}

# Plugin-Liste mit Modrinth-IDs
MODRINTH_PLUGINS = {
    "AxTrade": "nZSk44a8",
    "LuckPerms": "Vebnzrzj",
    "DiscordSRV": "UmLGoGij",
    "EssentialsX": "hXiIvTyT",
    "EssentialsX-Chat": "2qgyQbO1",
    "EssentialsX-Spawn": "sYpvDxGJ",
    "FancyNpcs": "EeyAn23L",
    "GriefPrevention": "O4o4mKaq",
    "Maintenance": "VCAqN1ln",
    "Multiverse-Core": "3wmN97b8",
    "Sit": "tFLdoQMh",
    "TAB": "gG7VFbG0",
    "ViaBackwards": "NpvuJQoq",
    "ViaVersion": "P1OZGk5p",
    "WorldEdit": "1u6JkXh5",
    "VoiceChat": "9eGKb6K1"
}

# SpigotMC-Plugins (Resource-IDs)
SPIGOT_PLUGINS = {
    "EconomyShopGUI": "69927",
    "PlaceholderAPI": "6245",
    "Skript": "114544",
    "WorldBorder": "111156"
}

# Logging-Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MinecraftUpdater:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MinecraftServerUpdater/1.0'
        })
        self.state = self.load_state()
        self.ensure_directories()
    
    def ensure_directories(self):
        """Erstellt alle benötigten Verzeichnisse"""
        for dir_path in [CONFIG["plugins_dir"], CONFIG["plugins_old_dir"], 
                        CONFIG["plugin_errors_dir"]]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def load_state(self) -> Dict:
        """Lädt den gespeicherten Zustand"""
        if Path(CONFIG["state_file"]).exists():
            try:
                with open(CONFIG["state_file"], 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"plugin_versions": {}, "purpur_hash": None}
    
    def save_state(self):
        """Speichert den aktuellen Zustand"""
        with open(CONFIG["state_file"], 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_file_hash(self, filepath: str) -> str:
        """Berechnet SHA256-Hash einer Datei"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def backup_plugin(self, plugin_path: str) -> str:
        """Sichert ein Plugin ins Old-Verzeichnis"""
        filename = os.path.basename(plugin_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{timestamp}_{filename}"
        backup_path = os.path.join(CONFIG["plugins_old_dir"], backup_name)
        shutil.copy2(plugin_path, backup_path)
        logger.info(f"Plugin gesichert: {backup_path}")
        return backup_path
    
    def restore_plugin(self, backup_path: str, plugin_name: str):
        """Stellt ein Plugin aus dem Backup wieder her"""
        restore_path = os.path.join(CONFIG["plugins_dir"], f"{plugin_name}.jar")
        shutil.copy2(backup_path, restore_path)
        logger.info(f"Plugin wiederhergestellt: {plugin_name}")
    
    def log_error(self, plugin_name: str, error_msg: str, plugin_path: str = None):
        """Protokolliert einen Plugin-Fehler"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = os.path.join(CONFIG["plugin_errors_dir"], 
                                 f"{timestamp}_{plugin_name}_error.txt")
        
        with open(error_file, 'w') as f:
            f.write(f"Plugin: {plugin_name}\n")
            f.write(f"Zeit: {datetime.now()}\n")
            f.write(f"Fehler: {error_msg}\n")
            f.write(f"Plugin-Pfad: {plugin_path}\n")
        
        # Verschiebe fehlerhaftes Plugin
        if plugin_path and os.path.exists(plugin_path):
            error_plugin = os.path.join(CONFIG["plugin_errors_dir"], 
                                       f"{timestamp}_{os.path.basename(plugin_path)}")
            shutil.move(plugin_path, error_plugin)
            logger.error(f"Fehlerhaftes Plugin verschoben: {error_plugin}")
    
    def update_purpur(self) -> bool:
        """Updated den Purpur-Server"""
        try:
            logger.info("Prüfe Purpur-Updates...")
            
            # Hole die neueste Version für die konfigurierte MC-Version
            url = f"https://api.purpurmc.org/v2/purpur/{CONFIG['minecraft_version']}/latest/download"
            
            # Download der JAR
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            temp_path = os.path.join(CONFIG["server_path"], "purpur_new.jar")
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Prüfe ob Update nötig ist
            new_hash = self.get_file_hash(temp_path)
            if new_hash != self.state.get("purpur_hash"):
                # Backup der alten Version
                old_jar = os.path.join(CONFIG["server_path"], "purpur.jar")
                if os.path.exists(old_jar):
                    backup_path = os.path.join(CONFIG["server_path"], 
                                              f"purpur_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jar")
                    shutil.copy2(old_jar, backup_path)
                
                # Ersetze mit neuer Version
                shutil.move(temp_path, old_jar)
                self.state["purpur_hash"] = new_hash
                logger.info(f"Purpur erfolgreich auf Version {CONFIG['minecraft_version']} aktualisiert")
                return True
            else:
                os.remove(temp_path)
                logger.info("Purpur ist bereits aktuell")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Purpur-Update: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def get_modrinth_version(self, project_id: str) -> Optional[Dict]:
        """Holt die neueste Version eines Modrinth-Plugins"""
        try:
            # API-Endpunkt für Projektversionen
            url = f"https://api.modrinth.com/v2/project/{project_id}/version"
            
            # Filter für Minecraft-Version und Loader
            params = {
                "game_versions": f'["{CONFIG["minecraft_version"]}"]',
                "loaders": '["purpur", "paper", "spigot", "bukkit"]'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            versions = response.json()
            if versions:
                # Nimm die neueste Version
                return versions[0]
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Modrinth-Version für {project_id}: {e}")
            return None
    
    def download_modrinth_plugin(self, plugin_name: str, project_id: str) -> bool:
        """Lädt ein Plugin von Modrinth herunter"""
        try:
            version_info = self.get_modrinth_version(project_id)
            if not version_info:
                logger.warning(f"Keine Version für {plugin_name} gefunden")
                return False
            
            # Prüfe ob Update nötig
            version_id = version_info['id']
            if self.state["plugin_versions"].get(plugin_name) == version_id:
                logger.info(f"{plugin_name} ist bereits aktuell")
                return False
            
            # Download-URL aus den Files
            if not version_info['files']:
                return False
            
            download_url = version_info['files'][0]['url']
            filename = version_info['files'][0]['filename']
            
            # Backup existierendes Plugin
            existing_plugin = None
            for file in os.listdir(CONFIG["plugins_dir"]):
                if plugin_name.lower() in file.lower() and file.endswith('.jar'):
                    existing_plugin = os.path.join(CONFIG["plugins_dir"], file)
                    self.backup_plugin(existing_plugin)
                    os.remove(existing_plugin)
                    break
            
            # Download neues Plugin
            plugin_path = os.path.join(CONFIG["plugins_dir"], filename)
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(plugin_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.state["plugin_versions"][plugin_name] = version_id
            logger.info(f"{plugin_name} erfolgreich aktualisiert: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Download von {plugin_name}: {e}")
            self.log_error(plugin_name, str(e))
            return False
    
    def download_spigot_plugin(self, plugin_name: str, resource_id: str) -> bool:
        """Lädt ein Plugin von SpigotMC herunter"""
        try:
            # SpigotMC erfordert Spiget API
            url = f"https://api.spiget.org/v2/resources/{resource_id}/download"
            
            # Backup existierendes Plugin
            existing_plugin = None
            for file in os.listdir(CONFIG["plugins_dir"]):
                if plugin_name.lower() in file.lower() and file.endswith('.jar'):
                    existing_plugin = os.path.join(CONFIG["plugins_dir"], file)
                    backup_path = self.backup_plugin(existing_plugin)
                    os.remove(existing_plugin)
                    break
            
            # Download neues Plugin
            plugin_path = os.path.join(CONFIG["plugins_dir"], f"{plugin_name}.jar")
            response = self.session.get(url, stream=True, allow_redirects=True)
            response.raise_for_status()
            
            with open(plugin_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Prüfe ob Download erfolgreich (Datei > 1KB)
            if os.path.getsize(plugin_path) < 1024:
                os.remove(plugin_path)
                if backup_path:
                    self.restore_plugin(backup_path, plugin_name)
                return False
            
            logger.info(f"{plugin_name} erfolgreich von SpigotMC aktualisiert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim SpigotMC-Download von {plugin_name}: {e}")
            self.log_error(plugin_name, str(e))
            return False
    
    def verify_plugin(self, plugin_path: str) -> bool:
        """Verifiziert ein Plugin (vereinfachte Prüfung)"""
        try:
            # Prüfe ob es eine gültige JAR-Datei ist
            if not os.path.exists(plugin_path):
                return False
            
            # Prüfe Dateigröße (sollte > 1KB sein)
            if os.path.getsize(plugin_path) < 1024:
                return False
            
            # Prüfe ob es eine JAR-Datei ist (Magic Bytes)
            with open(plugin_path, 'rb') as f:
                magic = f.read(4)
                if magic[:2] != b'PK':  # ZIP/JAR Magic Bytes
                    return False
            
            return True
            
        except Exception:
            return False
    
    def update_all_plugins(self):
        """Aktualisiert alle konfigurierten Plugins"""
        logger.info("Starte Plugin-Updates...")
        
        # Modrinth-Plugins
        for plugin_name, project_id in MODRINTH_PLUGINS.items():
            logger.info(f"Prüfe {plugin_name}...")
            self.download_modrinth_plugin(plugin_name, project_id)
            time.sleep(1)  # Rate-Limiting
        
        # SpigotMC-Plugins
        for plugin_name, resource_id in SPIGOT_PLUGINS.items():
            logger.info(f"Prüfe {plugin_name}...")
            self.download_spigot_plugin(plugin_name, resource_id)
            time.sleep(1)  # Rate-Limiting
        
        self.save_state()
        logger.info("Plugin-Updates abgeschlossen")
    
    def is_server_running(self) -> bool:
        """Prüft ob der Minecraft-Server läuft"""
        try:
            result = subprocess.run(['screen', '-ls'], 
                                  capture_output=True, text=True)
            return 'minecraft' in result.stdout
        except:
            return False
    
    def stop_server(self):
        """Stoppt den Minecraft-Server sanft"""
        if self.is_server_running():
            logger.info("Stoppe Minecraft-Server...")
            subprocess.run(['screen', '-S', 'minecraft', '-X', 'stuff', 'stop\n'])
            # Warte bis Server gestoppt ist
            for _ in range(60):  # Max 60 Sekunden warten
                time.sleep(1)
                if not self.is_server_running():
                    break
    
    def start_server(self):
        """Startet den Minecraft-Server"""
        logger.info("Starte Minecraft-Server...")
        start_script = os.path.join(CONFIG["server_path"], "start_minecraft.sh")
        subprocess.run(['bash', start_script])
    
    def run_update_cycle(self):
        """Führt einen kompletten Update-Zyklus durch"""
        logger.info("=== Starte Update-Zyklus ===")
        
        # Stoppe Server wenn nötig
        was_running = self.is_server_running()
        if was_running:
            self.stop_server()
        
        # Updates durchführen
        purpur_updated = self.update_purpur()
        self.update_all_plugins()
        
        # Server wieder starten wenn er lief
        if was_running:
            self.start_server()
        
        logger.info("=== Update-Zyklus abgeschlossen ===")
    
    def run_daemon(self):
        """Läuft als Daemon und prüft regelmäßig auf Updates"""
        logger.info("Updater-Daemon gestartet")
        
        # Initiale Prüfung beim Start
        self.run_update_cycle()
        
        # Endlosschleife für regelmäßige Prüfungen
        while True:
            time.sleep(CONFIG["check_interval"])
            self.run_update_cycle()

def main():
    """Hauptfunktion"""
    updater = MinecraftUpdater()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "once":
            # Einmaliger Update-Lauf
            updater.run_update_cycle()
        elif sys.argv[1] == "daemon":
            # Als Daemon laufen
            updater.run_daemon()
        else:
            print("Verwendung: python3 updater.py [once|daemon]")
            sys.exit(1)
    else:
        # Standard: Einmaliger Lauf
        updater.run_update_cycle()

if __name__ == "__main__":
    main()
