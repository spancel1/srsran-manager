# srsRAN Manager

**Менеджер профилей LTE базовых станций США для srsRAN 4G**

Приложение для Windows/Linux с тёмным GUI, позволяющее хранить и редактировать реальные профили базовых вышек операторов AT&T, Verizon, T-Mobile по 7 штатам США, генерировать конфигурационные файлы srsRAN 4G и профили SIM-карт.

---

## Возможности

- **210+ профилей вышек** по 7 штатам: CO, VA, WV, OH, PA, IL, KS
- Реальные параметры: EARFCN, PCI, TAC, Band, TX Power, координаты
- **Генерация конфигов srsRAN** (`enb.conf`, `rr.conf`, `sib.conf`)
- **Профили SIM-карт** → генерация `ue.conf` с IMSI, Ki, OPc
- **Экспорт** в любую папку / деплой в WSL2 одной кнопкой
- Подсветка синтаксиса конфиг-файлов
- Полное редактирование/создание/удаление профилей

---

## Запуск на Windows

### Вариант 1 — Прямой запуск Python (GUI only)

> Это запускает только менеджер профилей. srsRAN работает внутри WSL2.

**Требования:** Python 3.11+, pip

```powershell
# Установите Python с https://python.org/downloads
# Затем в PowerShell:
cd srsran-manager
pip install -r requirements.txt
python main.py
```

### Вариант 2 — Собрать в .exe (без Python у пользователя)

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name "srsRAN-Manager" main.py
# Результат: dist\srsRAN-Manager.exe
```

---

## Сборка srsRAN 4G на Windows через WSL2

> **srsRAN 4G требует Linux.** На Windows используется WSL2 (Windows Subsystem for Linux 2).

### 1. Установка WSL2

Откройте PowerShell **от имени администратора**:

```powershell
wsl --install
# Перезагрузите ПК
# При первом запуске создайте пользователя Ubuntu
```

### 2. Установка зависимостей в WSL2 (Ubuntu)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    build-essential cmake git \
    libfftw3-dev libmbedtls-dev \
    libboost-program-options-dev libboost-system-dev \
    libboost-test-dev libboost-thread-dev \
    libconfig++-dev libsctp-dev \
    libzmq3-dev
```

> **Опционально** (для GUI графиков):
> ```bash
> sudo apt install -y libqt5charts5-dev
> ```

### 3. Клонирование и сборка srsRAN 4G

```bash
git clone https://github.com/srsRAN/srsRAN_4G.git
cd srsRAN_4G
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
srsran_install_configs.sh user
```

Конфиги установятся в `~/.config/srsran/`.

### 4. Деплой конфигов из менеджера

В приложении **srsRAN Manager**:
1. Выберите штат → выберите вышку
2. Нажмите **"Deploy to WSL2"** — конфиги скопируются в `~/.config/srsran/`

Или: **Export configs…** → сохраните в папку → скопируйте в WSL2 вручную.

### 5. Запуск srsRAN eNB

```bash
# Убедитесь что ZMQ/UHD SDR подключён или запустите в виртуальном режиме
sudo srsenb ~/.config/srsran/enb.conf

# UE (в другом терминале WSL2):
sudo srsue ~/.config/srsran/ue.conf
```

---

## Структура проекта

```
srsran-manager/
├── main.py                    # Точка входа
├── requirements.txt           # PyQt6
├── data/
│   ├── towers.json            # БД вышек по штатам
│   └── sim_profiles.json      # Профили SIM-карт
├── core/
│   ├── config_generator.py    # Генерация enb.conf / rr.conf / sib.conf / ue.conf
│   └── tower_database.py      # CRUD для вышек и SIM
└── ui/
    ├── main_window.py         # Главное окно
    ├── tower_editor.py        # Диалог редактирования вышки
    ├── sim_editor.py          # Диалог редактирования SIM
    ├── config_viewer.py       # Просмотр + экспорт конфигов
    └── styles.py              # Dark theme CSS
```

---

## Параметры профиля вышки

| Параметр | Описание |
|----------|----------|
| `enb_id` | Идентификатор eNodeB (20 бит) |
| `cell_id` | Идентификатор соты |
| `pci` | Physical Cell Identity (0–503) |
| `dl_earfcn` | Downlink EARFCN (определяет частоту) |
| `band` | LTE диапазон (2/4/5/12/13/17) |
| `n_prb` | Кол-во PRB → ширина полосы (6=1.4MHz … 100=20MHz) |
| `tac` | Tracking Area Code |
| `mcc/mnc` | MCC 310 + MNC оператора |
| `tx_power` | Мощность передачи (dBm) |

### Частоты операторов США

| Оператор | Band | EARFCN | Частота |
|----------|------|--------|---------|
| AT&T | 12 | 5010–5179 | 729 MHz |
| AT&T | 17 | 5730–5849 | 734 MHz |
| AT&T | 4 | 1475–1575 | 2110 MHz |
| Verizon | 13 | 5180–5279 | 746 MHz |
| Verizon | 4 | 1475–1575 | 2110 MHz |
| T-Mobile | 12 | 5010–5179 | 729 MHz |
| T-Mobile | 4 | 1475–1575 | 2110 MHz |
| T-Mobile | 2 | 600–1199 | 1930 MHz |

---

## Параметры SIM профиля

| Параметр | Описание |
|----------|----------|
| `imsi` | 15-значный идентификатор подписчика |
| `ki` | 128-бит ключ аутентификации (hex) |
| `opc` | 128-бит OPc оператора (hex) |
| `amf` | Authentication Management Field |
| `sqn` | Sequence Number |
| `mode` | `soft` — программная SIM, `pcsc` — физическая карта |
| `apn` | Access Point Name |

---

## Лицензия

MIT — используется исключительно в исследовательских / образовательных целях.
Работа на лицензированных частотах без разрешений FCC является незаконной.
