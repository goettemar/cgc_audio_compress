#!/bin/bash
# CGC Audio Compress - Start Script
# Wird vom CGC Launcher aufgerufen oder direkt gestartet

cd "$(dirname "$0")"

# Pruefe ob virtual environment existiert, sonst erstellen
if [ ! -f .venv/bin/activate ]; then
    echo "Erstelle virtuelle Umgebung..."
    python3 -m venv .venv
fi

# Aktiviere venv
source .venv/bin/activate

# Installiere/Aktualisiere Abhängigkeiten
MARKER=".venv/.installed"
if [ ! -f "$MARKER" ] || [ requirements.txt -nt "$MARKER" ]; then
    echo "Installiere Abhängigkeiten..."
    pip install --upgrade pip --quiet 2>/dev/null
    pip install -r requirements.txt --quiet 2>/dev/null
    touch "$MARKER"
fi

# Starte App (expliziter Pfad zum venv-Python)
export PYTHONPATH="${PWD}:${PYTHONPATH}"
exec .venv/bin/python main.py "$@"
