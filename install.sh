#!/bin/bash
# ============================================
# Minecraft Plugin Updater - Installation
# ============================================

set -e  # Beende bei Fehlern

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Konfiguration
SERVER_DIR="/home/zfzfg/minecraftserver/purpur2"
SERVER_USER="zfzfg"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Minecraft Plugin Updater Installation   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Root-Check
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Bitte als root ausführen (sudo)${NC}"
   exit 1
fi

# Schritt 1: Abhängigkeiten installieren
echo -e "${YELLOW}[1/7] Installiere System-Abhängigkeiten...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv screen wget curl

# Schritt 2: Verzeichnisse erstellen
echo -e "${YELLOW}[2/7] Erstelle Verzeichnisse...${NC}"
sudo -u $SERVER_USER mkdir -p "$SERVER_DIR/pluginsold"
sudo -u $SERVER_USER mkdir -p "$SERVER_DIR/pluginerrors"
sudo -u $SERVER_USER mkdir -p "$SERVER_DIR/server_backups"

# Schritt 3: Python Virtual Environment
echo -e "${YELLOW}[3/7] Erstelle Python-Umgebung...${NC}"
cd "$SERVER_DIR"
sudo -u $SERVER_USER python3 -m venv updater_venv
sudo -u $SERVER_USER "$SERVER_DIR/updater_venv/bin/pip" install requests

# Schritt 4: Updater-Skript erstellen
echo -e "${YELLOW}[4/7] Erstelle Update-Skripte...${NC}"

# Hier würde normalerweise das Python-Skript eingefügt werden
# Da es zu lang ist, erstellen wir einen Platzhalter
cat > "$SERVER_DIR/plugin_updater.py" << 'PYTHON_END'
# WICHTIG: Füge hier den Inhalt von "Optimiertes Plugin-Update-System" ein
# Das ist das Python-Skript aus dem ersten Artifact dieser Installation
PYTHON_END

# Server-Start-Skript
cat > "$SERVER_DIR/start.sh" << 'SCRIPT_END'
#!/bin/bash
# WICHTIG: Füge hier den Inhalt von "Server-Start Skript mit Auto-Update" ein
# Das ist das Bash-Skript aus dem zweiten Artifact
SCRIPT_END

# Berechtigungen setzen
chown $SERVER_USER:$SERVER_USER "$SERVER_DIR/plugin_updater.py"
chown $SERVER_USER:$SERVER_USER "$SERVER_DIR/start.sh"
chmod +x "$SERVER_DIR/plugin_updater.py"
chmod +x "$SERVER_DIR/start.sh"

# Schritt 5: Systemd Service erstellen
echo -e "${YELLOW}[5/7] Erstelle systemd Services...${NC}"

# Minecraft Server Service
cat > /etc/systemd/system/minecraft-server.service << 'EOF'
[Unit]
Description=Minecraft Purpur Server
After=network.target

[Service]
Type=forking
User=zfzfg
WorkingDirectory=/home/zfzfg/minecraftserver/purpur2
ExecStart=/home/zfzfg/minecraftserver/purpur2/start.sh start
ExecStop=/home/zfzfg/minecraftserver/purpur2/start.sh stop
ExecReload=/home/zfzfg/minecraftserver/purpur2/start.sh restart
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Plugin Updater Timer (alle 10 Stunden)
cat > /etc/systemd/system/minecraft-updater.service << 'EOF'
[Unit]
Description=Minecraft Plugin Updater
After=network.target

[Service]
Type=oneshot
User=zfzfg
WorkingDirectory=/home/zfzfg/minecraftserver/purpur2
ExecStart=/home/zfzfg/minecraftserver/purpur2/updater_venv/bin/python /home/zfzfg/minecraftserver/purpur2/plugin_updater.py --force
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/minecraft-updater.timer << 'EOF'
[Unit]
Description=Minecraft Plugin Updater Timer (alle 10 Stunden)
Requires=minecraft-updater.service

[Timer]
# Starte 5 Minuten nach Boot
OnBootSec=5min
# Dann alle 10 Stunden
OnUnitActiveSec=10h
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Schritt 6: Cron-Job als Alternative
echo -e "${YELLOW}[6/7] Erstelle Cron-Jobs...${NC}"

# Cron für regelmäßige Updates
cat > /etc/cron.d/minecraft-plugin-updater << 'EOF'
# Minecraft Plugin Auto-Updater
# Prüfe alle 10 Stunden auf Updates
0 */10 * * * zfzfg /home/zfzfg/minecraftserver/purpur2/updater_venv/bin/python /home/zfzfg/minecraftserver/purpur2/plugin_updater.py >> /home/zfzfg/minecraftserver/purpur2/plugin_updater.log 2>&1

# Cleanup alte Backups jeden Sonntag um 3 Uhr
0 3 * * 0 zfzfg /home/zfzfg/minecraftserver/purpur2/updater_venv/bin/python /home/zfzfg/minecraftserver/purpur2/plugin_updater.py --cleanup >> /home/zfzfg/minecraftserver/purpur2/plugin_updater.log 2>&1
EOF

# Schritt 7: Hilfs-Skripte
echo -e "${YELLOW}[7/7] Erstelle Hilfs-Skripte...${NC}"

# Update-Wrapper für manuelle Updates
cat > "$SERVER_DIR/update_now.sh" << 'EOF'
#!/bin/bash
# Manuelle Update-Prüfung

echo "Stoppe Server für Updates..."
/home/zfzfg/minecraftserver/purpur2/start.sh stop

echo "Prüfe Updates..."
/home/zfzfg/minecraftserver/purpur2/updater_venv/bin/python \
    /home/zfzfg/minecraftserver/purpur2/plugin_updater.py --force

echo "Starte Server..."
/home/zfzfg/minecraftserver/purpur2/start.sh start

echo "Update abgeschlossen!"
EOF

# Log-Viewer
cat > "$SERVER_DIR/show_logs.sh" << 'EOF'
#!/bin/bash
# Zeige Update-Logs

echo "=== Letzte Plugin-Updates ==="
tail -n 50 /home/zfzfg/minecraftserver/purpur2/plugin_updater.log | grep -E "(Update|Fehler|erfolgreich)"

echo ""
echo "=== Fehlerhafte Plugins ==="
ls -la /home/zfzfg/minecraftserver/purpur2/pluginerrors/ 2>/dev/null || echo "Keine Fehler gefunden"

echo ""
echo "Für vollständige Logs: tail -f /home/zfzfg/minecraftserver/purpur2/plugin_updater.log"
EOF

# Server-Management-Skript
cat > "$SERVER_DIR/server.sh" << 'EOF'
#!/bin/bash
# Server Management Wrapper

case "$1" in
    start)
        systemctl start minecraft-server
        echo "Server gestartet"
        ;;
    stop)
        systemctl stop minecraft-server
        echo "Server gestoppt"
        ;;
    restart)
        systemctl restart minecraft-server
        echo "Server neugestartet"
        ;;
    status)
        systemctl status minecraft-server
        ;;
    console)
        screen -r minecraft
        ;;
    update)
        /home/zfzfg/minecraftserver/purpur2/update_now.sh
        ;;
    logs)
        /home/zfzfg/minecraftserver/purpur2/show_logs.sh
        ;;
    *)
        echo "Verwendung: $0 {start|stop|restart|status|console|update|logs}"
        ;;
esac
EOF

# Berechtigungen setzen
chown $SERVER_USER:$SERVER_USER "$SERVER_DIR"/*.sh
chmod +x "$SERVER_DIR"/*.sh

# Systemd neu laden
systemctl daemon-reload

# Abschluss
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Installation abgeschlossen!        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}WICHTIG: Bevor du fortfährst:${NC}"
echo -e "${YELLOW}1. Bearbeite /home/zfzfg/minecraftserver/purpur2/plugin_updater.py${NC}"
echo -e "   und füge den Python-Code aus dem ersten Artifact ein"
echo ""
echo -e "${YELLOW}2. Bearbeite /home/zfzfg/minecraftserver/purpur2/start.sh${NC}"
echo -e "   und füge den Bash-Code aus dem zweiten Artifact ein"
echo ""
echo -e "${GREEN}Verfügbare Befehle:${NC}"
echo ""
echo -e "  ${BLUE}Server starten (mit Auto-Update):${NC}"
echo -e "    sudo -u zfzfg /home/zfzfg/minecraftserver/purpur2/start.sh start"
echo ""
echo -e "  ${BLUE}Als systemd Service:${NC}"
echo -e "    systemctl enable minecraft-server    # Auto-Start aktivieren"
echo -e "    systemctl start minecraft-server     # Server starten"
echo -e "    systemctl status minecraft-server    # Status anzeigen"
echo ""
echo -e "  ${BLUE}Automatische Updates aktivieren:${NC}"
echo -e "    systemctl enable minecraft-updater.timer"
echo -e "    systemctl start minecraft-updater.timer"
echo ""
echo -e "  ${BLUE}Manuelle Update-Prüfung:${NC}"
echo -e "    sudo -u zfzfg /home/zfzfg/minecraftserver/purpur2/update_now.sh"
echo ""
echo -e "  ${BLUE}Server-Konsole:${NC}"
echo -e "    sudo -u zfzfg screen -r minecraft"
echo -e "    (Verlassen mit Strg+A dann D)"
echo ""
echo -e "  ${BLUE}Logs anzeigen:${NC}"
echo -e "    tail -f /home/zfzfg/minecraftserver/purpur2/plugin_updater.log"
echo ""
echo -e "${GREEN}Quick-Start:${NC}"
echo -e "  1. nano /home/zfzfg/minecraftserver/purpur2/plugin_updater.py"
echo -e "  2. nano /home/zfzfg/minecraftserver/purpur2/start.sh"
echo -e "  3. systemctl enable minecraft-server minecraft-updater.timer"
echo -e "  4. systemctl start minecraft-server"
echo ""
echo -e "${YELLOW}Der Server startet automatisch mit Update-Prüfung!${NC}"
