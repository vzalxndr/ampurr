#!/bin/bash
set -e

# --- Configuration ---
INSTALL_CLI_PATH="/usr/local/bin/ampurr"
INSTALL_GUI_PATH="/usr/local/bin/ampurr-gui"
GUI_RESOURCES_PATH="/usr/share/ampurr-gui"
ICON_PATH="/usr/share/pixmaps/ampurr-logo.png"
DESKTOP_ENTRY_PATH="/usr/share/applications/ampurr.desktop"

# --- Functions ---
check_root() {
  if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: Please run this script with sudo."
    exit 1
  fi
}

check_systemd() {
  if ! command -v systemctl &> /dev/null; then
    echo "❌ Error: This system does not use systemd, which is required by ampurr."
    exit 1
  fi
}

install_cli() {
  echo ">>> Installing ampurr CLI..."
  cp ampurr.py "$INSTALL_CLI_PATH"
  chmod +x "$INSTALL_CLI_PATH"
  # Call the internal ampurr installer to create the systemd service
  "$INSTALL_CLI_PATH" --install
}

install_gui() {
  echo ">>> Installing ampurr GUI..."

  # 1. Copy the GUI script
  cp ampurr-gui.py "$INSTALL_GUI_PATH"
  chmod +x "$INSTALL_GUI_PATH"

  # 2. Copy resources (icons)
  mkdir -p "$GUI_RESOURCES_PATH"
  cp -r img "$GUI_RESOURCES_PATH/"
  # Important: The GUI script must know where to find the icons.
  # You will need to adjust the paths in ampurr-gui.py!
  echo "    Resource files copied to $GUI_RESOURCES_PATH"

  # 3. Copy the application icon
  cp img/logo.png "$ICON_PATH" # Assuming the main icon is logo.png

  # 4. Create the .desktop file for the applications menu
  cat > "$DESKTOP_ENTRY_PATH" <<EOL
[Desktop Entry]
Version=1.0
Name=Ampurr
Comment=Manage battery and CPU power settings
Exec=${INSTALL_GUI_PATH}
Icon=${ICON_PATH}
Terminal=false
Type=Application
Categories=System;Utility;
EOL
  echo "    Application menu entry created."
}

# --- Main Logic ---
check_root
check_systemd

# Install the CLI in all cases
install_cli

# Check for the --gui flag
if [[ " $* " == *" --gui "* ]]; then

  # --- NEW: Interactive Dependency Check ---
  echo ">>> Checking GUI dependencies..."
  MISSING_PACKAGES=()

  # Check for lm-sensors (provides the 'sensors' command)
  if ! command -v sensors &> /dev/null; then
    echo "    - 'sensors' command not found (required for sensor data)."
    MISSING_PACKAGES+=("lm-sensors")
  fi

  # Check for PyQt5
  if ! python3 -c "import PyQt5.QtCore" &> /dev/null; then
    echo "    - 'PyQt5' library not found (required for the interface)."
    MISSING_PACKAGES+=("python3-pyqt5")
  fi

  # Check for pkexec (part of policykit-1, for running commands as root)
  if ! command -v pkexec &> /dev/null; then
    echo "    - 'pkexec' command not found (required for applying settings)."
    MISSING_PACKAGES+=("policykit-1")
  fi

  # If there are missing packages, ask the user to install them
  if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo "---"
    echo "The following required packages for the GUI are missing: ${MISSING_PACKAGES[*]}"
    read -p "Do you want to try and install them now? (y/n) " -n 1 -r
    echo # Move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Updating package list (this may take a moment)..."
        apt-get update
        echo "Installing dependencies..."
        apt-get install -y "${MISSING_PACKAGES[@]}"
    else
        echo "⚠️  Skipping dependency installation. The GUI may not work correctly."
    fi
  else
    echo "    All GUI dependencies are met."
  fi
  # --- End of Dependency Check ---

  install_gui
fi

echo ""
echo "✅ ampurr was successfully installed."
echo "Run 'ampurr --help' to get started with the CLI."
if [[ " $* " == *" --gui "* ]]; then
  echo "Look for 'Ampurr' in your applications menu."
fi