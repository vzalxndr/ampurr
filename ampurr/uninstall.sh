#!/bin/bash
set -e

# must be run as root
if [ "$EUID" -ne 0 ]; then
  echo "error: please run this script with sudo."
  exit 1
fi

echo "uninstalling ampurr..."

# tell the script to uninstall its systemd service and reset the limit
if [ -f "/usr/local/bin/ampurr" ]; then
    /usr/local/bin/ampurr --uninstall
fi

# remove the config file
if [ -f "/etc/ampurr.conf" ]; then
    echo "removing config file..."
    rm -f "/etc/ampurr.conf"
fi

# remove the main script itself
echo "removing main script..."
rm -f "/usr/local/bin/ampurr"

echo ""
echo "✅ ampurr was successfully uninstalled."
