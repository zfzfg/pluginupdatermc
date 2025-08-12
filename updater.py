#!/usr/bin/env python3
"""
Minecraft Server Auto-Updater für Ubuntu
Automatisches Update-System für Purpur Server und Plugins
Version 2.0 - Verbesserte Versionsprüfung und Fehlerbehandlung
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
    "minecraft_version": "1.21.4",  # Anpassbare Minecraft-Version
    "check_interval": 36000,  # 10 Stunden in Sekunden
    "log_file": "/home/zfzfg/minecraftserver/purpur2/updater.log",
    "state_file": "/home/zfzfg/minecraftserver/purpur2/updater_state.json",
    "debug_mode": True  # Debug-Modus für detaillierte Ausgaben
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
    level=logging.DEBUG if CONFIG.get("debug_mode") else logging.INFO,
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
            'User-Agent': 'MinecraftServerUpdater/2.0'
        })
        self.state = self.load_state()
        self.ensure_directories()
        
        # Initialisiere fehlende State-Strukturen
        if "plugin_versions" not in self.state:
            self.state["plugin_versions"] = {}
        if "plugin_hashes" not in self.state:
            self.state["plugin_hashes"] = {}
        if "plugin_files" not in self.state:
            self.state["plugin_files"] = {}
    
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
                    state = json.load(f)
                    logger.debug(f"State geladen: {len(state.get('plugin_versions', {}))} Plugin-Versionen")
                    return state
            except Exception as e:
                logger.error(f"Fehler beim Laden des States: {e}")
        return {"plugin_versions": {}, "plugin_hashes": {}, "plugin_files": {}, "purpur_hash": None}
    
    def save_state(self):
        """Speichert den aktuellen Zustand"""
        try:
            with open(CONFIG["state_file"], 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"State gespeichert: {len(self.state['plugin_versions'])} Plugins")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des States: {e}")
    
    def get_file_hash(self, filepath: str) -> Optional[str]:
        """Berechnet SHA256-Hash einer Datei"""
        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Fehler beim Hash-Berechnen von {filepath}: {e}")
            return None
    
    def find_plugin_file(self, plugin_name: str) -> Optional[str]:
        """Findet die aktuelle Plugin-Datei im plugins-Verzeichnis"""
        try:
            # Verschiedene Namenskonventionen prüfen
            possible_names = [
                plugin_name.lower(),
                plugin_name.replace("-", "").lower(),
                plugin_name.replace("_", "").lower(),
                plugin_name
            ]
            
            for file in os.listdir(CONFIG["plugins_dir"]):
                if not file.endswith('.jar'):
                    continue
                    
                file_lower = file.lower()
                for name in possible_names:
                    if name in file_lower:
                        full_path = os.path.join(CONFIG["plugins_dir"], file)
                        logger.debug(f"Plugin-Datei gefunden für {plugin_name}: {file}")
                        return full_path
            
            logger.debug(f"Keine Plugin-Datei gefunden für {plugin_name}")
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Suchen der Plugin-Datei für {plugin_name}: {e}")
            return None
    
    def backup_plugin(self, plugin_path: str) -> Optional[str]:
        """Sichert ein Plugin ins Old-Verzeichnis"""
        try:
            filename = os.path.basename(plugin_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{timestamp}_{filename}"
            backup_path = os.path.join(CONFIG["plugins_old_dir"], backup_name)
            shutil.copy2(plugin_path, backup_path)
            logger.info(f"Plugin gesichert: {backup_name}")
            return backup_path
        except Exception as e:
            logger.error(f"Fehler beim Backup von {plugin_path}: {e}")
            return None
    
    def restore_plugin(self, backup_path: str, plugin_name: str) -> bool:
        """Stellt ein Plugin aus dem Backup wieder her"""
        try:
            filename = os.path.basename(backup_path)
            # Entferne Timestamp aus dem Dateinamen
            if "_" in filename:
                parts = filename.split("_", 2)
                if len(parts) >= 3:
                    filename = parts[2]
            
            restore_path = os.path.join(CONFIG["plugins_dir"], filename)
            shutil.copy2(backup_path, restore_path)
            logger.info(f"Plugin wiederhergestellt: {plugin_name} -> {filename}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Wiederherstellen von {plugin_name}: {e}")
            return False
    
    def log_error(self, plugin_name: str, error_msg: str, plugin_path: str = None):
        """Protokolliert einen Plugin-Fehler"""
        try:
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
        except Exception as e:
            logger.error(f"Fehler beim Error-Logging für {plugin_name}: {e}")
    
    def update_purpur(self) -> bool:
        """Updated den Purpur-Server"""
        try:
            logger.info("Prüfe Purpur-Updates...")
            
            # Hole die neueste Version für die konfigurierte MC-Version
            url = f"https://api.purpurmc.org/v2/purpur/{CONFIG['minecraft_version']}/latest/download"
            
            # Download der JAR
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            temp_path = os.path.join(CONFIG["server_path"], "purpur_new.jar")
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Prüfe ob Update nötig ist
            new_hash = self.get_file_hash(temp_path)
            old_jar = os.path.join(CONFIG["server_path"], "purpur.jar")
            
            if new_hash and new_hash != self.state.get("purpur_hash"):
                # Backup der alten Version
                if os.path.exists(old_jar):
                    backup_path = os.path.join(CONFIG["server_path"], 
                                              f"purpur_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jar")
                    shutil.copy2(old_jar, backup_path)
                    logger.debug(f"Purpur-Backup erstellt: {backup_path}")
                
                # Ersetze mit neuer Version
                shutil.move(temp_path, old_jar)
                self.state["purpur_hash"] = new_hash
                self.save_state()
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
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            versions = response.json()
            if versions:
                # Nimm die neueste Version
                latest = versions[0]
                logger.debug(f"Modrinth neueste Version für {project_id}: {latest.get('name', 'unbekannt')}")
                return latest
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Modrinth-Version für {project_id}: {e}")
            return None
    
    def download_modrinth_plugin(self, plugin_name: str, project_id: str) -> bool:
        """Lädt ein Plugin von Modrinth herunter"""
        try:
            logger.debug(f"Prüfe Modrinth-Plugin: {plugin_name} ({project_id})")
            
            version_info = self.get_modrinth_version(project_id)
            if not version_info:
                logger.warning(f"Keine Version für {plugin_name} gefunden")
                return False
            
            # Version-ID und Dateiname extrahieren
            version_id = version_info['id']
            if not version_info.get('files'):
                logger.warning(f"Keine Dateien für {plugin_name} verfügbar")
                return False
            
            download_url = version_info['files'][0]['url']
            filename = version_info['files'][0]['filename']
            file_hash = version_info['files'][0].get('hashes', {}).get('sha256')
            
            # Prüfe ob Update nötig (basierend auf Version-ID UND Hash)
            current_version = self.state["plugin_versions"].get(plugin_name)
            current_file = self.find_plugin_file(plugin_name)
            
            logger.debug(f"{plugin_name}: Aktuelle Version={current_version}, Neue Version={version_id}")
            
            # Prüfe ob Plugin bereits aktuell ist
            if current_version == version_id and current_file:
                current_hash = self.get_file_hash(current_file)
                if current_hash == file_hash or current_hash == self.state["plugin_hashes"].get(plugin_name):
                    logger.info(f"{plugin_name} ist bereits aktuell (Version: {version_id})")
                    return False
            
            # Backup existierendes Plugin
            backup_path = None
            if current_file:
                backup_path = self.backup_plugin(current_file)
                if backup_path:
                    os.remove(current_file)
            
            # Download neues Plugin
            logger.info(f"Lade {plugin_name} herunter: {filename}")
            plugin_path = os.path.join(CONFIG["plugins_dir"], filename)
            
            response = self.session.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(plugin_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verifiziere Download
            downloaded_hash = self.get_file_hash(plugin_path)
            if not downloaded_hash:
                raise Exception("Konnte Hash der heruntergeladenen Datei nicht berechnen")
            
            # Prüfe Dateigröße
            if os.path.getsize(plugin_path) < 1024:
                raise Exception(f"Heruntergeladene Datei zu klein: {os.path.getsize(plugin_path)} bytes")
            
            # Speichere State nur bei erfolgreichem Download
            self.state["plugin_versions"][plugin_name] = version_id
            self.state["plugin_hashes"][plugin_name] = downloaded_hash
            self.state["plugin_files"][plugin_name] = filename
            self.save_state()
            
            logger.info(f"✓ {plugin_name} erfolgreich aktualisiert: {filename}")
            logger.debug(f"  Version: {version_id}, Hash: {downloaded_hash[:16]}...")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Download von {plugin_name}: {e}")
            
            # Wiederherstellen bei Fehler
            if backup_path and os.path.exists(backup_path):
                self.restore_plugin(backup_path, plugin_name)
            
            self.log_error(plugin_name, str(e))
            return False
    
    def download_spigot_plugin(self, plugin_name: str, resource_id: str) -> bool:
        """Lädt ein Plugin von SpigotMC herunter mit Hash-basierter Versionsprüfung"""
        try:
            logger.debug(f"Prüfe SpigotMC-Plugin: {plugin_name} ({resource_id})")
            
            # Finde aktuelle Plugin-Datei
            current_file = self.find_plugin_file(plugin_name)
            current_hash = None
            
            if current_file:
                current_hash = self.get_file_hash(current_file)
                logger.debug(f"{plugin_name}: Aktueller Hash={current_hash[:16] if current_hash else 'None'}...")
            
            # SpigotMC erfordert Spiget API
            # Hole zuerst Version-Info
            version_url = f"https://api.spiget.org/v2/resources/{resource_id}/versions/latest"
            try:
                version_response = self.session.get(version_url, timeout=30)
                version_data = version_response.json() if version_response.status_code == 200 else {}
                version_name = version_data.get('name', 'unbekannt')
                logger.debug(f"{plugin_name}: Neueste Version={version_name}")
            except:
                version_name = "unbekannt"
            
            # Download-URL
            download_url = f"https://api.spiget.org/v2/resources/{resource_id}/download"
            
            # Temporärer Download zum Hash-Vergleich
            temp_path = os.path.join(CONFIG["plugins_dir"], f"{plugin_name}_temp.jar")
            
            logger.info(f"Lade {plugin_name} von SpigotMC herunter...")
            response = self.session.get(download_url, stream=True, allow_redirects=True, timeout=60)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Prüfe Download
            if os.path.getsize(temp_path) < 1024:
                os.remove(temp_path)
                logger.warning(f"{plugin_name}: Download zu klein, überspringe")
                return False
            
            # Berechne Hash der neuen Datei
            new_hash = self.get_file_hash(temp_path)
            if not new_hash:
                os.remove(temp_path)
                return False
            
            logger.debug(f"{plugin_name}: Neuer Hash={new_hash[:16]}...")
            
            # Vergleiche Hashes
            stored_hash = self.state["plugin_hashes"].get(plugin_name)
            if new_hash == current_hash or new_hash == stored_hash:
                os.remove(temp_path)
                logger.info(f"{plugin_name} ist bereits aktuell (Hash unverändert)")
                return False
            
            # Backup existierendes Plugin
            backup_path = None
            if current_file:
                backup_path = self.backup_plugin(current_file)
                if backup_path:
                    os.remove(current_file)
            
            # Verschiebe neue Datei
            final_path = os.path.join(CONFIG["plugins_dir"], f"{plugin_name}.jar")
            shutil.move(temp_path, final_path)
            
            # Speichere State
            self.state["plugin_hashes"][plugin_name] = new_hash
            self.state["plugin_files"][plugin_name] = f"{plugin_name}.jar"
            # Für SpigotMC speichern wir den Hash als "Version"
            self.state["plugin_versions"][plugin_name] = f"hash_{new_hash[:16]}"
            self.save_state()
            
            logger.info(f"✓ {plugin_name} erfolgreich von SpigotMC aktualisiert")
            logger.debug(f"  Neuer Hash: {new_hash[:16]}...")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim SpigotMC-Download von {plugin_name}: {e}")
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Wiederherstellen bei Fehler
            if backup_path and os.path.exists(backup_path):
                self.restore_plugin(backup_path, plugin_name)
            
            self.log_error(plugin_name, str(e))
            return False
    
    def verify_plugin(self, plugin_path: str) -> bool:
        """Verifiziert ein Plugin (erweiterte Prüfung)"""
        try:
            # Prüfe ob Datei existiert
            if not os.path.exists(plugin_path):
                return False
            
            # Prüfe Dateigröße (sollte > 1KB sein)
            size = os.path.getsize(plugin_path)
            if size < 1024:
                logger.debug(f"Plugin zu klein: {plugin_path} ({size} bytes)")
                return False
            
            # Prüfe ob es eine JAR-Datei ist (Magic Bytes)
            with open(plugin_path, 'rb') as f:
                magic = f.read(4)
                if magic[:2] != b'PK':  # ZIP/JAR Magic Bytes
                    logger.debug(f"Keine gültige JAR-Datei: {plugin_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Plugin-Verifizierung {plugin_path}: {e}")
            return False
    
    def clean_old_backups(self, keep_count: int = 3):
        """Bereinigt alte Backup-Dateien, behält nur die neuesten"""
        try:
            for plugin_name in list(MODRINTH_PLUGINS.keys()) + list(SPIGOT_PLUGINS.keys()):
                # Finde alle Backups für dieses Plugin
                backups = []
                for file in os.listdir(CONFIG["plugins_old_dir"]):
                    if plugin_name.lower() in file.lower():
                        full_path = os.path.join(CONFIG["plugins_old_dir"], file)
                        backups.append((full_path, os.path.getmtime(full_path)))
                
                # Sortiere nach Änderungszeit
                backups.sort(key=lambda x: x[1], reverse=True)
                
                # Lösche alte Backups
                for backup_path, _ in backups[keep_count:]:
                    os.remove(backup_path)
                    logger.debug(f"Altes Backup gelöscht: {os.path.basename(backup_path)}")
                    
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen der Backups: {e}")
    
    def update_all_plugins(self):
        """Aktualisiert alle konfigurierten Plugins"""
        logger.info("=== Starte Plugin-Updates ===")
        
        success_count = 0
        fail_count = 0
        
        # Modrinth-Plugins
        logger.info(f"Prüfe {len(MODRINTH_PLUGINS)} Modrinth-Plugins...")
        for plugin_name, project_id in MODRINTH_PLUGINS.items():
            try:
                if self.download_modrinth_plugin(plugin_name, project_id):
                    success_count += 1
                time.sleep(1)  # Rate-Limiting
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei {plugin_name}: {e}")
                fail_count += 1
        
        # SpigotMC-Plugins
        logger.info(f"Prüfe {len(SPIGOT_PLUGINS)} SpigotMC-Plugins...")
        for plugin_name, resource_id in SPIGOT_PLUGINS.items():
            try:
                if self.download_spigot_plugin(plugin_name, resource_id):
                    success_count += 1
                time.sleep(1)  # Rate-Limiting
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei {plugin_name}: {e}")
                fail_count += 1
        
        # Bereinige alte Backups
        self.clean_old_backups()
        
        self.save_state()
        logger.info(f"=== Plugin-Updates abgeschlossen: {success_count} aktualisiert, {fail_count} Fehler ===")
    
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
            for i in range(60):  # Max 60 Sekunden warten
                time.sleep(1)
                if not self.is_server_running():
                    logger.info(f"Server nach {i+1} Sekunden gestoppt")
                    break
            else:
                logger.warning("Server konnte nicht rechtzeitig gestoppt werden")
    
    def start_server(self):
        """Startet den Minecraft-Server"""
        logger.info("Starte Minecraft-Server...")
        start_script = os.path.join(CONFIG["server_path"], "start_minecraft.sh")
        if os.path.exists(start_script):
            subprocess.run(['bash', start_script])
        else:
            logger.error(f"Start-Skript nicht gefunden: {start_script}")
    
    def run_update_cycle(self):
        """Führt einen kompletten Update-Zyklus durch"""
        logger.info("=== Starte Update-Zyklus ===")
        start_time = time.time()
        
        # Zeige aktuellen State
        logger.info(f"Aktueller State: {len(self.state['plugin_versions'])} Plugins registriert")
        if CONFIG.get("debug_mode"):
            logger.debug(f"Registrierte Plugins: {list(self.state['plugin_versions'].keys())}")
        
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
        
        elapsed = time.time() - start_time
        logger.info(f"=== Update-Zyklus abgeschlossen in {elapsed:.1f} Sekunden ===")
    
    def reset_state(self):
        """Setzt den State zurück (für Neuinitialisierung)"""
        logger.warning("State wird zurückgesetzt!")
        self.state = {"plugin_versions": {}, "plugin_hashes": {}, "plugin_files": {}, "purpur_hash": None}
        self.save_state()
        logger.info("State zurückgesetzt - alle Plugins werden beim nächsten Lauf als neu behandelt")
    
    def run_daemon(self):
        """Läuft als Daemon und prüft regelmäßig auf Updates"""
        logger.info("Updater-Daemon gestartet")
        logger.info(f"Update-Intervall: {CONFIG['check_interval']} Sekunden ({CONFIG['check_interval']/3600:.1f} Stunden)")
        
        # Initiale Prüfung beim Start
        self.run_update_cycle()
        
        # Endlosschleife für regelmäßige Prüfungen
        while True:
            logger.info(f"Nächste Prüfung in {CONFIG['check_interval']/3600:.1f} Stunden...")
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
        elif sys.argv[1] == "reset":
            # State zurücksetzen
            updater.reset_state()
            print("State wurde zurückgesetzt. Führe 'python3 updater.py once' aus für ein komplettes Update.")
        elif sys.argv[1] == "status":
            # Status anzeigen
            print(f"Updater Status:")
            print(f"  Plugins registriert: {len(updater.state['plugin_versions'])}")
            print(f"  Purpur-Hash: {updater.state.get('purpur_hash', 'Nicht gesetzt')[:16]}...")
            print(f"\nRegistrierte Plugins:")
            for plugin, version in updater.state['plugin_versions'].items():
                hash_val = updater.state['plugin_hashes'].get(plugin, 'Kein Hash')
                if hash_val != 'Kein Hash':
                    hash_val = hash_val[:16] + "..."
                print(f"  - {plugin}: {version[:20]}... (Hash: {hash_val})")
        else:
            print("Minecraft Server Updater v2.0")
            print("Verwendung: python3 updater.py [once|daemon|reset|status]")
            print("  once   - Einmaliger Update-Lauf")
            print("  daemon - Als Daemon mit regelmäßigen Updates")
            print("  reset  - State zurücksetzen (für Neuinitialisierung)")
            print("  status - Aktuellen Status anzeigen")
            sys.exit(1)
    else:
        # Standard: Einmaliger Lauf
        updater.run_update_cycle()

if __name__ == "__main__":
    main()
