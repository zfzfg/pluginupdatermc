#!/bin/bash
# Setup-Skript für das Minecraft Server Update-System
# Pfad: /home/zfzfg/minecraftserver/purpur2/setup.sh

SERVER_DIR="/home/zfzfg/minecraftserver/purpur2"
MINECRAFT_VERSION="1.21.4"  # Standard-Version, kann angepasst werden

echo "======================================="
echo "Minecraft Server Updater - Installation"
echo "======================================="
echo ""

# Funktion für farbige Ausgabe
print_color() {
    COLOR=$1
    MESSAGE=$2
    case $COLOR in
        "red") echo -e "\033[0;31m$MESSAGE\033[0m" ;;
        "green") echo -e "\033[0;32m$MESSAGE\033[0m" ;;
        "yellow") echo -e "\033[0;33m$MESSAGE\033[0m" ;;
        "blue") echo -e "\033[0;34m$MESSAGE\033[0m" ;;
        *) echo "$MESSAGE" ;;
    esac
}

# Root-Prüfung
if [ "$EUID" -eq 0 ]; then
   print_color "red" "Bitte nicht als root ausführen!"
   exit 1
fi

# Prüfe Voraussetzungen
check_requirements() {
    print_color "blue" "Prüfe Systemvoraussetzungen..."
    
    # Python3
    if ! command -v python3 &> /dev/null; then
        print_color "red" "✗ Python3 nicht gefunden!"
        print_color "yellow" "  Installiere mit: sudo apt-get install python3"
        exit 1
    else
        print_color "green" "✓ Python3 gefunden"
    fi
    
    # pip3
    if ! command -v pip3 &> /dev/null; then
        print_color "red" "✗ pip3 nicht gefunden!"
        print_color "yellow" "  Installiere mit: sudo apt-get install python3-pip"
        exit 1
    else
        print_color "green" "✓ pip3 gefunden"
    fi
    
    # Screen
    if ! command -v screen &> /dev/null; then
        print_color "red" "✗ Screen nicht gefunden!"
        print_color "yellow" "  Installiere mit: sudo apt-get install screen"
        exit 1
    else
        print_color "green" "✓ Screen gefunden"
    fi
    
    # Java
    if ! command -v java &> /dev/null; then
        print_color "red" "✗ Java nicht gefunden!"
        print_color "yellow" "  Installiere mit: sudo apt-get install openjdk-21-jre-headless"
        exit 1
    else
        JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}' | cut -d'.' -f1)
        if [ "$JAVA_VERSION" -ge 21 ]; then
            print_color "green" "✓ Java $JAVA_VERSION gefunden"
        else
            print_color "yellow" "⚠ Java $JAVA_VERSION gefunden (Java 21+ empfohlen)"
        fi
    fi
}

# Installiere Python-Pakete
install_python_packages() {
    print_color "blue" "Installiere Python-Pakete..."
    pip3 install --user requests
    if [ $? -eq 0 ]; then
        print_color "green" "✓ Python-Pakete installiert"
    else
        print_color "red" "✗ Fehler bei der Installation der Python-Pakete"
        exit 1
    fi
}

# Erstelle Verzeichnisstruktur
create_directories() {
    print_color "blue" "Erstelle Verzeichnisstruktur..."
    
    mkdir -p "$SERVER_DIR/plugins"
    mkdir -p "$SERVER_DIR/pluginsold"
    mkdir -p "$SERVER_DIR/pluginerrors"
    
    print_color "green" "✓ Verzeichnisse erstellt"
}

# Konfiguriere Minecraft-Version
configure_version() {
    echo ""
    print_color "blue" "Minecraft-Version Konfiguration"
    print_color "yellow" "Aktuelle Version: $MINECRAFT_VERSION"
    read -p "Möchten Sie eine andere Version verwenden? (j/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        echo "Verfügbare Versionen: 1.21.4, 1.21.3, 1.21.1, 1.20.6, etc."
        read -p "Minecraft-Version eingeben: " NEW_VERSION
        if [ ! -z "$NEW_VERSION" ]; then
            MINECRAFT_VERSION=$NEW_VERSION
            # Update in updater.py
            sed -i "s/\"minecraft_version\": \"[^\"]*\"/\"minecraft_version\": \"$MINECRAFT_VERSION\"/" "$SERVER_DIR/updater.py"
            print_color "green" "✓ Version auf $MINECRAFT_VERSION gesetzt"
        fi
    fi
}

# Backup existierende Dateien
backup_existing() {
    print_color "blue" "Sichere existierende Konfiguration..."
    
    # Backup start_minecraft.sh falls vorhanden
    if [ -f "$SERVER_DIR/start_minecraft.sh" ]; then
        if [ ! -f "$SERVER_DIR/start_minecraft.sh.backup" ]; then
            cp "$SERVER_DIR/start_minecraft.sh" "$SERVER_DIR/start_minecraft.sh.backup"
            print_color "green" "✓ Original start_minecraft.sh gesichert"
        fi
    fi
}

# Setze Berechtigungen
set_permissions() {
    print_color "blue" "Setze Dateiberechtigungen..."
    
    chmod +x "$SERVER_DIR/start_minecraft.sh"
    chmod +x "$SERVER_DIR/setup.sh"
    chmod +x "$SERVER_DIR/uninstall_updater.sh"
    chmod +x "$SERVER_DIR/updater.py"
    
    print_color "green" "✓ Berechtigungen gesetzt"
}

# Erstelle Systemd-Service (optional)
create_systemd_service() {
    echo ""
    read -p "Möchten Sie einen Systemd-Service für automatische Updates erstellen? (j/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        print_color "blue" "Erstelle Systemd-Service..."
        
        # Service-Datei erstellen
        cat > /tmp/minecraft-updater.service << EOF
[Unit]
Description=Minecraft Server Auto-Updater
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SERVER_DIR
ExecStart=/usr/bin/python3 $SERVER_DIR/updater.py daemon
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF
        
        # Service installieren
        sudo mv /tmp/minecraft-updater.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable minecraft-updater.service
        
        print_color "green" "✓ Systemd-Service erstellt"
        print_color "yellow" "  Starte mit: sudo systemctl start minecraft-updater"
        print_color "yellow" "  Status mit: sudo systemctl status minecraft-updater"
    fi
}

# Erstelle Cron-Job (Alternative)
create_cron_job() {
    echo ""
    read -p "Möchten Sie einen Cron-Job für stündliche Updates erstellen? (j/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        print_color "blue" "Erstelle Cron-Job..."
        
        # Cron-Job hinzufügen (alle 10 Stunden)
        (crontab -l 2>/dev/null; echo "0 */10 * * * /usr/bin/python3 $SERVER_DIR/updater.py once >> $SERVER_DIR/updater.log 2>&1") | crontab -
        
        print_color "green" "✓ Cron-Job erstellt (alle 10 Stunden)"
    fi
}

# Initiales Update ausführen
run_initial_update() {
    echo ""
    read -p "Möchten Sie jetzt ein initiales Update durchführen? (j/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        print_color "blue" "Führe initiales Update durch..."
        python3 "$SERVER_DIR/updater.py" once
        
        if [ $? -eq 0 ]; then
            print_color "green" "✓ Initiales Update erfolgreich"
        else
            print_color "yellow" "⚠ Update fehlgeschlagen - prüfe updater.log"
        fi
    fi
}

# Hauptprogramm
main() {
    cd "$SERVER_DIR"
    
    # Prüfungen
    check_requirements
    
    echo ""
    print_color "blue" "Beginne Installation..."
    echo ""
    
    # Installation
    install_python_packages
    create_directories
    backup_existing
    set_permissions
    
    # Konfiguration
    configure_version
    
    # Optionale Komponenten
    create_systemd_service
    if [ $? -ne 0 ]; then
        create_cron_job
    fi
    
    # Initiales Update
    run_initial_update
    
    echo ""
    print_color "green" "======================================="
    print_color "green" "Installation erfolgreich abgeschlossen!"
    print_color "green" "======================================="
    echo ""
    
    print_color "blue" "Nächste Schritte:"
    echo "1. Server starten: ./start_minecraft.sh"
    echo "2. Updates manuell: python3 updater.py once"
    echo "3. Logs prüfen: tail -f updater.log"
    echo "4. Server-Konsole: screen -r minecraft"
    echo ""
    
    print_color "yellow" "Wichtige Dateien:"
    echo "- updater.py: Haupt-Update-Skript"
    echo "- start_minecraft.sh: Server-Start mit Auto-Update"
    echo "- uninstall_updater.sh: Deinstallation"
    echo "- updater.log: Update-Protokoll"
    echo ""
}

# Ausführung
main
