# Minecraft Server Auto-Updater

Ein automatisches Update-System für Purpur-Server und Plugins auf Ubuntu.

## 🚀 Features

- **Automatische Purpur-Updates**: Hält den Server auf der neuesten Version
- **Plugin-Updates von Modrinth**: Automatische Updates für 16+ Plugins
- **Plugin-Updates von SpigotMC**: Unterstützung für SpigotMC-Ressourcen
- **Backup-System**: Sichert alte Versionen vor Updates
- **Fehlerbehandlung**: Automatische Wiederherstellung bei Problemen
- **Zeitgesteuerte Updates**: Alle 10 Stunden oder beim Serverstart
- **Logging**: Detaillierte Protokollierung aller Vorgänge

## 📁 Verzeichnisstruktur

```
/home/zfzfg/minecraftserver/purpur2/
├── purpur.jar              # Server-JAR
├── plugins/                # Aktive Plugins
├── pluginsold/            # Backup alter Plugin-Versionen
├── pluginerrors/          # Fehlerhafte Plugins & Fehlerberichte
├── updater.py             # Haupt-Update-Skript
├── start_minecraft.sh     # Server-Start mit Auto-Update
├── setup.sh               # Installations-Skript
├── uninstall_updater.sh   # Deinstallations-Skript
├── updater.log            # Update-Protokoll
└── updater_state.json     # Gespeicherter Update-Status
```

## 🔧 Installation

### Voraussetzungen

```bash
# System-Pakete installieren
sudo apt-get update
sudo apt-get install python3 python3-pip screen openjdk-21-jre-headless

# Python-Pakete installieren
pip3 install --user requests
```

### Schnellinstallation

1. Alle Dateien nach `/home/zfzfg/minecraftserver/purpur2/` kopieren
2. Setup ausführen:
```bash
cd /home/zfzfg/minecraftserver/purpur2
chmod +x setup.sh
./setup.sh
```

## 📝 Konfiguration

### Minecraft-Version ändern

In `updater.py`, Zeile ~30:
```python
"minecraft_version": "1.21.4",  # Hier Version anpassen
```

### Update-Intervall ändern

In `updater.py`, Zeile ~31:
```python
"check_interval": 36000,  # Zeit in Sekunden (36000 = 10 Stunden)
```

### Plugins hinzufügen/entfernen

#### Modrinth-Plugin hinzufügen:
```python
MODRINTH_PLUGINS = {
    "PluginName": "projekt-id",  # ID aus der Modrinth-URL
    # ...
}
```

#### SpigotMC-Plugin hinzufügen:
```python
SPIGOT_PLUGINS = {
    "PluginName": "resource-id",  # ID aus der SpigotMC-URL
    # ...
}
```

## 🎮 Verwendung

### Server starten (mit automatischem Update)
```bash
./start_minecraft.sh
```

### Manuelles Update durchführen
```bash
python3 updater.py once
```

### Update-Daemon starten
```bash
python3 updater.py daemon
```

### Server-Konsole öffnen
```bash
screen -r minecraft
```

### Server stoppen
In der Server-Konsole:
```
stop
```

## 🔄 Automatische Updates

### Option 1: Systemd-Service (empfohlen)
```bash
# Service starten
sudo systemctl start minecraft-updater

# Service aktivieren (Auto-Start)
sudo systemctl enable minecraft-updater

# Status prüfen
sudo systemctl status minecraft-updater
```

### Option 2: Cron-Job
Der Setup erstellt automatisch einen Cron-Job für Updates alle 10 Stunden.

## 📊 Überwachung

### Logs einsehen
```bash
# Update-Log
tail -f updater.log

# Server-Log
tail -f server.log
```

### Update-Status prüfen
```bash
cat updater_state.json
```

## 🛠️ Fehlerbehebung

### Plugin-Fehler
- Fehlerhafte Plugins werden automatisch nach `pluginerrors/` verschoben
- Alte Versionen werden aus `pluginsold/` wiederhergestellt
- Fehlerbeschreibungen finden sich in `pluginerrors/`

### Server startet nicht
```bash
# Prüfe Java-Version
java -version  # Sollte 21+ sein

# Prüfe Logs
tail -n 50 updater.log
tail -n 50 server.log

# Manueller Start zum Debuggen
java -Xms22G -Xmx22G -jar purpur.jar nogui
```

### Updates funktionieren nicht
```bash
# Python-Pakete neu installieren
pip3 install --user --upgrade requests

# Manuelles Update mit Debug-Ausgabe
python3 -u updater.py once
```

## 🗑️ Deinstallation

```bash
./uninstall_updater.sh
```

Dies entfernt:
- Update-Skripte
- Systemd-Service/Cron-Jobs
- Optional: Backups und Logs

Der Server und Plugins bleiben erhalten.

## 📋 Unterstützte Plugins

### Modrinth
- AxTrade
- LuckPerms
- DiscordSRV
- EssentialsX (+ Chat, Spawn)
- FancyNpcs
- GriefPrevention
- Maintenance
- Multiverse-Core
- Sit
- TAB
- ViaBackwards
- ViaVersion
- WorldEdit
- VoiceChat

### SpigotMC
- EconomyShopGUI
- PlaceholderAPI
- Skript
- WorldBorder

## ⚠️ Wichtige Hinweise

1. **Backups**: Erstelle regelmäßig manuelle Backups deiner Welt-Daten
2. **RAM-Einstellung**: Standard ist 22GB - anpassen in `start_minecraft.sh`
3. **Screen-Session**: Server läuft in Screen-Session "minecraft"
4. **Kompatibilität**: Plugins werden für die konfigurierte MC-Version heruntergeladen
5. **Rate-Limiting**: Updates haben 1 Sekunde Verzögerung zwischen Downloads

## 📞 Support

Bei Problemen:
1. Prüfe `updater.log` für detaillierte Fehlerinformationen
2. Stelle sicher, dass alle Voraussetzungen installiert sind
3. Überprüfe die Netzwerkverbindung zu Modrinth/SpigotMC
4. Kontrolliere die Dateiberechtigungen

## 📜 Lizenz

Dieses Update-System ist für den privaten Gebrauch entwickelt.
Minecraft ist eine Marke von Mojang/Microsoft.