#!/bin/bash
set -e

# --- Configuration ---
INSTALL_CLI_PATH="/usr/local/bin/ampurr"
INSTALL_GUI_PATH="/usr/local/bin/ampurr-gui"
GUI_RESOURCES_PATH="/usr/share/ampurr-gui"
ICON_PATH="/usr/share/pixmaps/ampurr-logo.png"
DESKTOP_ENTRY_PATH="/usr/share/applications/ampurr.desktop"

# --- Main Logic ---
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this script with sudo."
  exit 1
fi

echo "Uninstalling ampurr..."

# 1. Call the internal ampurr uninstaller
if [ -f "$INSTALL_CLI_PATH" ]; then
    "$INSTALL_CLI_PATH" --uninstall
fi

# 2. Remove the main executable files
rm -f "$INSTALL_CLI_PATH"
rm -f "$INSTALL_GUI_PATH"

# 3. Remove GUI resources and the .desktop file if they exist
if [ -d "$GUI_RESOURCES_PATH" ]; then
    echo "Removing GUI resources..."
    rm -rf "$GUI_RESOURCES_PATH"
fi
if [ -f "$DESKTOP_ENTRY_PATH" ]; then
    echo "Removing application menu entry..."
    rm -f "$DESKTOP_ENTRY_PATH"
fi
rm -f "$ICON_PATH"

echo ""
echo "✅ ampurr was successfully uninstalled."