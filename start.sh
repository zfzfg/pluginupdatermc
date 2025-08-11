#!/bin/bash
# ============================================
# Minecraft Server Start-Skript mit Auto-Updates
# Übernimmt die Einstellungen der vorhandenen start_minecraft.sh
# ============================================

# Konfiguration (aus deiner vorhandenen start_minecraft.sh)
SERVER_DIR="/home/zfzfg/minecraftserver/purpur2"
SCREEN_NAME="minecraft"
MEMORY="22G"  # 22GB RAM wie in deiner Konfiguration
SERVER_JAR="purpur.jar"
UPDATER_SCRIPT="plugin_updater.py"
LOG_FILE="$SERVER_DIR/server_start.log"

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Logging
log() {
    echo -e "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# In das Verzeichnis wechseln
cd "$SERVER_DIR" || exit 1

# Funktion: Server läuft prüfen
is_server_running() {
    screen -list | grep -q "$SCREEN_NAME"
    return $?
}

# Funktion: Update-Check durchführen
check_updates() {
    log "${YELLOW}Prüfe auf Plugin und Server Updates...${NC}"
    
    # Prüfe ob Python-Umgebung existiert
    if [ ! -d "$SERVER_DIR/updater_venv" ]; then
        log "${YELLOW}Python-Umgebung nicht gefunden, überspringe Updates${NC}"
        return 0
    fi
    
    # Führe Update-Check aus (mit --startup Flag für Server-Start)
    if [ -f "$SERVER_DIR/$UPDATER_SCRIPT" ]; then
        "$SERVER_DIR/updater_venv/bin/python" "$SERVER_DIR/$UPDATER_SCRIPT" --startup 2>&1 | tee -a "$LOG_FILE"
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log "${GREEN}✓ Update-Check erfolgreich${NC}"
        else
            log "${RED}✗ Fehler beim Update-Check (Server startet trotzdem)${NC}"
        fi
    else
        log "${YELLOW}Update-Skript nicht gefunden, starte ohne Updates${NC}"
    fi
}

# Funktion: Server starten
start_server() {
    if is_server_running; then
        log "${YELLOW}Server läuft bereits in Screen-Session '$SCREEN_NAME'${NC}"
        log "Verwende 'screen -r $SCREEN_NAME' um dich zu verbinden"
        return 0
    fi
    
    log "${GREEN}Starte Minecraft Server mit 22GB RAM...${NC}"
    
    # Starte den Server genau wie in deiner vorhandenen start_minecraft.sh
    screen -dmS "$SCREEN_NAME" java -Xms"$MEMORY" -Xmx"$MEMORY" -jar "$SERVER_JAR" nogui
    
    # Warte kurz
    sleep 5
    
    if is_server_running; then
        log "${GREEN}✓ Server erfolgreich gestartet${NC}"
        log "Verbinde mit: screen -r $SCREEN_NAME"
        return 0
    else
        log "${RED}✗ Server konnte nicht gestartet werden${NC}"
        return 1
    fi
}

# Funktion: Server stoppen
stop_server() {
    if ! is_server_running; then
        log "${YELLOW}Server läuft nicht${NC}"
        return 0
    fi
    
    log "${YELLOW}Stoppe Server...${NC}"
    
    # Ankündigung im Spiel
    screen -S "$SCREEN_NAME" -X stuff "say Server wird in 10 Sekunden gestoppt...\n"
    sleep 5
    screen -S "$SCREEN_NAME" -X stuff "say 5 Sekunden...\n"
    sleep 5
    
    # Stoppe Server
    screen -S "$SCREEN_NAME" -X stuff "stop\n"
    
    # Warte auf Shutdown (max 30 Sekunden)
    local timeout=30
    while [ $timeout -gt 0 ] && is_server_running; do
        sleep 1
        ((timeout--))
    done
    
    if is_server_running; then
        log "${RED}Server reagiert nicht, erzwinge Beendigung...${NC}"
        screen -S "$SCREEN_NAME" -X quit
    fi
    
    log "${GREEN}✓ Server gestoppt${NC}"
}

# Hauptlogik
case "${1:-start}" in
    start)
        # Standard-Start mit Update-Check
        log "${GREEN}=== Minecraft Server Start ===${NC}"
        check_updates
        start_server
        ;;
    
    start-no-update)
        # Start ohne Update-Check (wie die alte start_minecraft.sh)
        log "${GREEN}=== Minecraft Server Start (ohne Updates) ===${NC}"
        start_server
        ;;
    
    stop)
        log "${YELLOW}=== Minecraft Server Stop ===${NC}"
        stop_server
        ;;
    
    restart)
        log "${YELLOW}=== Minecraft Server Neustart ===${NC}"
        stop_server
        sleep 5
        check_updates
        start_server
        ;;
    
    update)
        log "${YELLOW}=== Erzwinge Update-Prüfung ===${NC}"
        if is_server_running; then
            log "${YELLOW}Stoppe Server für Updates...${NC}"
            stop_server
            sleep 5
        fi
        check_updates
        start_server
        ;;
    
    status)
        if is_server_running; then
            echo -e "${GREEN}✓ Server läuft${NC}"
            echo "Screen-Session: $SCREEN_NAME"
            echo "RAM: $MEMORY"
            echo "Verbinde mit: screen -r $SCREEN_NAME"
        else
            echo -e "${RED}✗ Server läuft nicht${NC}"
        fi
        ;;
    
    console|attach)
        if is_server_running; then
            screen -r "$SCREEN_NAME"
        else
            log "${RED}Server läuft nicht${NC}"
        fi
        ;;
    
    *)
        echo "Verwendung: $0 {start|start-no-update|stop|restart|update|status|console}"
        echo ""
        echo "  start           - Startet Server MIT Update-Check (Standard)"
        echo "  start-no-update - Startet Server OHNE Update-Check (wie alte Version)"
        echo "  stop            - Stoppt den Server"
        echo "  restart         - Neustart mit Update-Check"
        echo "  update          - Erzwingt Update-Check mit Neustart"
        echo "  status          - Zeigt Server-Status"
        echo "  console         - Öffnet Server-Konsole (Strg+A dann D zum Verlassen)"
        exit 1
        ;;
esac

exit 0
