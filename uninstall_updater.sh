#!/bin/bash
# Deinstallationsskript für das Minecraft Server Update-System
# Pfad: /home/zfzfg/minecraftserver/purpur2/uninstall_updater.sh

SERVER_DIR="/home/zfzfg/minecraftserver/purpur2"

echo "==================================="
echo "Minecraft Updater Deinstallation"
echo "==================================="
echo ""

# Funktion für farbige Ausgabe
print_color() {
    COLOR=$1
    MESSAGE=$2
    case $COLOR in
        "red") echo -e "\033[0;31m$MESSAGE\033[0m" ;;
        "green") echo -e "\033[0;32m$MESSAGE\033[0m" ;;
        "yellow") echo -e "\033[0;33m$MESSAGE\033[0m" ;;
        *) echo "$MESSAGE" ;;
    esac
}

# Bestätigung einholen
read -p "Möchten Sie das Update-System wirklich deinstallieren? (j/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Jj]$ ]]; then
    print_color "yellow" "Deinstallation abgebrochen."
    exit 0
fi

echo ""
print_color "yellow" "Starte Deinstallation..."
echo ""

# Stoppe laufende Update-Prozesse
print_color "yellow" "Stoppe laufende Update-Prozesse..."
pkill -f "updater.py" 2>/dev/null
if [ $? -eq 0 ]; then
    print_color "green" "✓ Update-Prozesse gestoppt"
else
    print_color "green" "✓ Keine laufenden Update-Prozesse gefunden"
fi

# Entferne Updater-Skript
if [ -f "$SERVER_DIR/updater.py" ]; then
    rm "$SERVER_DIR/updater.py"
    print_color "green" "✓ Updater-Skript entfernt"
else
    print_color "yellow" "⚠ Updater-Skript nicht gefunden"
fi

# Entferne Systemd-Service falls vorhanden
if [ -f "/etc/systemd/system/minecraft-updater.service" ]; then
    sudo systemctl stop minecraft-updater.service 2>/dev/null
    sudo systemctl disable minecraft-updater.service 2>/dev/null
    sudo rm /etc/systemd/system/minecraft-updater.service
    sudo systemctl daemon-reload
    print_color "green" "✓ Systemd-Service entfernt"
fi

# Entferne Cron-Job falls vorhanden
crontab -l 2>/dev/null | grep -v "updater.py" | crontab - 2>/dev/null
print_color "green" "✓ Cron-Jobs bereinigt"

# Frage ob auch die Backup-Verzeichnisse entfernt werden sollen
echo ""
read -p "Möchten Sie auch die Backup-Verzeichnisse entfernen? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    # Entferne Backup-Verzeichnisse
    if [ -d "$SERVER_DIR/pluginsold" ]; then
        rm -rf "$SERVER_DIR/pluginsold"
        print_color "green" "✓ Plugin-Backup-Verzeichnis entfernt"
    fi
    
    if [ -d "$SERVER_DIR/pluginerrors" ]; then
        rm -rf "$SERVER_DIR/pluginerrors"
        print_color "green" "✓ Plugin-Fehler-Verzeichnis entfernt"
    fi
    
    # Entferne Purpur-Backups
    rm -f "$SERVER_DIR"/purpur_backup_*.jar 2>/dev/null
    print_color "green" "✓ Purpur-Backups entfernt"
else
    print_color "yellow" "⚠ Backup-Verzeichnisse wurden beibehalten"
fi

# Frage ob Logs entfernt werden sollen
echo ""
read -p "Möchten Sie die Update-Logs entfernen? (j/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    if [ -f "$SERVER_DIR/updater.log" ]; then
        rm "$SERVER_DIR/updater.log"
        print_color "green" "✓ Update-Log entfernt"
    fi
    
    if [ -f "$SERVER_DIR/updater_state.json" ]; then
        rm "$SERVER_DIR/updater_state.json"
        print_color "green" "✓ Status-Datei entfernt"
    fi
else
    print_color "yellow" "⚠ Logs wurden beibehalten"
fi

# Stelle Original start_minecraft.sh wieder her
if [ -f "$SERVER_DIR/start_minecraft.sh.backup" ]; then
    mv "$SERVER_DIR/start_minecraft.sh.backup" "$SERVER_DIR/start_minecraft.sh"
    print_color "green" "✓ Original start_minecraft.sh wiederhergestellt"
fi

echo ""
print_color "green" "==================================="
print_color "green" "Deinstallation abgeschlossen!"
print_color "green" "==================================="
echo ""
echo "Das Update-System wurde entfernt."
echo "Der Minecraft-Server selbst wurde nicht verändert."
echo ""

# Optionaler Neustart-Hinweis
if screen -list | grep -q "minecraft"; then
    print_color "yellow" "Hinweis: Der Minecraft-Server läuft noch."
    print_color "yellow" "Ein Neustart wird empfohlen: screen -S minecraft -X stuff 'stop\n'"
fi
