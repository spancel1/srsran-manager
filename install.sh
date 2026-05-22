#!/bin/bash
# srsRAN Manager — Linux installer
set -e

INSTALL_DIR="$HOME/srsran-manager"
SRSRAN_DIR="$HOME/srsRAN_4G"
DESKTOP_FILE="$HOME/Desktop/srsRAN-Manager.desktop"
ICON_URL="https://raw.githubusercontent.com/spancel1/srsran-manager/main/assets/icon.png"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[+]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     srsRAN Manager — Linux Installer     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Зависимости ─────────────────────────────────────────────────────────
info "Устанавливаем системные зависимости..."
sudo apt-get update -qq
sudo apt-get install -y \
    cmake build-essential git python3 python3-pip python3-venv \
    libfftw3-dev libmbedtls-dev libboost-all-dev \
    libconfig++-dev libsctp-dev libzmq3-dev \
    libsoapysdr-dev soapysdr-tools limesuite liblimesuite-dev \
    libpcsclite-dev pkg-config

# ── 2. Python зависимости ──────────────────────────────────────────────────
info "Устанавливаем PyQt6..."
pip3 install --user PyQt6 2>/dev/null || pip3 install --user --break-system-packages PyQt6

# ── 3. Клонировать srsran-manager ──────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    info "Обновляем srsRAN Manager..."
    cd "$INSTALL_DIR" && git pull
else
    info "Скачиваем srsRAN Manager..."
    git clone https://github.com/spancel1/srsran-manager.git "$INSTALL_DIR"
fi

# ── 4. Собрать srsRAN_4G ───────────────────────────────────────────────────
if command -v srsenb &>/dev/null; then
    warn "srsRAN уже установлен ($(srsenb --version 2>&1 | head -1)). Пропускаем сборку."
else
    info "Клонируем srsRAN_4G..."
    if [ ! -d "$SRSRAN_DIR" ]; then
        git clone https://github.com/srsran/srsRAN_4G.git "$SRSRAN_DIR"
    fi

    info "Патчим CMakeLists.txt для совместимости с Boost 1.70+..."
    cd "$SRSRAN_DIR"
    python3 -c "
import re
with open('CMakeLists.txt','r') as f: c=f.read()
c=re.sub(r'find_package\s*\(\s*Boost[^)]*COMPONENTS[^)]*system[^)]*\)',
         'find_package(Boost CONFIG COMPONENTS program_options)',c)
c=re.sub(r'list\s*\(\s*APPEND BOOST_REQUIRED_COMPONENTS[^)]*\"system\"[^)]*\)','',c)
with open('CMakeLists.txt','w') as f: f.write(c)
"
    # Отключить тесты чтобы не мешали
    find . -name 'CMakeLists.txt' -exec sed -i 's/add_subdirectory(test)/# add_subdirectory(test)/g' {} \;

    mkdir -p build && cd build
    info "Запускаем cmake..."
    cmake .. -DCMAKE_BUILD_TYPE=Release \
             -DCMAKE_C_FLAGS="-Wno-error" \
             -DCMAKE_CXX_FLAGS="-Wno-error" | tail -5

    info "Собираем srsRAN (это займёт 5-10 минут)..."
    make -j$(nproc)
    sudo make install
    sudo ldconfig
    info "srsRAN установлен!"
fi

# ── 5. Иконка ──────────────────────────────────────────────────────────────
ICON_PATH="$INSTALL_DIR/assets/icon.png"
mkdir -p "$INSTALL_DIR/assets"
if [ ! -f "$ICON_PATH" ]; then
    # Создаём простую иконку через Python если нет
    python3 -c "
try:
    from urllib.request import urlretrieve
    urlretrieve('$ICON_URL', '$ICON_PATH')
except:
    pass
" 2>/dev/null || true
fi

# Если иконки нет — используем системную
if [ ! -f "$ICON_PATH" ]; then
    ICON_PATH="utilities-terminal"
fi

# ── 6. Ярлык на рабочем столе ──────────────────────────────────────────────
info "Создаём ярлык на рабочем столе..."
mkdir -p "$HOME/Desktop"

PYTHON_BIN=$(which python3)

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=srsRAN Manager
GenericName=LTE Base Station Manager
Comment=Manage US LTE base station profiles and srsRAN configs
Exec=bash -c "cd $INSTALL_DIR && $PYTHON_BIN main.py"
Icon=$ICON_PATH
Terminal=false
Categories=Network;HamRadio;Science;
Keywords=LTE;SDR;srsRAN;LimeSDR;4G;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

# Для некоторых DE нужно доверие
if command -v gio &>/dev/null; then
    gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

# Также установить в ~/.local/share/applications
mkdir -p "$HOME/.local/share/applications"
cp "$DESKTOP_FILE" "$HOME/.local/share/applications/srsran-manager.desktop"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Установка завершена!           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
info "Ярлык создан: $DESKTOP_FILE"
info "Запуск: $PYTHON_BIN $INSTALL_DIR/main.py"
echo ""
echo "  Или дважды кликни на ярлык 'srsRAN Manager' на рабочем столе."
echo ""
