# Update system
if ! grep -q "alias update=" $HOME/.bashrc; then
  echo "alias update='sudo apt update && sudo apt upgrade -y'" >> $HOME/.bashrc
  source $HOME/.bashrc
else
  echo "Alias 'update' already exists in .bashrc. Skip adding alias."
fi
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y git python3-pip net-tools curl wget gnupg2 ca-certificates lsb-release

# Make keyrings directory for adding repositories
sudo mkdir -p --mode=0755 /usr/share/keyrings

# Postgres repository
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Nginx repository
curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \
    | sudo tee /usr/share/keyrings/nginx-archive-keyring.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
http://nginx.org/packages/ubuntu `lsb_release -cs` nginx" \
    | sudo tee /etc/apt/sources.list.d/nginx.list
echo -e "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" \
    | sudo tee /etc/apt/preferences.d/99nginx

# Cloudflared repository
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg > /dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared noble main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Install
sudo apt update
sudo apt install -y postgresql nginx cloudflared

# Set up PostgreSQL password
echo "Please enter a password for the PostgreSQL 'postgres' user:"
read -s password
echo
if [ -z "$password" ]; then
    echo "Error: Password cannot be empty." >&2
    exit 1
fi
echo "Setting password for the 'postgres' user..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '$password';" || {
    echo "Error: Failed to set password for 'postgres' user." >&2
    exit 1
}
sudo systemctl restart postgresql || {
    echo "Error: Failed to restart PostgreSQL." >&2
    exit 1
}
echo "Password for 'postgres' user set successfully."
echo "Creating environment variable file for PostgreSQL password..."
mkdir -p $HOME/secret
chmod 600 $HOME/secret
echo "POSTGRES_DB_PASSWORD=$password" > $HOME/secret/db_info.env || {
    echo "Error: Failed to create environment variable file." >&2
    exit 1
}

# Filebrowser
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash

# Install Docker
## Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

## Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Deploy container using docker-compose
COMPOSE_DIR=$HOME/my-docker-services
mkdir -p $COMPOSE_DIR
wget https://nduc.id.vn/setup-server-ubuntu-nduc03/docker-compose.yml -O $COMPOSE_DIR
cd $COMPOSE_DIR
sudo docker-compose up -d

# Pi-hole install
curl -sSL https://install.pi-hole.net | bash