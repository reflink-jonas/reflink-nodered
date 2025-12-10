#!/bin/bash
# =====================================================
# REFLINK PI5 KIOSK SETUP - Kör på Pi5!
# =====================================================

echo "🚀 Sätter upp Reflink Kiosk..."

# 1. Skapa kiosk-scriptet
cat > /home/jonas/start-reflink-kiosk.sh << 'SCRIPT'
#!/bin/bash
# Vänta på Node-RED (max 30 sek)
for i in {1..30}; do 
  curl -s http://localhost:1880/dashboard > /dev/null 2>&1 && break
  sleep 1
done

# Spela intro (om den finns)
if [ -f /home/jonas/intro.mp4 ]; then
  mpv --fullscreen --no-terminal --really-quiet /home/jonas/intro.mp4 2>/dev/null || true
fi

# Starta Chromium i kiosk-läge
chromium --kiosk --no-first-run --password-store=basic \
  --disable-features=PasswordManager \
  --disable-session-crashed-bubble --noerrdialogs --disable-infobars \
  --ozone-platform=wayland --touch-events=enabled \
  http://localhost:1880/kiosk.html &
SCRIPT
chmod +x /home/jonas/start-reflink-kiosk.sh
echo "✓ Kiosk-script skapat"

# 2. Konfigurera labwc autostart
mkdir -p /home/jonas/.config/labwc
cat > /home/jonas/.config/labwc/autostart << 'AUTOSTART'
# Rotera skärm 270°
wlr-randr --output DSI-2 --transform 270 &

# Svart bakgrund (inget skrivbord)
swaybg -c '#000000' &

# Göm muspekare
unclutter -idle 0.5 &

# Starta kiosk efter kort delay
sleep 2
/home/jonas/start-reflink-kiosk.sh &
AUTOSTART
chmod +x /home/jonas/.config/labwc/autostart
echo "✓ Autostart konfigurerad"

# 3. Touch-kalibrering för 270° rotation
sudo tee /etc/udev/rules.d/99-touch-rotate.rules > /dev/null << 'UDEV'
ATTRS{name}=="11-005d Goodix Capacitive TouchScreen", ENV{LIBINPUT_CALIBRATION_MATRIX}="0 -1 1 1 0 0"
UDEV
echo "✓ Touch-kalibrering satt"

# 4. Installera unclutter om det saknas
if ! command -v unclutter &> /dev/null; then
  sudo apt update && sudo apt install -y unclutter
fi

# 5. Kopiera kiosk.html till rätt plats
if [ -f ~/.node-red/public/kiosk.html ]; then
  echo "✓ kiosk.html finns redan"
else
  echo "⚠️  kiosk.html saknas - kör: git pull"
fi

echo ""
echo "============================================"
echo "✅ KLART! Starta om Pi5 med: sudo reboot"
echo "============================================"

