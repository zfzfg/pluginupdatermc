# 🚀 Minecraft Plugin & Purpur Auto-Updater

Vollautomatisches Update-System für deinen Minecraft Server mit Purpur-Updates und Plugin-Management.

## ✨ Features

- **Automatische Purpur Server Updates** von purpurmc.org
- **Plugin-Updates** von Modrinth, GitHub und SpigotMC
- **Update-Prüfung** beim Server-Start und alle 10 Stunden
- **Automatische Backups** vor jedem Update
- **Fehlerbehandlung** mit automatischem Rollback
- **Server-Integration** mit Screen-Session Management
- **Keine mcrcon erforderlich** - verwendet Screen-Befehle

## 📦 Unterstützte Plugins

### Modrinth (vollautomatisch)
- AxTrade, LuckPerms, DiscordSRV
- EssentialsX (+ Chat, Spawn)
- FancyNpcs, GriefPrevention
- Maintenance, Multiverse-Core
- sit, TAB, ViaBackwards, ViaVersion
- WorldEdit, VoiceChat

### SpigotMC (Info-Only)
- EconomyShopGUI, PlaceholderAPI
- Skript, WorldBorder, ServerBackup

### GitHub
- Vault (Fallback)

## 🛠️ Installation

### 1. Download der Skripte

```bash
# Als root/sudo
cd /home/zfzfg/minecraftserver/purpur2

# Lade das Installations-Skript herunter
wget https://raw.githubusercontent.com/[dein-repo]/install.sh
chmod +x install.sh
sudo ./install.sh
```

### 2. Manuelle Installation

```bash
# System-Abhängigkeiten
sudo apt update
sudo apt install -y python3 python3-pip python3-venv screen

# Python-Umgebung
cd /home/zfzfg/minecraftserver/purpur2
python3 -m venv updater_venv
source updater_venv/bin/activate
pip install requests
deactivate

# Verzeichnisse erstellen
mkdir -p pluginsold pluginerrors server_backups
```

### 3. Skripte einrichten

Speichere die folgenden Dateien:
- `plugin_updater.py` - Hauptskript (aus Artifact 1)
- `start.sh` - Server-Start mit Updates (aus Artifact 2)

```bash
# Berechtigungen setzen
chmod +x plugin_updater.py start.sh
chown zfzfg:zfzfg plugin_updater.py start.sh
```

## 🎮 Verwendung

### Server starten (mit Auto-Update)
```bash
# Als Benutzer zfzfg
./start.sh start

# Oder mit systemd
sudo systemctl start minecraft-server
```

### Manuelle Update-Prüfung
```bash
# Updates prüfen und installieren
./updater_venv/bin/python plugin_updater.py --force

# Mit Server-Neustart
./start.sh update
```

### Server-Verwaltung
```bash
# Status
./start.sh status

# Stoppen
./start.sh stop

# Neustart
./start.sh restart

# Konsole öffnen
screen -r minecraft
# Verlassen mit Strg+A dann D
```

## ⚙️ Automatisierung

### Option 1: Systemd Timer (empfohlen)

```bash
# Service-Dateien erstellen
sudo nano /etc/systemd/system/minecraft-updater.service
```

```ini
[Unit]
Description=Minecraft Plugin Updater

[Service]
Type=oneshot
User=zfzfg
WorkingDirectory=/home/zfzfg/minecraftserver/purpur2
ExecStart=/home/zfzfg/minecraftserver/purpur2/updater_venv/bin/python plugin_updater.py

[Install]
WantedBy=multi-user.target
```

Timer erstellen:
```bash
sudo nano /etc/systemd/system/minecraft-updater.timer
```

```ini
[Unit]
Description=Plugin Update Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=10h
Persistent=true

[Install]
WantedBy=timers.target
```

Aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable minecraft-updater.timer
sudo systemctl start minecraft-updater.timer
```

### Option 2: Cron-Job

```bash
# Als zfzfg
crontab -e

# Alle 10 Stunden
0 */10 * * * /home/zfzfg/minecraftserver/purpur2/updater_venv/bin/python /home/zfzfg/minecraftserver/purpur2/plugin_updater.py
```

## 📁 Verzeichnisstruktur

```
/home/zfzfg/minecraftserver/purpur2/
├── server.jar           # Purpur Server
├── plugins/             # Aktive Plugins
├── pluginsold/          # Plugin-Backups
├── pluginerrors/        # Fehlerhafte Plugins
├── server_backups/      # Server JAR Backups
├── plugin_updater.py    # Update-Skript
├── start.sh             # Server-Start-Skript
├── updater_venv/        # Python Environment
├── .updater_state.json  # Update-Status
└── plugin_updater.log   # Logs
```

## 🔍 Überwachung

### Logs anzeigen
```bash
# Live-Logs
tail -f plugin_updater.log

# Letzte Updates
grep "erfolgreich\|Update\|Fehler" plugin_updater.log | tail -20

# Fehler anzeigen
ls -la pluginerrors/
```

### Status prüfen
```bash
# Timer-Status
systemctl status minecraft-updater.timer
systemctl list-timers

# Letzter Update-Check
cat .updater_state.json | python3 -m json.tool
```

## 🔧 Konfiguration

### Plugin-Liste anpassen

Bearbeite `plugin_updater.py`:
```python
PLUGINS = [
    {
        "name": "PluginName",
        "file": "Plugin-*.jar",  # Wildcard unterstützt
        "source": "modrinth",
        "project_id": "xxxxx",
        "enabled": True  # False zum Deaktivieren
    },
    # ...
]
```

### Update-Intervall ändern
```python
CONFIG = {
    "check_interval_hours": 10,  # Stunden zwischen Checks
    "announce_restart_minutes": 5,  # Ankündigung vor Restart
    # ...
}
```

## 🆘 Fehlerbehebung

### Plugin-Update fehlgeschlagen
- Alte Version wird automatisch aus `/pluginsold/` wiederhergestellt
- Fehlerhafte Version in `/pluginerrors/` mit Fehler-Log
- Prüfe `plugin_updater.log` für Details

### Server startet nicht
```bash
# Alte Plugins wiederherstellen
cp pluginsold/*.jar plugins/

# Server manuell starten
screen -dmS minecraft java -Xmx4G -jar server.jar nogui
```

### Updates funktionieren nicht
```bash
# Python-Umgebung neu erstellen
rm -rf updater_venv
python3 -m venv updater_venv
./updater_venv/bin/pip install requests

# Test-Lauf
./updater_venv/bin/python plugin_updater.py --force
```

## 📊 Update-Quellen

### Modrinth IDs finden
1. Gehe zu https://modrinth.com/plugins
2. URL-Format: `modrinth.com/plugin/[PROJECT_ID]`
3. Verwende die ID im Skript

### SpigotMC Resource IDs
1. Plugin-URL: `spigotmc.org/resources/[plugin-name].[RESOURCE_ID]/`
2. Nur die Nummer verwenden

## 🔐 Sicherheit

- **Automatische Backups** vor jedem Update
- **Validierung** aller heruntergeladenen Plugins
- **Rollback** bei Fehlern
- **Keine Root-Rechte** erforderlich
- **Screen-Session** für sicheren Server-Betrieb

## 💡 Tipps

### Nur bestimmte Plugins updaten
```python
# In plugin_updater.py
{
    "name": "PluginName",
    "enabled": False,  # Deaktiviert Updates
}
```

### Purpur-Updates deaktivieren
Entferne den `update_purpur()` Aufruf in `run_update_cycle()`

### Test ohne Server-Neustart
```bash
./updater_venv/bin/python plugin_updater.py --force
# (ohne --startup Flag startet kein Server)
```

### Backup-Retention anpassen
```python
# In plugin_updater.py
manager.cleanup_old_backups(days=14)  # 14 Tage behalten
```

## 📝 Logs & Monitoring

### Log-Level anpassen
```python
# In plugin_updater.py
logging.basicConfig(
    level=logging.DEBUG,  # Mehr Details
    # ...
)
```

### Discord-Webhooks (zukünftig)
Kann in `plugin_updater.py` erweitert werden für Benachrichtigungen.

## 🚨 Wichtige Hinweise

1. **Teste manuell** bevor du Automatisierung aktivierst
2. **Backups** werden automatisch erstellt, lösche sie regelmäßig
3. **SpigotMC** Plugins können nicht automatisch heruntergeladen werden
4. **Server-Neustart** erfolgt automatisch bei Purpur-Updates
5. **Screen-Session** heißt "minecraft" - ändere bei Bedarf

## 📞 Support

Bei Problemen prüfe:
1. `/home/zfzfg/minecraftserver/purpur2/plugin_updater.log`
2. `/home/zfzfg/minecraftserver/purpur2/pluginerrors/`
3. Server-Logs in `logs/latest.log`

---

**Version:** 2.0
**Minecraft:** 1.21.1
**Server:** Purpur
**Python:** 3.x