#!/usr/bin/env python3
"""
Minecraft Plugin & Server Auto-Updater für Purpur
Automatische Updates für Plugins und Purpur Server
"""

import os
import sys
import json
import shutil
import hashlib
import requests
import subprocess
import time
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# ========== KONFIGURATION ==========
CONFIG = {
    "server_dir": "/home/zfzfg/minecraftserver/purpur2",
    "plugin_dir": "/home/zfzfg/minecraftserver/purpur2/plugins",
    "backup_dir": "/home/zfzfg/minecraftserver/purpur2/pluginsold",
    "error_dir": "/home/zfzfg/minecraftserver/purpur2/pluginerrors",
    "server_backup_dir": "/home/zfzfg/minecraftserver/purpur2/server_backups",
    "server_jar": "server.jar",
    "check_interval_hours": 10,  # Alle 10 Stunden
    "minecraft_version": "1.21.1",
    "loader": "purpur",
    "modrinth_api": "https://api.modrinth.com/v2",
    "spigot_api": "https://api.spiget.org/v2",
    "purpur_api": "https://api.purpurmc.org/v2",
    "screen_name": "minecraft",
    "auto_restart_server": True,
    "announce_restart_minutes": 5
}

# ========== PLUGIN DEFINITIONEN ==========
PLUGINS = [
    # Modrinth Plugins mit korrekten IDs
    {
        "name": "AxTrade",
        "file": "AcTrade-*.jar",
        "source": "modrinth",
        "project_id": "nZSk44a8",
        "enabled": True
    },
    {
        "name": "LuckPerms",
        "file": "LuckPerms-Bukkit-*.jar",
        "source": "modrinth",
        "project_id": "Vebnzrzj",
        "enabled": True
    },
    {
        "name": "DiscordSRV",
        "file": "DiscordSRV-*.jar",
        "source": "modrinth",
        "project_id": "UmLGoGij",
        "enabled": True
    },
    {
        "name": "EssentialsX",
        "file": "EssentialsX-*.jar",
        "source": "modrinth",
        "project_id": "hXiIvTyT",
        "enabled": True
    },
    {
        "name": "EssentialsXChat",
        "file": "EssentialsXChat-*.jar",
        "source": "modrinth",
        "project_id": "2qgyQbO1",
        "enabled": True
    },
    {
        "name": "EssentialsXSpawn",
        "file": "EssentialsXSpawn-*.jar",
        "source": "modrinth",
        "project_id": "sYpvDxGJ",
        "enabled": True
    },
    {
        "name": "FancyNpcs",
        "file": "FancyNpcs-*.jar",
        "source": "modrinth",
        "project_id": "EeyAn23L",
        "enabled": True
    },
    {
        "name": "GriefPrevention",
        "file": "GriefPrevention-*.jar",
        "source": "modrinth",
        "project_id": "O4o4mKaq",
        "enabled": True
    },
    {
        "name": "Maintenance",
        "file": "Maintenance-*.jar",
        "source": "modrinth",
        "project_id": "VCAqN1ln",
        "enabled": True
    },
    {
        "name": "Multiverse-Core",
        "file": "multiverse-core-*.jar",
        "source": "modrinth",
        "project_id": "3wmN97b8",
        "enabled": True
    },
    {
        "name": "sit",
        "file": "sit-*.jar",
        "source": "modrinth",
        "project_id": "tFLdoQMh",
        "enabled": True
    },
    {
        "name": "TAB",
        "file": "TAB*.jar",
        "source": "modrinth",
        "project_id": "gG7VFbG0",
        "enabled": True
    },
    {
        "name": "ViaBackwards",
        "file": "ViaBackwards-*.jar",
        "source": "modrinth",
        "project_id": "NpvuJQoq",
        "enabled": True
    },
    {
        "name": "ViaVersion",
        "file": "ViaVersion-*.jar",
        "source": "modrinth",
        "project_id": "P1OZGk5p",
        "enabled": True
    },
    {
        "name": "WorldEdit",
        "file": "worldedit-bukkit-*.jar",
        "source": "modrinth",
        "project_id": "1u6JkXh5",
        "enabled": True
    },
    {
        "name": "VoiceChat",
        "file": "voicechat-bukkit-*.jar",
        "source": "modrinth",
        "project_id": "9eGKb6K1",
        "enabled": True
    },
    
    # SpigotMC Plugins
    {
        "name": "EconomyShopGUI",
        "file": "EconomyShopGUI-*.jar",
        "source": "spigot",
        "resource_id": "69927",
        "enabled": True
    },
    {
        "name": "PlaceholderAPI",
        "file": "PlaceholderAPI-*.jar",
        "source": "spigot",
        "resource_id": "6245",
        "enabled": True
    },
    {
        "name": "Skript",
        "file": "Skript-*.jar",
        "source": "spigot",
        "resource_id": "114544",
        "enabled": True
    },
    {
        "name": "WorldBorder",
        "file": "WorldBorder-*.jar",
        "source": "spigot",
        "resource_id": "111156",
        "enabled": True
    },
    
    # Vault von GitHub (als Fallback wenn nicht auf Modrinth)
    {
        "name": "Vault",
        "file": "Vault*.jar",
        "source": "github",
        "repo": "milkbowl/Vault",
        "enabled": True
    },
    {
        "name": "ServerBackup",
        "file": "ServerBackup-*.jar",
        "source": "spigot",
        "resource_id": "79320",
        "enabled": True
    }
]

# ========== LOGGING SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(CONFIG["server_dir"]) / 'plugin_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== UPDATE MANAGER KLASSE ==========
class MinecraftUpdateManager:
    def __init__(self):
        self.server_dir = Path(CONFIG["server_dir"])
        self.plugin_dir = Path(CONFIG["plugin_dir"])
        self.backup_dir = Path(CONFIG["backup_dir"])
        self.error_dir = Path(CONFIG["error_dir"])
        self.server_backup_dir = Path(CONFIG["server_backup_dir"])
        
        # Erstelle Verzeichnisse
        for dir_path in [self.backup_dir, self.error_dir, self.server_backup_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # HTTP Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MinecraftPluginUpdater/2.0 (Purpur Server Manager)'
        })
        
        # State-Datei für letzten Check
        self.state_file = self.server_dir / '.updater_state.json'
        self.load_state()
    
    def load_state(self):
        """Lädt den letzten Update-Status"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "last_check": 0,
                "plugin_versions": {},
                "purpur_version": None
            }
    
    def save_state(self):
        """Speichert den Update-Status"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    # ========== HILFSFUNKTIONEN ==========
    def get_file_hash(self, filepath: Path) -> str:
        """Berechnet SHA256 Hash einer Datei"""
        if not filepath.exists():
            return ""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def find_plugin_file(self, plugin: Dict) -> Optional[Path]:
        """Findet die aktuelle Plugin-Datei mit Wildcard-Unterstützung"""
        pattern = plugin["file"].replace("*", ".*")
        pattern = f"^{pattern}$"
        
        for file in self.plugin_dir.iterdir():
            if file.is_file() and re.match(pattern, file.name, re.IGNORECASE):
                return file
        return None
    
    def backup_file(self, filepath: Path, backup_type: str = "plugin") -> Optional[Path]:
        """Erstellt Backup einer Datei"""
        if not filepath.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if backup_type == "plugin":
            backup_dir = self.backup_dir
        else:
            backup_dir = self.server_backup_dir
        
        backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(filepath, backup_path)
        logger.info(f"Backup erstellt: {backup_path}")
        return backup_path
    
    def validate_jar(self, jar_path: Path) -> Tuple[bool, str]:
        """Validiert eine JAR-Datei"""
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                namelist = jar.namelist()
                
                # Prüfe auf plugin.yml oder paper-plugin.yml
                has_plugin_yml = any(name in namelist for name in ['plugin.yml', 'paper-plugin.yml'])
                
                if not has_plugin_yml:
                    return False, "Keine plugin.yml gefunden"
                
                # Lese plugin.yml
                plugin_yml_name = 'plugin.yml' if 'plugin.yml' in namelist else 'paper-plugin.yml'
                plugin_yml = jar.read(plugin_yml_name).decode('utf-8', errors='ignore')
                
                # Basis-Validierung
                if 'name:' not in plugin_yml:
                    return False, "Plugin-Name fehlt"
                if 'main:' not in plugin_yml and 'loader:' not in plugin_yml:
                    return False, "Main-Klasse/Loader fehlt"
                
                return True, "Validierung erfolgreich"
        
        except zipfile.BadZipFile:
            return False, "Ungültige JAR-Datei"
        except Exception as e:
            return False, f"Validierungsfehler: {str(e)}"
    
    # ========== PURPUR SERVER UPDATE ==========
    def check_purpur_update(self) -> Optional[Tuple[str, str, str]]:
        """Prüft auf Purpur Server Updates"""
        try:
            # Hole aktuelle Version Info
            mc_version = CONFIG["minecraft_version"]
            url = f"{CONFIG['purpur_api']}/purpur/{mc_version}/latest"
            
            response = self.session.get(url)
            if response.status_code != 200:
                logger.warning(f"Purpur API nicht erreichbar: {response.status_code}")
                return None
            
            data = response.json()
            build_number = data.get("build")
            
            if not build_number:
                return None
            
            # Download URL
            download_url = f"{CONFIG['purpur_api']}/purpur/{mc_version}/{build_number}/download"
            
            # Version String
            version = f"{mc_version}-{build_number}"
            
            # Prüfe ob bereits aktuell
            if self.state.get("purpur_version") == version:
                logger.info(f"Purpur bereits aktuell: {version}")
                return None
            
            return download_url, version, str(build_number)
        
        except Exception as e:
            logger.error(f"Fehler beim Purpur Update-Check: {e}")
            return None
    
    def update_purpur(self) -> bool:
        """Aktualisiert den Purpur Server"""
        logger.info("Prüfe Purpur Server Updates...")
        
        update_info = self.check_purpur_update()
        if not update_info:
            logger.info("Kein Purpur Update verfügbar")
            return True
        
        download_url, version, build = update_info
        logger.info(f"Purpur Update gefunden: {version}")
        
        server_jar = self.server_dir / CONFIG["server_jar"]
        temp_jar = self.server_dir / f".tmp_server_{build}.jar"
        
        try:
            # Download
            logger.info(f"Lade Purpur {version} herunter...")
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_jar, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) < 8192:  # Log alle MB
                            logger.info(f"Download: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB)")
            
            # Validiere Download
            if temp_jar.stat().st_size < 1024 * 1024:  # Mindestens 1MB
                raise ValueError("Download zu klein, vermutlich fehlerhaft")
            
            # Backup altes JAR
            if server_jar.exists():
                backup_path = self.backup_file(server_jar, "server")
                logger.info(f"Server-Backup erstellt: {backup_path}")
            
            # Ersetze Server JAR
            shutil.move(temp_jar, server_jar)
            
            # Update State
            self.state["purpur_version"] = version
            self.save_state()
            
            logger.info(f"Purpur erfolgreich auf {version} aktualisiert")
            return True
        
        except Exception as e:
            logger.error(f"Fehler beim Purpur Update: {e}")
            if temp_jar.exists():
                temp_jar.unlink()
            return False
    
    # ========== PLUGIN UPDATE FUNKTIONEN ==========
    def check_modrinth_update(self, plugin: Dict) -> Optional[Tuple[str, str, str]]:
        """Prüft Modrinth auf Updates"""
        project_id = plugin.get("project_id")
        if not project_id:
            return None
        
        try:
            # Hole Versionen für Minecraft-Version
            url = f"{CONFIG['modrinth_api']}/project/{project_id}/version"
            params = {
                "game_versions": f'["{CONFIG["minecraft_version"]}"]',
                "loaders": f'["purpur", "paper", "spigot", "bukkit"]'
            }
            
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                logger.warning(f"Modrinth API Fehler für {plugin['name']}: {response.status_code}")
                return None
            
            versions = response.json()
            if not versions:
                logger.info(f"Keine kompatible Version für {plugin['name']} gefunden")
                return None
            
            # Nimm neueste Version
            latest = versions[0]
            
            # Finde primäre Datei
            primary_file = None
            for file in latest.get("files", []):
                if file.get("primary", False):
                    primary_file = file
                    break
            
            if not primary_file and latest.get("files"):
                primary_file = latest["files"][0]
            
            if primary_file:
                return primary_file["url"], latest["version_number"], primary_file["filename"]
            
            return None
        
        except Exception as e:
            logger.error(f"Modrinth Check Fehler für {plugin['name']}: {e}")
            return None
    
    def check_github_update(self, plugin: Dict) -> Optional[Tuple[str, str, str]]:
        """Prüft GitHub auf Updates"""
        repo = plugin.get("repo")
        if not repo:
            return None
        
        try:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = self.session.get(url)
            
            if response.status_code != 200:
                return None
            
            release = response.json()
            
            # Finde passende JAR
            for asset in release.get("assets", []):
                name = asset["name"].lower()
                if name.endswith(".jar") and "source" not in name:
                    return asset["browser_download_url"], release["tag_name"], asset["name"]
            
            return None
        
        except Exception as e:
            logger.error(f"GitHub Check Fehler für {plugin['name']}: {e}")
            return None
    
    def check_spigot_update(self, plugin: Dict) -> Optional[Tuple[str, str, str]]:
        """Prüft SpigotMC auf Updates (eingeschränkt)"""
        resource_id = plugin.get("resource_id")
        if not resource_id:
            return None
        
        try:
            # SpigotMC API ist limitiert, wir können nur Version-Info holen
            url = f"{CONFIG['spigot_api']}/resources/{resource_id}/versions/latest"
            response = self.session.get(url)
            
            if response.status_code != 200:
                return None
            
            version_info = response.json()
            version = version_info.get("name", "unknown")
            
            # Generiere Info-String (Download muss manuell erfolgen)
            info_url = f"https://www.spigotmc.org/resources/{resource_id}/"
            
            logger.warning(f"SpigotMC Plugin {plugin['name']} hat Version {version}. "
                         f"Automatischer Download nicht möglich. Besuche: {info_url}")
            
            # Wir geben None zurück, da kein automatischer Download möglich ist
            return None
        
        except Exception as e:
            logger.error(f"Spigot Check Fehler für {plugin['name']}: {e}")
            return None
    
    def download_file(self, url: str, target_path: Path) -> bool:
        """Lädt eine Datei herunter"""
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
        except Exception as e:
            logger.error(f"Download-Fehler: {e}")
            return False
    
    def update_plugin(self, plugin: Dict) -> bool:
        """Aktualisiert ein einzelnes Plugin"""
        if not plugin.get("enabled", True):
            logger.debug(f"Plugin {plugin['name']} ist deaktiviert")
            return True
        
        logger.info(f"Prüfe Updates für {plugin['name']}...")
        
        # Finde aktuelle Plugin-Datei
        current_file = self.find_plugin_file(plugin)
        current_hash = self.get_file_hash(current_file) if current_file else ""
        
        # Prüfe auf Updates
        update_info = None
        
        if plugin["source"] == "modrinth":
            update_info = self.check_modrinth_update(plugin)
        elif plugin["source"] == "github":
            update_info = self.check_github_update(plugin)
        elif plugin["source"] == "spigot":
            update_info = self.check_spigot_update(plugin)
        
        if not update_info:
            logger.info(f"Kein Update für {plugin['name']} verfügbar")
            return True
        
        download_url, version, filename = update_info
        
        # Prüfe ob bereits aktuell (über State)
        if self.state["plugin_versions"].get(plugin["name"]) == version:
            logger.info(f"{plugin['name']} ist bereits auf Version {version}")
            return True
        
        logger.info(f"Update gefunden für {plugin['name']}: {version}")
        
        # Download
        temp_file = self.plugin_dir / f".tmp_{filename}"
        
        if not self.download_file(download_url, temp_file):
            logger.error(f"Download fehlgeschlagen für {plugin['name']}")
            if temp_file.exists():
                temp_file.unlink()
            return False
        
        # Validiere Plugin
        valid, error_msg = self.validate_jar(temp_file)
        
        if not valid:
            # Fehler dokumentieren
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = self.error_dir / f"{plugin['name']}_{timestamp}_error.txt"
            
            with open(error_file, 'w') as f:
                f.write(f"Plugin: {plugin['name']}\n")
                f.write(f"Version: {version}\n")
                f.write(f"Zeitpunkt: {datetime.now()}\n")
                f.write(f"Fehler: {error_msg}\n")
                f.write(f"Download-URL: {download_url}\n")
            
            # Verschiebe fehlerhaftes Plugin
            error_plugin = self.error_dir / f"{plugin['name']}_{timestamp}.jar"
            shutil.move(temp_file, error_plugin)
            
            logger.error(f"Validierung fehlgeschlagen für {plugin['name']}: {error_msg}")
            return False
        
        # Backup altes Plugin
        if current_file and current_file.exists():
            self.backup_file(current_file, "plugin")
            current_file.unlink()
        
        # Installiere neues Plugin
        final_path = self.plugin_dir / filename
        shutil.move(temp_file, final_path)
        
        # Update State
        self.state["plugin_versions"][plugin["name"]] = version
        self.save_state()
        
        logger.info(f"✓ {plugin['name']} erfolgreich auf {version} aktualisiert")
        return True
    
    def restore_plugin(self, plugin: Dict) -> bool:
        """Stellt ein Plugin aus Backup wieder her"""
        pattern = plugin["file"].replace("*", "")
        
        # Finde neuestes Backup
        backups = []
        for backup_file in self.backup_dir.iterdir():
            if pattern.lower() in backup_file.name.lower():
                backups.append(backup_file)
        
        if not backups:
            logger.warning(f"Kein Backup für {plugin['name']} gefunden")
            return False
        
        # Sortiere nach Änderungszeit
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_backup = backups[0]
        
        # Stelle wieder her
        restore_path = self.plugin_dir / latest_backup.name.rsplit('_', 1)[0] + ".jar"
        shutil.copy2(latest_backup, restore_path)
        
        logger.info(f"Backup wiederhergestellt für {plugin['name']}")
        return True
    
    # ========== SERVER MANAGEMENT ==========
    def is_server_running(self) -> bool:
        """Prüft ob der Server läuft"""
        try:
            # Prüfe Screen Session
            result = subprocess.run(
                ["screen", "-list"],
                capture_output=True,
                text=True
            )
            return CONFIG["screen_name"] in result.stdout
        except:
            return False
    
    def send_screen_command(self, command: str) -> bool:
        """Sendet Befehl an Server über Screen"""
        try:
            subprocess.run(
                ["screen", "-S", CONFIG["screen_name"], "-X", "stuff", f"{command}\n"],
                check=True
            )
            return True
        except:
            return False
    
    def announce_restart(self, minutes: int = 5):
        """Kündigt Server-Neustart an"""
        if not self.is_server_running():
            return
        
        logger.info(f"Kündige Neustart in {minutes} Minuten an...")
        
        announcements = [
            (minutes * 60, f"Server-Neustart in {minutes} Minuten für Updates!"),
            (240, "Server-Neustart in 4 Minuten!"),
            (180, "Server-Neustart in 3 Minuten!"),
            (120, "Server-Neustart in 2 Minuten! Bitte Items sichern!"),
            (60, "Server-Neustart in 1 Minute!"),
            (30, "Server-Neustart in 30 Sekunden!"),
            (10, "Server-Neustart in 10 Sekunden!"),
            (5, "Neustart in 5..."),
            (4, "4..."),
            (3, "3..."),
            (2, "2..."),
            (1, "1..."),
            (0, "Neustart jetzt!")
        ]
        
        start_time = time.time()
        for seconds, message in announcements:
            if seconds > minutes * 60:
                continue
            
            wait_until = start_time + (minutes * 60 - seconds)
            wait_time = wait_until - time.time()
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            self.send_screen_command(f"say §c§l{message}")
    
    def stop_server(self, graceful: bool = True) -> bool:
        """Stoppt den Server"""
        if not self.is_server_running():
            return True
        
        if graceful:
            self.announce_restart(CONFIG.get("announce_restart_minutes", 5))
            self.send_screen_command("save-all")
            time.sleep(5)
        
        logger.info("Stoppe Server...")
        self.send_screen_command("stop")
        
        # Warte auf Shutdown
        timeout = 60
        start = time.time()
        while self.is_server_running() and (time.time() - start) < timeout:
            time.sleep(2)
        
        return not self.is_server_running()
    
    def start_server(self) -> bool:
        """Startet den Server"""
        if self.is_server_running():
            return True
        
        logger.info("Starte Server...")
        
        try:
            # Starte in Screen Session
            os.chdir(self.server_dir)
            subprocess.run([
                "screen", "-dmS", CONFIG["screen_name"],
                "java", "-Xmx4G", "-Xms2G", "-jar", CONFIG["server_jar"], "nogui"
            ])
            
            # Warte auf Start
            time.sleep(10)
            
            return self.is_server_running()
        
        except Exception as e:
            logger.error(f"Fehler beim Server-Start: {e}")
            return False
    
    # ========== HAUPTFUNKTIONEN ==========
    def run_update_cycle(self, force: bool = False) -> bool:
        """Führt kompletten Update-Zyklus durch"""
        
        # Prüfe ob Update nötig (außer bei force oder Server-Start)
        if not force:
            last_check = self.state.get("last_check", 0)
            time_since_check = time.time() - last_check
            check_interval = CONFIG["check_interval_hours"] * 3600
            
            if time_since_check < check_interval:
                remaining_hours = (check_interval - time_since_check) / 3600
                logger.info(f"Nächster Check in {remaining_hours:.1f} Stunden")
                return True
        
        logger.info("=" * 60)
        logger.info("STARTE UPDATE-ZYKLUS")
        logger.info("=" * 60)
        
        server_was_running = self.is_server_running()
        updates_found = False
        failed_plugins = []
        
        # 1. Prüfe Purpur Updates
        purpur_updated = False
        if self.check_purpur_update():
            updates_found = True
            if server_was_running and CONFIG.get("auto_restart_server", True):
                self.stop_server(graceful=True)
                server_was_running = False
            
            if self.update_purpur():
                purpur_updated = True
                logger.info("✓ Purpur Server aktualisiert")
            else:
                logger.error("✗ Purpur Update fehlgeschlagen")
        
        # 2. Prüfe Plugin Updates
        for plugin in PLUGINS:
            if not plugin.get("enabled", True):
                continue
            
            success = self.update_plugin(plugin)
            
            if not success:
                failed_plugins.append(plugin["name"])
                # Versuche Wiederherstellung
                self.restore_plugin(plugin)
        
        # 3. Update Zeitstempel
        self.state["last_check"] = time.time()
        self.save_state()
        
        # 4. Server neu starten wenn nötig
        if purpur_updated or updates_found:
            if CONFIG.get("auto_restart_server", True) and not self.is_server_running():
                logger.info("Starte Server nach Updates...")
                if not self.start_server():
                    logger.error("Server konnte nicht gestartet werden!")
        
        # 5. Zusammenfassung
        logger.info("=" * 60)
        logger.info("UPDATE-ZYKLUS ABGESCHLOSSEN")
        if purpur_updated:
            logger.info("  Purpur: AKTUALISIERT")
        if failed_plugins:
            logger.warning(f"  Fehlerhafte Plugins: {', '.join(failed_plugins)}")
        else:
            logger.info("  Alle Plugins: OK")
        logger.info("=" * 60)
        
        return len(failed_plugins) == 0
    
    def cleanup_old_backups(self, days: int = 7):
        """Löscht alte Backups"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        for backup_dir in [self.backup_dir, self.server_backup_dir]:
            if not backup_dir.exists():
                continue
            
            for backup in backup_dir.iterdir():
                if backup.is_file() and backup.stat().st_mtime < cutoff_time:
                    backup.unlink()
                    logger.debug(f"Altes Backup gelöscht: {backup}")

# ========== HAUPTPROGRAMM ==========
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Minecraft Plugin & Server Updater')
    parser.add_argument('--force', action='store_true', help='Erzwinge Update-Check')
    parser.add_argument('--daemon', action='store_true', help='Laufe als Daemon')
    parser.add_argument('--startup', action='store_true', help='Server-Start Modus')
    parser.add_argument('--cleanup', action='store_true', help='Nur alte Backups löschen')
    
    args = parser.parse_args()
    
    manager = MinecraftUpdateManager()
    
    if args.cleanup:
        manager.cleanup_old_backups()
        logger.info("Alte Backups gelöscht")
    
    elif args.daemon:
        logger.info("Starte im Daemon-Modus...")
        logger.info(f"Check-Intervall: {CONFIG['check_interval_hours']} Stunden")
        
        while True:
            try:
                manager.run_update_cycle()
                manager.cleanup_old_backups()
                
                # Warte bis zum nächsten Check
                sleep_hours = CONFIG["check_interval_hours"]
                logger.info(f"Nächster Check in {sleep_hours} Stunden...")
                time.sleep(sleep_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("Daemon beendet")
                break
            except Exception as e:
                logger.error(f"Unerwarteter Fehler: {e}")
                time.sleep(300)  # 5 Minuten bei Fehler
    
    elif args.startup:
        logger.info("Server-Start erkannt, prüfe Updates...")
        manager.run_update_cycle(force=True)
        
        # Stelle sicher dass Server läuft
        if not manager.is_server_running():
            manager.start_server()
    
    else:
        # Einmaliger Lauf
        manager.run_update_cycle(force=args.force)
        manager.cleanup_old_backups()

if __name__ == "__main__":
    main()
