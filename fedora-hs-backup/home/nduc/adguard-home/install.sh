#!/usr/bin/env bash
# This is Quadlet Container Service Installer Template, to use this template:
# 1. Copy this file into your container project folder.
# 2. Rename it to 'install.sh' and make it executable: 'chmod +x install.sh'.
# 3. Customize this script as needed; recommended customization points are marked with '#*'.

set -e

# Determine the script's absolute directory
SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

# get script directory name which will be used as service name
SCRIPT_DIR_NAME="$(basename "$SCRIPT_DIR")"

# sanitize service name (example: My Service (v1.0)! -> My-Service-v1-0)
SERVICE_NAME=$(printf '%s\n' "$SCRIPT_DIR_NAME" | awk '{
    g=$0;
    # replace non-alnum/_/- with hyphen
    g=gensub(/[^[:alnum:]_-]+/, "-", "g", g);
    # remove leading hyphen
    g=gensub(/^-+/, "", "g", g);
    # remove trailing hyphen
    g=gensub(/-+$/, "", "g", g);
    print g
}')

# get host's default ipv4 address
__default_iface=$(ip route | grep default | head -n1 | awk '{print $5}')
HOST_IPV4=$(ip -4 addr show "$__default_iface" | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n1)

TEMPLATE_FILE="$SERVICE_NAME.container.template"
TARGET_FILE="$SERVICE_NAME.container"
ROOTLESS=true #* set to true if this container can run rootless
USE_TEMPLATE=true  #* set to true if using a .container.template file
INSTALL="cp"

echo ">>> Preparing $SERVICE_NAME Quadlet installation..."
echo "Script directory detected: $SCRIPT_DIR"

# template processing
if [[ "$USE_TEMPLATE" = "true" ]]; then
  # Ensure template exists
  if [[ ! -f "$SCRIPT_DIR/$TEMPLATE_FILE" ]]; then
    echo "Error: $TEMPLATE_FILE not found in $SCRIPT_DIR."
    exit 1
  fi
  INSTALL="mv"
  # replace %service_dir% and %host_ipv4% placeholder
  sed "s|%service_dir%|$SCRIPT_DIR|g; s|%host_ipv4%|$HOST_IPV4|g" "$SCRIPT_DIR/$TEMPLATE_FILE" \
    > "$SCRIPT_DIR/$TARGET_FILE"

  #* process more %variables% or more files here if needed
  # Detect if this is first-time setup
  CONF_DIR="$SCRIPT_DIR/conf"
  WORK_DIR="$SCRIPT_DIR/work"
  if [[ ! -d "$CONF_DIR" || ! -d "$WORK_DIR" || ! -f "$CONF_DIR/AdGuardHome.yaml" ]]; then
    echo ">>> First-time installation detected — enabling setup port 3000..."
    EXTRA_PUBLISH="PublishPort=$HOST_IPV4:3000:3000/tcp"
  else
    echo ">>> Existing configuration found — skipping setup port 3000."
    EXTRA_PUBLISH=""
  fi
  sed -i "s|%EXTRA_PORT_PLACEHOLDER%|$EXTRA_PUBLISH|" "$SCRIPT_DIR/$TARGET_FILE"
  #* ...
fi

#* Custom pre installation setup here if needed

#* ...

# Setup quadlet systemd
if [[ "$ROOTLESS" = "true" ]]; then
  SYSTEMCTL_CMD="systemctl --user"
  SYSTEMD_DIR="$HOME/.config/containers/systemd/"
  SUDO=""
else
  SYSTEMCTL_CMD="sudo systemctl"
  SYSTEMD_DIR="/etc/containers/systemd/"
  SUDO="sudo"
fi
echo ">>> Installing $TARGET_FILE to $SYSTEMD_DIR"
$SUDO mkdir -p "$SYSTEMD_DIR"
# $TO expands to nothing, just for readability
$SUDO $INSTALL "$SCRIPT_DIR/$TARGET_FILE" $TO "$SYSTEMD_DIR/$TARGET_FILE"

#* Uncomment if you have .network and/or .volume files to install
# echo ">>> Copying $SERVICE_NAME.network to $SYSTEMD_DIR"
# $SUDO cp "$SCRIPT_DIR/$SERVICE_NAME.network" "$SYSTEMD_DIR/$SERVICE_NAME.network"
# echo ">>> Copying $SERVICE_NAME.volume to $SYSTEMD_DIR"
# $SUDO cp "$SCRIPT_DIR/$SERVICE_NAME.volume" "$SYSTEMD_DIR/$SERVICE_NAME.volume"

echo ">>> Reloading systemd daemon to recognize new Quadlet"
$SYSTEMCTL_CMD daemon-reload

echo ">>> Starting $SERVICE_NAME container..."
$SYSTEMCTL_CMD start $SERVICE_NAME

echo ">>> Done!"
echo
echo "To check status:"
echo "  $SYSTEMCTL_CMD status $SERVICE_NAME"

#* Custom post installation setup here if needed
if [[ -n "$EXTRA_PUBLISH" ]]; then
  echo
  echo "AdGuardHome setup UI is available at: http://$HOST_IPV4:3000"
  echo "After completing setup, re-run ./install.sh and restart the service to lock it down."
  echo "To restart the service:"
  echo "  $SYSTEMCTL_CMD restart $SERVICE_NAME"
else
  echo
  echo "AdGuardHome is running with setup port closed."
  echo "If you haven't restarted the service:"
  echo "  $SYSTEMCTL_CMD restart $SERVICE_NAME"
fi
#* ...