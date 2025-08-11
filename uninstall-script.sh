#!/bin/bash
# ============================================
# Minecraft Plugin Updater - Deinstallation
# ============================================

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Konfiguration
SERVER_DIR="/home/zfzfg/minecraftserver/purpur2"
SERVER_USER="zfzfg"

echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
echo -e "${RED}║   Minecraft Plugin Updater Deinstallation ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
echo ""

# Root-Check
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Bitte als root ausführen (sudo)${NC}"
   exit 1
fi

# Bestätigung
echo -e "${YELLOW}WARNUNG: Dies wird folgende Komponenten entfernen:${NC}"
echo "  - Plugin Updater Skripte"
echo "  - Python Virtual Environment"
echo "  - Systemd Services und Timer"
echo "  - Cron-Jobs"
echo "  - Update-Logs"
echo ""
echo -e "${GREEN}Folgende Daten bleiben ERHALTEN:${NC}"
echo "  - Minecraft Server und Plugins"
echo "  - Plugin-Backups in pluginsold/"
echo "  - Fehlerhafte Plugins in pluginerrors/"
echo "  - Server-Backups"
echo ""
read -p "Möchtest du wirklich deinstallieren? (ja/nein): " confirm

if [ "$confirm" != "ja" ]; then
    echo "Deinstallation abgebrochen."
    exit 0
fi

echo ""
echo -e "${YELLOW}Starte Deinstallation...${NC}"

# Schritt 1: Stoppe Services
echo -e "${BLUE}[1/8] Stoppe Services...${NC}"
systemctl stop minecraft-updater.timer 2>/dev/null || true
systemctl stop minecraft-updater.service 2>/dev/null || true
systemctl disable minecraft-updater.timer 2>/dev/null || true
systemctl disable minecraft-updater.service 2>/dev/null || true

# Schritt 2: Entferne Systemd Dateien
echo -e "${BLUE}[2/8] Entferne Systemd Konfiguration...${NC}"
rm -f /etc/systemd/system/minecraft-updater.service
rm -f /etc/systemd/system/minecraft-updater.timer
rm -f /etc/systemd/system/minecraft-server.service
systemctl daemon-reload

# Schritt 3: Entferne Cron-Jobs
echo -e "${BLUE}[3/8] Entferne Cron-Jobs...${NC}"
rm -f /etc/cron.d/minecraft-plugin-updater

# Entferne auch User-Crontab Einträge
sudo -u $SERVER_USER crontab -l 2>/dev/null | grep -v "plugin_updater.py" | sudo -u $SERVER_USER crontab - 2>/dev/null || true

# Schritt 4: Entferne Python Virtual Environment
echo -e "${BLUE}[4/8] Entferne Python-Umgebung...${NC}"
rm -rf "$SERVER_DIR/updater_venv"

# Schritt 5: Entferne Updater-Skripte
echo -e "${BLUE}[5/8] Entferne Updater-Skripte...${NC}"
rm -f "$SERVER_DIR/plugin_updater.py"
rm -f "$SERVER_DIR/update_now.sh"
rm -f "$SERVER_DIR/show_logs.sh"
rm -f "$SERVER_DIR/server.sh"

# Schritt 6: Logs und State-Dateien
echo -e "${BLUE}[6/8] Entferne Logs und State-Dateien...${NC}"
read -p "Möchtest du auch die Update-Logs löschen? (ja/nein): " delete_logs
if [ "$delete_logs" == "ja" ]; then
    rm -f "$SERVER_DIR/plugin_updater.log"
    rm -f "$SERVER_DIR/server_start.log"
    rm -f "$SERVER_DIR/.updater_state.json"
    echo "  Logs gelöscht"
else
    echo "  Logs behalten"
fi

# Schritt 7: Backup-Verzeichnisse
echo -e "${BLUE}[7/8] Backup-Verzeichnisse...${NC}"
echo -e "${YELLOW}Die folgenden Verzeichnisse enthalten Backups:${NC}"
if [ -d "$SERVER_DIR/pluginsold" ]; then
    count=$(ls -1 "$SERVER_DIR/pluginsold" 2>/dev/null | wc -l)
    echo "  - pluginsold/: $count Backup-Dateien"
fi
if [ -d "$SERVER_DIR/pluginerrors" ]; then
    count=$(ls -1 "$SERVER_DIR/pluginerrors" 2>/dev/null | wc -l)
    echo "  - pluginerrors/: $count fehlerhafte Plugins"
fi
if [ -d "$SERVER_DIR/server_backups" ]; then
    count=$(ls -1 "$SERVER_DIR/server_backups" 2>/dev/null | wc -l)
    echo "  - server_backups/: $count Server-Backups"
fi

read -p "Möchtest du diese Backup-Verzeichnisse löschen? (ja/nein): " delete_backups
if [ "$delete_backups" == "ja" ]; then
    rm -rf "$SERVER_DIR/pluginsold"
    rm -rf "$SERVER_DIR/pluginerrors"
    rm -rf "$SERVER_DIR/server_backups"
    echo "  Backup-Verzeichnisse gelöscht"
else
    echo "  Backup-Verzeichnisse behalten"
fi

# Schritt 8: start_minecraft.sh wiederherstellen
echo -e "${BLUE}[8/8] Stelle originale start_minecraft.sh wieder her...${NC}"

# Prüfe ob Backup existiert
if [ -f "$SERVER_DIR/start_minecraft.sh.backup" ]; then
    mv "$SERVER_DIR/start_minecraft.sh.backup" "$SERVER_DIR/start_minecraft.sh"
    echo "  Original start_minecraft.sh wiederhergestellt"
else
    # Erstelle neue minimale Version (ohne Update-Check)
    cat > "$SERVER_DIR/start_minecraft.sh" << 'EOF'
#!/bin/bash
# Original Minecraft Server Start-Skript (ohne Updates)
cd /home/zfzfg/minecraftserver/purpur2
screen -dmS minecraft java -Xms22G -Xmx22G -jar "purpur.jar" nogui
EOF
    echo "  Neue start_minecraft.sh erstellt (ohne Update-Funktion)"
fi

chown $SERVER_USER:$SERVER_USER "$SERVER_DIR/start_minecraft.sh"
chmod +x "$SERVER_DIR/start_minecraft.sh"

# Abschluss
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      Deinstallation abgeschlossen!        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Was wurde entfernt:${NC}"
echo "  ✓ Plugin Updater System"
echo "  ✓ Python Virtual Environment"
echo "  ✓ Systemd Services und Timer"
echo "  ✓ Cron-Jobs"
if [ "$delete_logs" == "ja" ]; then
    echo "  ✓ Update-Logs"
fi
if [ "$delete_backups" == "ja" ]; then
    echo "  ✓ Backup-Verzeichnisse"
fi
echo ""
echo -e "${GREEN}Was bleibt erhalten:${NC}"
echo "  ✓ Minecraft Server"
echo "  ✓ Alle Plugins"
echo "  ✓ Server-Konfiguration"
echo "  ✓ start_minecraft.sh (ohne Update-Funktion)"
if [ "$delete_logs" != "ja" ]; then
    echo "  ✓ Update-Logs (falls vorhanden)"
fi
if [ "$delete_backups" != "ja" ]; then
    echo "  ✓ Backup-Verzeichnisse"
fi
echo ""
echo -e "${BLUE}Server kann weiterhin normal gestartet werden mit:${NC}"
echo "  sudo -u zfzfg $SERVER_DIR/start_minecraft.sh"
echo ""
echo -e "${YELLOW}Hinweis:${NC} Der Server startet jetzt ohne automatische Update-Prüfung."
