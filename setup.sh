#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║       PHANTOM v3.0 SPECTRE — Kali Linux Setup Script         ║
# ╚══════════════════════════════════════════════════════════════╝

RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
CYAN='\033[96m'; BOLD='\033[1m'; RESET='\033[0m'; DIM='\033[2m'

echo -e "\n${RED}${BOLD}"
echo "  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗"
echo "  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║"
echo "  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║"
echo "  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║"
echo "  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║"
echo "  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝"
echo -e "${RESET}${DIM}          v3.0 SPECTRE — Kali Linux Setup${RESET}"
echo -e "${YELLOW}  ──────────────────────────────────────────────────────${RESET}\n"

# Root check
[ "$EUID" -ne 0 ] && SUDO="sudo" && echo -e "${YELLOW}  [!] Using sudo for package installs${RESET}" \
                  || SUDO="" && echo -e "${GREEN}  [+] Running as root${RESET}"

# Python
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    echo -e "${GREEN}  [+] ${PY_VER}${RESET}"
else
    echo -e "${RED}  [-] Python3 not found — installing...${RESET}"
    $SUDO apt-get install -y python3 python3-pip -qq
fi

# System packages
echo -e "\n${CYAN}  [*] Installing system dependencies...${RESET}"
PACKAGES=("dnsutils" "traceroute" "whois" "nmap" "curl" "netcat-openbsd" "net-tools")

for pkg in "${PACKAGES[@]}"; do
    if dpkg -l "$pkg" &>/dev/null 2>&1; then
        echo -e "  ${GREEN}[✓]${RESET} $pkg"
    else
        echo -e "  ${YELLOW}[↓]${RESET} Installing $pkg..."
        $SUDO apt-get install -y "$pkg" -qq 2>/dev/null \
            && echo -e "  ${GREEN}[✓]${RESET} $pkg installed" \
            || echo -e "  ${RED}[✗]${RESET} Failed: $pkg"
    fi
done

# Make executable + symlink
echo -e "\n${CYAN}  [*] Configuring Phantom...${RESET}"
chmod +x phantom.py
echo -e "  ${GREEN}[✓]${RESET} phantom.py executable"

$SUDO ln -sf "$(pwd)/phantom.py" /usr/local/bin/phantom 2>/dev/null \
    && echo -e "  ${GREEN}[✓]${RESET} Linked → /usr/local/bin/phantom" || true

# Readline history dir
touch ~/.phantom_history 2>/dev/null
echo -e "  ${GREEN}[✓]${RESET} Command history enabled (~/.phantom_history)"

# Desktop entry
DESKTOP_FILE="/usr/share/applications/phantom-osint.desktop"
$SUDO bash -c "cat > $DESKTOP_FILE" 2>/dev/null <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Phantom OSINT v3
Comment=SPECTRE Intelligence Framework
Exec=bash -c 'cd $(pwd) && python3 phantom.py; read'
Icon=kali-menu
Terminal=true
Categories=Network;Security;
Keywords=osint;recon;security;phantom;spectre;
DESKTOP
[ -f "$DESKTOP_FILE" ] && echo -e "  ${GREEN}[✓]${RESET} Kali menu entry created"

echo -e "\n${YELLOW}  ╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${YELLOW}  ║${RESET}          ${BOLD}PHANTOM v3.0 SPECTRE — READY${RESET}              ${YELLOW}║${RESET}"
echo -e "${YELLOW}  ╠══════════════════════════════════════════════════════╣${RESET}"
echo -e "${YELLOW}  ║${RESET}  ${GREEN}Run anywhere:${RESET}   phantom                          ${YELLOW}║${RESET}"
echo -e "${YELLOW}  ║${RESET}  ${GREEN}Direct:${RESET}         python3 phantom.py               ${YELLOW}║${RESET}"
echo -e "${YELLOW}  ║${RESET}  ${GREEN}Quick module:${RESET}   python3 phantom.py -m 01 -t IP   ${YELLOW}║${RESET}"
echo -e "${YELLOW}  ║${RESET}  ${GREEN}No animation:${RESET}   python3 phantom.py --no-banner    ${YELLOW}║${RESET}"
echo -e "${YELLOW}  ╠══════════════════════════════════════════════════════╣${RESET}"
echo -e "${YELLOW}  ║${RESET}  ${RED}For educational and authorized use only!${RESET}        ${YELLOW}║${RESET}"
echo -e "${YELLOW}  ╚══════════════════════════════════════════════════════╝${RESET}\n"
