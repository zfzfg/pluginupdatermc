#!/bin/bash
# ============================================
# Minecraft Server Start-Skript mit Auto-Updates
# ============================================

# Konfiguration
SERVER_DIR="/home/zfzfg/minecraftserver/purpur2"
SCREEN_NAME="minecraft"
MEMORY_MIN="2G"
MEMORY_MAX="4G"
SERVER_JAR="server.jar"
UPDATER_SCRIPT="plugin_updater.py"
LOG_FILE="$SERVER_DIR/server_start.log"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging-Funktion
log() {
    echo -e "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Prüfe ob als richtiger Benutzer
if [ "$USER" != "zfzfg" ]; then
    log "${RED}Fehler: Dieses Skript muss als Benutzer 'zfzfg' ausgeführt werden${NC}"
    log "Verwende: sudo -u zfzfg $0"
    exit 1
fi

# Wechsle ins Server-Verzeichnis
cd "$SERVER_DIR" || exit 1

# Funktion: Server Status prüfen
is_server_running() {
    screen -list | grep -q "$SCREEN_NAME"
    return $?
}

# Funktion: Updates durchführen
run_updates() {
    log "${YELLOW}Prüfe auf Updates...${NC}"
    
    # Prüfe ob Python-Umgebung existiert
    if [ ! -d "$SERVER_DIR/updater_venv" ]; then
        log "${YELLOW}Erstelle Python-Umgebung...${NC}"
        python3 -m venv updater_venv
        source updater_venv/bin/activate
        pip install requests
        deactivate
    fi
    
    # Führe Update-Check aus
    if [ -f "$SERVER_DIR/$UPDATER_SCRIPT" ]; then
        "$SERVER_DIR/updater_venv/bin/python" "$SERVER_DIR/$UPDATER_SCRIPT" --startup
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✓ Update-Check abgeschlossen${NC}"
        else
            log "${RED}✗ Fehler beim Update-Check${NC}"
        fi
    else
        log "${YELLOW}Update-Skript nicht gefunden, überspringe Updates${NC}"
    fi
}

# Funktion: Server starten
start_server() {
    if is_server_running; then
        log "${YELLOW}Server läuft bereits in Screen-Session '$SCREEN_NAME'${NC}"
        log "Verwende 'screen -r $SCREEN_NAME' um dich zu verbinden"
        return 0
    fi
    
    log "${GREEN}Starte Minecraft Server...${NC}"
    
    # Starte Server in Screen-Session
    screen -dmS "$SCREEN_NAME" java -Xms"$MEMORY_MIN" -Xmx"$MEMORY_MAX" \
        -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 \
        -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch \
        -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 \
        -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 \
        -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 \
        -Dusing.aikars.flags=https://mcflags.emc.gs \
        -Daikars.new.flags=true \
        -jar "$SERVER_JAR" nogui
    
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
    
    # Sende Stop-Befehl
    screen -S "$SCREEN_NAME" -X stuff "say Server wird in 10 Sekunden gestoppt...\n"
    sleep 10
    screen -S "$SCREEN_NAME" -X stuff "stop\n"
    
    # Warte auf Shutdown
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

# Funktion: Server neustarten
restart_server() {
    stop_server
    sleep 5
    run_updates
    start_server
}

# Hauptprogramm
main() {
    case "${1:-start}" in
        start)
            log "${GREEN}=== Minecraft Server Start ===${NC}"
            run_updates
            start_server
            ;;
        
        stop)
            log "${YELLOW}=== Minecraft Server Stop ===${NC}"
            stop_server
            ;;
        
        restart)
            log "${YELLOW}=== Minecraft Server Neustart ===${NC}"
            restart_server
            ;;
        
        update)
            log "${YELLOW}=== Manuelle Update-Prüfung ===${NC}"
            stop_server
            run_updates
            start_server
            ;;
        
        status)
            if is_server_running; then
                echo -e "${GREEN}✓ Server läuft${NC}"
                echo "Screen-Session: $SCREEN_NAME"
                echo "Verbinde mit: screen -r $SCREEN_NAME"
            else
                echo -e "${RED}✗ Server läuft nicht${NC}"
            fi
            ;;
        
        attach|console)
            if is_server_running; then
                screen -r "$SCREEN_NAME"
            else
                log "${RED}Server läuft nicht${NC}"
            fi
            ;;
        
        *)
            echo "Verwendung: $0 {start|stop|restart|update|status|attach}"
            echo ""
            echo "  start    - Startet den Server (mit Update-Check)"
            echo "  stop     - Stoppt den Server"
            echo "  restart  - Neustart mit Update-Check"
            echo "  update   - Stoppt Server, prüft Updates, startet neu"
            echo "  status   - Zeigt Server-Status"
            echo "  attach   - Verbindet zur Server-Konsole (Strg+A dann D zum Verlassen)"
            exit 1
            ;;
    esac
}

# Skript ausführen
main "$@"