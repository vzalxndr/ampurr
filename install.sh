#!/bin/bash
set -e

# check if systemd is the init system.
if ! command -v systemctl &> /dev/null; then
    echo "❌ error: this system does not use systemd."
    echo "ampurr's persistence feature requires systemd to work automatically on boot."
    echo "installation aborted."
    exit 1
fi

# must be run as root
if [ "$EUID" -ne 0 ]; then
  echo "error: please run this script with sudo."
  exit 1
fi

echo "installing ampurr..."

# copy the main script to a system-wide location
cp ampurr.py /usr/local/bin/ampurr
chmod +x /usr/local/bin/ampurr

# tell the script to install its systemd service
/usr/local/bin/ampurr --install

echo ""
echo "✅ ampurr was successfully installed."
echo "run 'ampurr --help' to get started."
