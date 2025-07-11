#!/bin/bash
set -e

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
echo "run 'ampurr status' to get started."
