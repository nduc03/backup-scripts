import configparser
import subprocess
import os
import sys

if sys.platform.startswith("linux") and os.geteuid() != 0:
    print("This script must be run as root.")
    sys.exit(1)

CONFIG_PATH = '/etc/add-priv-service.conf'
NGINX_CONFIG_PATH = '/etc/nginx/sites-enabled/default'
CLOUDFLARE_CREDENTIALS = os.path.expanduser('~/.secrets/cloudflare.ini')

def get_domain_from_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    try:
        return config['general']['domain']
    except KeyError:
        print("Error: Could not find 'domain' in [general] section of config.")
        sys.exit(1)

def get_user_input():
    service_name = input("Enter service name: ").strip()
    service_port = input("Enter service port: ").strip()
    if not service_port.isdigit() or not (1 <= int(service_port) <= 65535):
        print("Invalid port number.")
        sys.exit(1)

    last_octet = input("Enter proxy IP address: 192.168.1.").strip()
    if not last_octet.isdigit() or not (1 <= int(last_octet) <= 254):
        print("Invalid IP octet. Must be a number between 1 and 254.")
        sys.exit(1)

    return service_name, service_port, last_octet

def request_ssl_cert(domain, service_name):
    full_domain = f"{service_name}.{domain}"
    try:
        subprocess.run([
            "sudo", "certbot", "certonly",
            "--dns-cloudflare",
            "--dns-cloudflare-credentials", CLOUDFLARE_CREDENTIALS,
            "-d", full_domain
        ], check=True)
    except subprocess.CalledProcessError:
        print("Certbot failed. Aborting.")
        sys.exit(1)

def update_nginx_config(domain, service_name, last_octet, service_port):
    full_domain = f"{service_name}.{domain}"
    config_block = f"""
server {{
    # Auto generated
    # {service_name} server
    listen 192.168.1.{last_octet}:443 ssl;
    server_name {full_domain};

    ssl on;

    ssl_certificate     /etc/letsencrypt/live/{full_domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{full_domain}/privkey.pem;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    keepalive_timeout   70;

    location / {{
        proxy_pass http://127.0.0.1:{service_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }}
}}

server {{
    # Auto generated
    # {service_name} https redirect
    listen 192.168.1.{last_octet}:80;
    server_name {full_domain};

    return 301 https://$host$request_uri;
}}
"""
    try:
        with open(NGINX_CONFIG_PATH, 'a') as f:
            f.write(config_block)
        subprocess.run(["nginx", "-t"], check=True)
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
        print(f"Nginx config updated for {full_domain}.")
    except PermissionError:
        print("Permission denied: need to run as root to modify Nginx config.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Nginx configuration error. Aborting.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while updating Nginx config: {e}")
        sys.exit(1)

def main():
    domain = get_domain_from_config()
    service_name, service_port, last_octet = get_user_input()
    request_ssl_cert(domain, service_name)
    update_nginx_config(domain, service_name, last_octet, service_port)

if __name__ == '__main__':
    main()
