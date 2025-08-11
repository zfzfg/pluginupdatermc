#!/bin/bash
# Minecraft Server Start-Skript mit automatischem Update-System
# Pfad: /home/zfzfg/minecraftserver/purpur2/start_minecraft.sh

# Server-Verzeichnis
SERVER_DIR="/home/zfzfg/minecraftserver/purpur2"
UPDATER_SCRIPT="$SERVER_DIR/updater.py"
LOG_FILE="$SERVER_DIR/server.log"

# In das Server-Verzeichnis wechseln
cd "$SERVER_DIR"

# Funktion zum Protokollieren
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Prüfe ob Python3 installiert ist
if ! command -v python3 &> /dev/null; then
    log_message "FEHLER: Python3 ist nicht installiert!"
    exit 1
fi

# Installiere benötigte Python-Pakete falls nicht vorhanden
install_dependencies() {
    log_message "Prüfe Python-Abhängigkeiten..."
    python3 -c "import requests" 2>/dev/null || {
        log_message "Installiere requests..."
        pip3 install --user requests
    }
}

# Führe Updates durch bevor der Server startet
run_updates() {
    if [ -f "$UPDATER_SCRIPT" ]; then
        log_message "Führe Server- und Plugin-Updates durch..."
        python3 "$UPDATER_SCRIPT" once
        
        if [ $? -eq 0 ]; then
            log_message "Updates erfolgreich abgeschlossen"
        else
            log_message "WARNUNG: Updates fehlgeschlagen, starte trotzdem..."
        fi
    else
        log_message "WARNUNG: Updater-Skript nicht gefunden: $UPDATER_SCRIPT"
    fi
}

# Hauptprogramm
main() {
    log_message "=== Minecraft Server Start ==="
    
    # Prüfe ob Server bereits läuft
    if screen -list | grep -q "minecraft"; then
        log_message "Server läuft bereits in Screen-Session 'minecraft'"
        exit 0
    fi
    
    # Installiere Abhängigkeiten
    install_dependencies
    
    # Führe Updates durch
    run_updates
    
    # Prüfe ob purpur.jar existiert
    if [ ! -f "$SERVER_DIR/purpur.jar" ]; then
        log_message "FEHLER: purpur.jar nicht gefunden!"
        log_message "Versuche Purpur herunterzuladen..."
        python3 "$UPDATER_SCRIPT" once
        
        if [ ! -f "$SERVER_DIR/purpur.jar" ]; then
            log_message "FEHLER: Konnte purpur.jar nicht herunterladen!"
            exit 1
        fi
    fi
    
    # Starte den Minecraft-Server in einer neuen Screen-Sitzung
    log_message "Starte Minecraft-Server mit 22GB RAM..."
    screen -dmS minecraft java -Xms22G -Xmx22G -jar "purpur.jar" nogui
    
    # Warte kurz und prüfe ob Server gestartet wurde
    sleep 5
    if screen -list | grep -q "minecraft"; then
        log_message "Server erfolgreich in Screen-Session 'minecraft' gestartet"
        log_message "Verwende 'screen -r minecraft' zum Verbinden"
    else
        log_message "FEHLER: Server konnte nicht gestartet werden!"
        exit 1
    fi
    
    log_message "=== Server-Start abgeschlossen ==="
}

# Führe Hauptprogramm aus
main "$@"
