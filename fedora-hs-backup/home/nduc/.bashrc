# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific environment
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]; then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        if [ -f "$rc" ]; then
            . "$rc"
        fi
    done
fi
unset rc

alias update='sudo dnf update'
alias pkgin='sudo dnf install'
alias pkgrm='sudo dnf remove'

create-service() {
    # --- argument parsing ---
    if [[ -z "$1" ]]; then
        echo "Usage: create-service <service_name> [--template|-t]"
        return 1
    fi

    local service_name="$1"
    shift

    local use_template=false

    # parse optional flags
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --template|-t)
                use_template=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: create-service <service_name> [--template|-t]"
                return 1
                ;;
        esac
    done

    # --- paths ---
    local service_dir="$HOME/$service_name"
    local install_script_src="$HOME/install.sh.template"
    local install_script_dst="$service_dir/install.sh"

    # --- checks ---
    if [[ ! -f "$install_script_src" ]]; then
        echo "Error: install template not found at: $install_script_src"
        return 1
    fi

    # --- create service directory ---
    mkdir -p "$service_dir"

    # --- copy install.sh template ---
    cp "$install_script_src" "$install_script_dst"
    chmod +x "$install_script_dst"

    # --- create .container or .container.template ---
    if [[ "$use_template" = true ]]; then
        touch "$service_dir/$service_name.container.template"
        echo "Created: $service_dir/$service_name.container.template"
    else
        touch "$service_dir/$service_name.container"
        echo "Created: $service_dir/$service_name.container"
    fi

    echo "Service skeleton created at: $service_dir"
}

alias rm='rm -i'