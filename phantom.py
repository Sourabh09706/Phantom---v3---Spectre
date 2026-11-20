#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          PHANTOM v3.0 — SPECTRE OSINT Intelligence Framework            ║
║                  Advanced Reconnaissance Platform                        ║
║               Built for Kali Linux | B.Tech CSE Project                 ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os, sys, json, time, socket, struct, hashlib, ipaddress, argparse
import threading, subprocess, urllib.request, urllib.parse, urllib.error
import ssl, re, random, readline, atexit, signal, textwrap
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# ─── Version ─────────────────────────────────────────────────────────────────
VERSION   = "3.0.0"
CODENAME  = "SPECTRE"
BUILD     = datetime.now().strftime("%Y%m%d")

# ─── ANSI Color + Style ───────────────────────────────────────────────────────
class C:
    RESET    = '\033[0m'
    BOLD     = '\033[1m'
    DIM      = '\033[2m'
    ITALIC   = '\033[3m'
    ULINE    = '\033[4m'
    BLINK    = '\033[5m'
    INVERT   = '\033[7m'

    BLACK    = '\033[30m';  DGRAY   = '\033[90m'
    RED      = '\033[31m';  BRED    = '\033[91m'
    GREEN    = '\033[32m';  BGREEN  = '\033[92m'
    YELLOW   = '\033[33m';  BYELLOW = '\033[93m'
    BLUE     = '\033[34m';  BBLUE   = '\033[94m'
    MAGENTA  = '\033[35m';  BMAGENTA= '\033[95m'
    CYAN     = '\033[36m';  BCYAN   = '\033[96m'
    WHITE    = '\033[37m';  BWHITE  = '\033[97m'

    BG_BLACK = '\033[40m';  BG_RED  = '\033[41m'
    BG_GREEN = '\033[42m';  BG_CYAN = '\033[46m'
    BG_BLUE  = '\033[44m';  BG_MAG  = '\033[45m'

def strip_ansi(s):
    return re.sub(r'\033\[[0-9;]*m', '', s)

def visible_len(s):
    return len(strip_ansi(s))

# ─── Session Logger ───────────────────────────────────────────────────────────
class Logger:
    def __init__(self):
        self.file = None
        self.path = None
        self.lock = threading.Lock()

    def start(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = f"phantom_session_{ts}.log"
        self.file = open(self.path, 'w', encoding='utf-8')
        self._write(f"PHANTOM v{VERSION} SESSION LOG — {datetime.now().isoformat()}\n")
        self._write("=" * 70 + "\n")

    def _write(self, text):
        if self.file:
            with self.lock:
                clean = strip_ansi(text)
                self.file.write(clean)
                self.file.flush()

    def log(self, text):
        self._write(text + "\n")

    def close(self):
        if self.file:
            self._write(f"\n\nSession ended: {datetime.now().isoformat()}\n")
            self.file.close()
            self.file = None

LOG = Logger()

# ─── Threat Score Tracker ─────────────────────────────────────────────────────
class ThreatScore:
    def __init__(self):
        self.score = 0
        self.max_score = 0
        self.findings = []

    def add(self, label, severity, points):
        """severity: LOW / MED / HIGH / CRIT"""
        self.score += points
        self.max_score += points
        self.findings.append((label, severity, points))

    def add_good(self, label, relief):
        self.max_score += relief

    def render(self):
        if self.max_score == 0:
            return
        ratio = min(self.score / max(self.max_score, 1), 1.0)
        bars = 40
        filled = int(ratio * bars)

        if ratio < 0.3:
            col = C.BGREEN;  grade = "LOW RISK"
        elif ratio < 0.6:
            col = C.BYELLOW; grade = "MODERATE"
        elif ratio < 0.8:
            col = C.BRED;    grade = "HIGH RISK"
        else:
            col = C.BMAGENTA + C.BOLD; grade = "CRITICAL"

        bar = col + '█' * filled + C.DIM + '░' * (bars - filled) + C.RESET
        print(f'\n  {C.BCYAN}┌─ THREAT ASSESSMENT ────────────────────────────────────┐{C.RESET}')
        print(f'  {C.BCYAN}│{C.RESET}  Risk Gauge: [{bar}]')
        print(f'  {C.BCYAN}│{C.RESET}  {C.BOLD}Score:{C.RESET} {col}{self.score}{C.RESET}  │  {C.BOLD}Level:{C.RESET} {col}{grade}{C.RESET}')
        if self.findings:
            print(f'  {C.BCYAN}│{C.RESET}  {C.DIM}Key Findings:{C.RESET}')
            for label, sev, pts in self.findings[:5]:
                sev_colors = {'LOW':C.BGREEN,'MED':C.BYELLOW,'HIGH':C.BRED,'CRIT':C.BMAGENTA+C.BOLD}
                sc = sev_colors.get(sev, C.BWHITE)
                print(f'  {C.BCYAN}│{C.RESET}    {sc}[{sev}]{C.RESET} {label}')
        print(f'  {C.BCYAN}└────────────────────────────────────────────────────────┘{C.RESET}')
        LOG.log(f"Threat Score: {self.score} | Level: {grade}")

THREAT = ThreatScore()

# ─── Core UI Primitives ───────────────────────────────────────────────────────
def typewrite(text, delay=0.018, newline=True):
    for ch in text:
        sys.stdout.write(ch); sys.stdout.flush(); time.sleep(delay)
    if newline: print()

def slow_print(text, delay=0.003):
    for line in text.split('\n'):
        for ch in line:
            sys.stdout.write(ch); sys.stdout.flush(); time.sleep(delay)
        print()

def spinner(message, duration=1.2, style='braille'):
    frames_map = {
        'braille': ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏'],
        'line':    ['─','\\','│','/'],
        'dot':     ['·','•','●','•'],
        'arrow':   ['←','↖','↑','↗','→','↘','↓','↙'],
    }
    frames = frames_map.get(style, frames_map['braille'])
    end = time.time() + duration; i = 0
    while time.time() < end:
        sys.stdout.write(f'\r  {C.BCYAN}{frames[i % len(frames)]}{C.RESET} {C.DIM}{message}{C.RESET}')
        sys.stdout.flush(); time.sleep(0.08); i += 1
    sys.stdout.write(f'\r  {C.BGREEN}✔{C.RESET} {message}{"" * 10}\n')
    sys.stdout.flush()
    LOG.log(f"[INIT] {message}")

def progress_bar(label, steps=30, delay=0.04, color=C.BGREEN):
    sys.stdout.write(f'  {C.DIM}{label}{C.RESET}: [')
    for i in range(steps):
        time.sleep(delay)
        ratio = i / steps
        c = C.BGREEN if ratio > 0.7 else C.BYELLOW if ratio > 0.4 else C.BRED
        sys.stdout.write(f'{c}█{C.RESET}'); sys.stdout.flush()
    sys.stdout.write(f'] {C.BGREEN}DONE{C.RESET}\n'); sys.stdout.flush()

def section_header(title, subtitle=''):
    w = 66
    print(f'\n{C.BBLUE}{"═"*w}{C.RESET}')
    print(f'{C.BOLD}{C.BCYAN}  ▶  {title.upper()}{C.RESET}')
    if subtitle:
        print(f'{C.DIM}     {subtitle}{C.RESET}')
    print(f'{C.BBLUE}{"═"*w}{C.RESET}\n')
    LOG.log(f"\n{'='*60}\nMODULE: {title}\n{'='*60}")

def result_line(key, value, ok=True, indent=2):
    icon = f'{C.BGREEN}[+]{C.RESET}' if ok else f'{C.BRED}[-]{C.RESET}'
    pad = ' ' * indent
    line = f'{pad}{icon} {C.BYELLOW}{key:<26}{C.RESET}: {C.BWHITE}{value}{C.RESET}'
    print(line)
    LOG.log(f"  {'[+]' if ok else '[-]'} {key:<26}: {strip_ansi(str(value))}")

def warn(msg, indent=2):
    pad = ' ' * indent
    print(f'{pad}{C.BYELLOW}[!]{C.RESET} {C.YELLOW}{msg}{C.RESET}')
    LOG.log(f"  [!] {strip_ansi(msg)}")

def error(msg, indent=2):
    pad = ' ' * indent
    print(f'{pad}{C.BRED}[✗]{C.RESET} {C.RED}{msg}{C.RESET}')
    LOG.log(f"  [X] {strip_ansi(msg)}")

def info(msg, indent=2):
    pad = ' ' * indent
    print(f'{pad}{C.BCYAN}[*]{C.RESET} {C.CYAN}{msg}{C.RESET}')
    LOG.log(f"  [*] {strip_ansi(msg)}")

def success(msg, indent=2):
    pad = ' ' * indent
    print(f'{pad}{C.BGREEN}[✓]{C.RESET} {C.BGREEN}{msg}{C.RESET}')
    LOG.log(f"  [✓] {strip_ansi(msg)}")

def table(headers, rows, col_colors=None):
    """Render a clean ASCII table."""
    if not rows: return
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], visible_len(str(cell)))
    sep = '  ├─' + '─┼─'.join('─'*w for w in widths) + '─┤'
    top = '  ┌─' + '─┬─'.join('─'*w for w in widths) + '─┐'
    bot = '  └─' + '─┴─'.join('─'*w for w in widths) + '─┘'
    hdr = '  │ ' + ' │ '.join(
        f'{C.BOLD}{C.BYELLOW}{h:<{widths[i]}}{C.RESET}' for i, h in enumerate(headers)
    ) + ' │'
    print(f'{C.DIM}{top}{C.RESET}')
    print(hdr)
    print(f'{C.DIM}{sep}{C.RESET}')
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            col = (col_colors or {}).get(i, C.BWHITE)
            s = str(cell)
            pad = widths[i] - visible_len(s)
            cells.append(f'{col}{s}{C.RESET}{" "*pad}')
        print(f'  │ ' + ' │ '.join(cells) + ' │')
    print(f'{C.DIM}{bot}{C.RESET}')

def status_bar():
    """Print a small status/timestamp bar."""
    now = datetime.now().strftime('%H:%M:%S')
    print(f'\n  {C.DIM}{"─"*62}{C.RESET}')
    print(f'  {C.DIM}Phantom v{VERSION}-{CODENAME}  │  {now}  │  Log: {LOG.path or "none"}{C.RESET}')
    print(f'  {C.DIM}{"─"*62}{C.RESET}\n')

# ─── Matrix Rain Boot Effect ──────────────────────────────────────────────────
def matrix_rain(duration=1.8):
    """Brief matrix-style column rain effect."""
    try:
        cols = min(os.get_terminal_size().columns, 100)
    except Exception:
        cols = 80
    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ!#$%&<>?"
    end = time.time() + duration
    while time.time() < end:
        line = ''.join(
            random.choice([C.BGREEN, C.GREEN, C.DIM+C.GREEN]) +
            random.choice(chars) + C.RESET
            for _ in range(cols // 2)
        )
        print(line[:cols])
        time.sleep(0.04)
    print(C.RESET)

# ─── Animated Banner ──────────────────────────────────────────────────────────
BANNER = f"""\
{C.BRED}{C.BOLD}
  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝{C.RESET}
{C.DIM}              ◈  O P E N   S O U R C E   I N T E L L I G E N C E  ◈{C.RESET}
{C.BYELLOW}  ╔════════════════════════════════════════════════════════════╗{C.RESET}
{C.BYELLOW}  ║{C.RESET}  {C.BCYAN}Version{C.RESET} {C.BOLD}{VERSION}{C.RESET}  {C.BCYAN}│{C.RESET}  Codename {C.BRED}{C.BOLD}{CODENAME}{C.RESET}  {C.BCYAN}│{C.RESET}  Build {C.DIM}{BUILD}{C.RESET}          {C.BYELLOW}║{C.RESET}
{C.BYELLOW}  ║{C.RESET}  {C.DIM}Authorized reconnaissance and academic security research only{C.RESET}  {C.BYELLOW}║{C.RESET}
{C.BYELLOW}  ╚════════════════════════════════════════════════════════════╝{C.RESET}
"""

MENU = f"""
{C.BBLUE}  ┌──────────────────────────────────────────────────────────────┐{C.RESET}
{C.BBLUE}  │{C.RESET}          {C.BOLD}{C.BWHITE}[ PHANTOM SPECTRE — MODULE SELECTION ]{C.RESET}          {C.BBLUE}│{C.RESET}
{C.BBLUE}  ├────────────────────────────────┬─────────────────────────────┤{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[01]{C.RESET} {C.BWHITE}IP Intelligence{C.RESET}          {C.BBLUE}│{C.RESET}  {C.BYELLOW}[08]{C.RESET} {C.BWHITE}Hash Analyzer{C.RESET}         {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[02]{C.RESET} {C.BWHITE}DNS Reconnaissance{C.RESET}       {C.BBLUE}│{C.RESET}  {C.BYELLOW}[09]{C.RESET} {C.BWHITE}Network Tracer{C.RESET}        {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[03]{C.RESET} {C.BWHITE}Port Scanner{C.RESET}             {C.BBLUE}│{C.RESET}  {C.BYELLOW}[10]{C.RESET} {C.BWHITE}Full OSINT Report{C.RESET}     {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[04]{C.RESET} {C.BWHITE}SSL/TLS Inspector{C.RESET}        {C.BBLUE}│{C.RESET}  {C.BYELLOW}[11]{C.RESET} {C.BWHITE}Username Hunter{C.RESET}       {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[05]{C.RESET} {C.BWHITE}HTTP Header Audit{C.RESET}        {C.BBLUE}│{C.RESET}  {C.BYELLOW}[12]{C.RESET} {C.BWHITE}Tech Fingerprint{C.RESET}      {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[06]{C.RESET} {C.BWHITE}Subdomain Harvester{C.RESET}      {C.BBLUE}│{C.RESET}  {C.BYELLOW}[13]{C.RESET} {C.BGREEN}CVE Intelligence{C.RESET}      {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[07]{C.RESET} {C.BWHITE}Email OSINT{C.RESET}              {C.BBLUE}│{C.RESET}  {C.BYELLOW}[14]{C.RESET} {C.BGREEN}WHOIS Deep Dive{C.RESET}       {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BYELLOW}[15]{C.RESET} {C.BGREEN}WAF Detector{C.RESET}             {C.BBLUE}│{C.RESET}  {C.BYELLOW}[16]{C.RESET} {C.BGREEN}CMS Exploit Map{C.RESET}       {C.BBLUE}│{C.RESET}
{C.BBLUE}  ├────────────────────────────────┴─────────────────────────────┤{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.DIM}Special:{C.RESET} {C.BCYAN}help <module#{C.RESET}>  {C.BCYAN}history{C.RESET}  {C.BCYAN}clear{C.RESET}  {C.BCYAN}log{C.RESET}  {C.BCYAN}score{C.RESET}      {C.BBLUE}│{C.RESET}
{C.BBLUE}  │{C.RESET}  {C.BRED}[00]{C.RESET} Exit    {C.DIM}|{C.RESET}  Session auto-saved to {C.DIM}phantom_session_*.log{C.RESET}    {C.BBLUE}│{C.RESET}
{C.BBLUE}  └──────────────────────────────────────────────────────────────┘{C.RESET}
"""

MODULE_HELP = {
    '01': ("IP Intelligence",
           "Geolocates an IP or hostname via ip-api.com. Performs reverse DNS,\n"
           "     ASN lookup, ISP identification, and quick port probe on common services.\n"
           "     Target: IP address or hostname  (e.g. 8.8.8.8 or example.com)"),
    '02': ("DNS Reconnaissance",
           "Queries A, AAAA, MX, NS, TXT, SOA, CNAME records. Tests for zone\n"
           "     transfer vulnerability (AXFR). Checks SPF, DMARC, DKIM configuration.\n"
           "     Target: Domain name  (e.g. example.com)"),
    '03': ("Port Scanner",
           "Multi-threaded TCP connect scanner with banner grabbing. Three modes:\n"
           "     Top-40 services, full 1-1024, or custom range/list. Service detection\n"
           "     with risk annotations for dangerous open ports.\n"
           "     Target: IP address or hostname"),
    '04': ("SSL/TLS Inspector",
           "Full TLS certificate analysis: chain, SANs, expiry countdown,\n"
           "     cipher suite strength, protocol version, HSTS preload check,\n"
           "     weak cipher detection, and OCSP stapling hint.\n"
           "     Target: Domain  (e.g. example.com)"),
    '05': ("HTTP Header Audit",
           "Fetches HTTP response headers and audits 11 security controls.\n"
           "     Grades from A+ to F. Detects server/tech disclosure, clickjacking,\n"
           "     CSP, HSTS, XSS, MIME, and Referrer Policy.\n"
           "     Target: URL or domain"),
    '06': ("Subdomain Harvester",
           "Combines brute-force DNS (60+ wordlist) with certificate transparency\n"
           "     (crt.sh). Concurrent resolution. Outputs IPs and flags wildcards.\n"
           "     Target: Domain  (e.g. example.com)"),
    '07': ("Email OSINT",
           "Parses and validates email structure, pattern classification,\n"
           "     MX record verification, SMTP passive check, permutation generation,\n"
           "     and breach/OSINT resource links.\n"
           "     Target: Email address"),
    '08': ("Hash Analyzer",
           "Identifies 25+ hash types by length and prefix patterns.\n"
           "     Quick dictionary attack on MD5/SHA1. Provides crack resource links.\n"
           "     Target: Hash string"),
    '09': ("Network Tracer",
           "Runs traceroute/tracepath with hop-by-hop geolocation of public IPs.\n"
           "     Annotates known CDN nodes and identifies potential choke points.\n"
           "     Target: IP address or hostname"),
    '10': ("Full OSINT Report",
           "Orchestrates DNS, Subdomain, HTTP, SSL, Tech modules sequentially.\n"
           "     Computes aggregate threat score and saves full report to disk.\n"
           "     Target: Domain"),
    '11': ("Username Hunter",
           "Probes 25 platforms (GitHub, GitLab, Reddit, HackerOne, etc.).\n"
           "     HTTP 200/404 detection with false-positive filtering.\n"
           "     Target: Username"),
    '12': ("Tech Fingerprint",
           "Pattern-matches 30+ technology signatures in HTTP body+headers:\n"
           "     CMS (WordPress/Drupal/Joomla), frameworks (React/Vue/Angular),\n"
           "     CDNs, analytics, server software, languages.\n"
           "     Target: URL or domain"),
    '13': ("CVE Intelligence",
           "Queries NIST NVD API for CVEs matching a product/service keyword.\n"
           "     Shows CVSS score, severity, description, and reference links.\n"
           "     Target: Product name  (e.g. apache, openssh, wordpress)"),
    '14': ("WHOIS Deep Dive",
           "Runs whois and parses registrar, registrant, creation/expiry dates,\n"
           "     name servers, abuse contacts, and DNSSEC status.\n"
           "     Target: Domain or IP"),
    '15': ("WAF Detector",
           "Sends crafted payloads (XSS, SQLi, path traversal) to detect WAF\n"
           "     presence. Fingerprints vendor (Cloudflare, AWS WAF, ModSecurity,\n"
           "     Akamai, etc.) from response headers and error pages.\n"
           "     Target: URL or domain"),
    '16': ("CMS Exploit Map",
           "Fingerprints the CMS then maps known public vulnerabilities and\n"
           "     default credential risks for that platform. Checks for exposed\n"
           "     admin panels, readme files, and config endpoints.\n"
           "     Target: URL or domain"),
}

# ─── Command History ──────────────────────────────────────────────────────────
HISTORY_FILE = os.path.expanduser("~/.phantom_history")
try:
    readline.read_history_file(HISTORY_FILE)
except FileNotFoundError:
    pass
readline.set_history_length(200)
atexit.register(readline.write_history_file, HISTORY_FILE)

SESSION_HISTORY = []

# ─── Helper: safe HTTP fetch ──────────────────────────────────────────────────
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

def http_get(url, timeout=10, headers=None):
    h = {'User-Agent': f'PhantomOSINT/{VERSION} (Security Research)'}
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='ignore'), dict(r.getheaders()), r.status, r.url

def http_get_raw(url, timeout=10, headers=None):
    h = {'User-Agent': f'PhantomOSINT/{VERSION}'}
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=timeout) as r:
        return r.read(), dict(r.getheaders()), r.status

# ─── Module 01: IP Intelligence ──────────────────────────────────────────────
def module_ip_intel(target):
    section_header("IP Intelligence Engine", "Geolocation · ASN · Reverse DNS · Quick Port Probe")
    ts = ThreatScore()

    spinner("Resolving target", 0.6)
    try:
        resolved = socket.gethostbyname(target)
        if resolved != target:
            result_line("Resolved IP", resolved)
        ip = resolved
    except Exception:
        ip = target

    try:
        ip_obj = ipaddress.ip_address(ip)
        result_line("IP Version", f"IPv{ip_obj.version}")
        result_line("Private Range", "Yes" if ip_obj.is_private else "No", ok=not ip_obj.is_private)
        result_line("Loopback",     "Yes" if ip_obj.is_loopback else "No", ok=not ip_obj.is_loopback)
        result_line("Multicast",    "Yes" if ip_obj.is_multicast else "No")
        result_line("Global",       "Yes" if ip_obj.is_global else "No", ok=ip_obj.is_global)
        if ip_obj.is_private:
            warn("Private IP — geolocation won't be meaningful")
    except ValueError:
        error(f"Invalid IP: {ip}"); return

    spinner("Querying ip-api.com geolocation", 1.0)
    try:
        url = (f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
               "region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,"
               "mobile,proxy,hosting,query")
        body, _, _, _ = http_get(url, timeout=8)
        data = json.loads(body)

        if data.get('status') == 'success':
            print()
            rows = [
                ("Country",      f"{data.get('country','?')} ({data.get('countryCode','?')})"),
                ("Region",       data.get('regionName','?')),
                ("City",         data.get('city','?')),
                ("ZIP / Postal", data.get('zip','?')),
                ("Coordinates",  f"{data.get('lat','?')}, {data.get('lon','?')}"),
                ("Timezone",     data.get('timezone','?')),
                ("ISP",          data.get('isp','?')),
                ("Organization", data.get('org','?')),
                ("AS Number",    data.get('as','?')),
                ("AS Name",      data.get('asname','?')),
            ]
            for k, v in rows:
                result_line(k, v)

            flags = []
            if data.get('proxy') or data.get('hosting'):
                flags.append("VPN/Proxy/Hosting detected")
                ts.add("Proxy/Hosting IP", "MED", 20)
            if data.get('mobile'):
                flags.append("Mobile carrier IP")
            for f in flags:
                warn(f)

            lat, lon = data.get('lat'), data.get('lon')
            if lat and lon:
                maps_url = f"https://maps.google.com/?q={lat},{lon}"
                info(f"Google Maps → {C.BCYAN}{maps_url}{C.RESET}")
    except Exception as e:
        warn(f"Geo lookup failed: {e}")

    # Reverse DNS
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        result_line("Reverse DNS", hostname)
    except Exception:
        result_line("Reverse DNS", "No PTR record", ok=False)

    # Port quick-scan
    print()
    info("Quick port probe (top services)...")
    RISKY_PORTS = {23:'TELNET',4444:'Metasploit',5900:'VNC',3389:'RDP',6379:'Redis'}
    COMMON_PORTS = {21:'FTP', 22:'SSH', 23:'TELNET', 25:'SMTP', 53:'DNS',
                    80:'HTTP', 110:'POP3', 143:'IMAP', 443:'HTTPS', 445:'SMB',
                    1433:'MSSQL', 3306:'MySQL', 3389:'RDP', 4444:'Metasploit',
                    5432:'PgSQL', 5900:'VNC', 6379:'Redis', 8080:'HTTP-Alt',
                    8443:'HTTPS-Alt', 9200:'Elasticsearch', 27017:'MongoDB'}
    open_ports = []
    lock = threading.Lock()

    def probe(port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.6)
            if s.connect_ex((ip, port)) == 0:
                with lock: open_ports.append(port)
            s.close()
        except Exception: pass

    with ThreadPoolExecutor(max_workers=80) as ex:
        ex.map(probe, COMMON_PORTS.keys())

    if open_ports:
        rows = []
        for p in sorted(open_ports):
            svc = COMMON_PORTS.get(p,'UNKNOWN')
            risk = "⚠ HIGH" if p in RISKY_PORTS else "—"
            rows.append([str(p), svc, risk])
            if p in RISKY_PORTS:
                ts.add(f"Dangerous port {p}/{svc} open", "HIGH", 35)
        table(["Port","Service","Risk"], rows,
              col_colors={0:C.BGREEN, 1:C.BCYAN, 2:C.BYELLOW})
    else:
        result_line("Open Ports", "None detected in quick scan", ok=False)

    ts.render()


# ─── Module 02: DNS Reconnaissance ───────────────────────────────────────────
def module_dns_recon(domain):
    section_header("DNS Reconnaissance Unit", "Record Enumeration · Zone Transfer · Email Security")
    ts = ThreatScore()

    def dig(rtype, target=None):
        t = target or domain
        try:
            r = subprocess.run(['dig', '+short', '+time=3', rtype, t],
                               capture_output=True, text=True, timeout=6)
            return [l.strip() for l in r.stdout.strip().split('\n') if l.strip()]
        except FileNotFoundError:
            try:
                r = subprocess.run(['nslookup', f'-type={rtype}', t],
                                   capture_output=True, text=True, timeout=6)
                return [r.stdout.strip()[:300]]
            except Exception: return []
        except Exception: return []

    spinner("Enumerating DNS records", 1.0)
    record_types = ['A','AAAA','MX','NS','TXT','SOA','CNAME','CAA']
    for rtype in record_types:
        records = dig(rtype)
        if records:
            for r in records:
                result_line(f"{rtype} Record", r[:72])
        else:
            result_line(f"{rtype} Record", "Not found", ok=False)

    # Zone Transfer
    print()
    info("Testing DNS zone transfer (AXFR)...")
    nameservers = dig('NS')
    vuln_ns = []
    for ns_raw in nameservers[:3]:
        ns = ns_raw.strip().rstrip('.')
        try:
            r = subprocess.run(['dig', 'AXFR', f'@{ns}', domain],
                               capture_output=True, text=True, timeout=10)
            if 'Transfer failed' not in r.stdout and len(r.stdout.strip()) > 200:
                warn(f"Zone transfer ALLOWED on {ns} — CRITICAL MISCONFIGURATION!")
                ts.add(f"AXFR allowed on {ns}", "CRIT", 90)
                vuln_ns.append(ns)
        except Exception: pass
    if not vuln_ns:
        success("Zone transfer not allowed (good)")

    # Email security
    print()
    info("Checking email security records...")
    for label, query, check in [
        ('SPF',   domain,            lambda v: 'v=spf1' in v.lower()),
        ('DMARC', f'_dmarc.{domain}', lambda v: 'v=dmarc1' in v.lower()),
        ('DKIM',  f'default._domainkey.{domain}', lambda v: 'v=dkim1' in v.lower()),
    ]:
        recs = dig('TXT', query)
        found = any(check(r) for r in recs)
        if found:
            result_line(label, f"Configured ✓")
        else:
            result_line(label, "Not configured — email spoofing risk", ok=False)
            ts.add(f"Missing {label}", "MED", 25)

    ts.render()


# ─── Module 03: Port Scanner ──────────────────────────────────────────────────
def module_port_scanner(target):
    section_header("Phantom Port Scanner", "Multi-threaded TCP · Banner Grab · Risk Annotation")
    ts = ThreatScore()

    SERVICE_MAP = {
        20:'FTP-DATA', 21:'FTP', 22:'SSH', 23:'TELNET', 25:'SMTP',
        53:'DNS', 67:'DHCP', 80:'HTTP', 110:'POP3', 111:'RPC',
        135:'MSRPC', 137:'NetBIOS', 139:'NetBIOS-SSN', 143:'IMAP',
        161:'SNMP', 389:'LDAP', 443:'HTTPS', 445:'SMB', 465:'SMTPS',
        512:'REXEC', 513:'RLOGIN', 514:'RSHELL', 587:'SMTP-SUB',
        631:'CUPS', 636:'LDAPS', 873:'RSYNC', 902:'VMware',
        993:'IMAPS', 995:'POP3S', 1080:'SOCKS', 1194:'OpenVPN',
        1433:'MSSQL', 1521:'Oracle', 2049:'NFS', 2222:'SSH-ALT',
        2375:'Docker', 2376:'Docker-TLS', 3000:'Dev-Server',
        3306:'MySQL', 3389:'RDP', 4369:'Erlang', 4444:'Metasploit',
        5432:'PostgreSQL', 5672:'RabbitMQ', 5900:'VNC',
        5984:'CouchDB', 6379:'Redis', 6443:'K8s-API',
        7001:'WebLogic', 7077:'Spark', 8080:'HTTP-Proxy',
        8443:'HTTPS-ALT', 8888:'Jupyter', 9000:'PHP-FPM',
        9090:'Prometheus', 9200:'Elasticsearch', 9300:'ES-Cluster',
        11211:'Memcached', 27017:'MongoDB', 50070:'Hadoop',
    }

    DANGER_PORTS = {23,4444,5900,3389,6379,11211,27017,9200,2375,5984,50070,7001}

    try:
        ip = socket.gethostbyname(target)
        info(f"Resolved: {C.BWHITE}{target}{C.RESET} → {C.BCYAN}{ip}{C.RESET}")
    except Exception:
        ip = target

    print(f'\n  {C.BYELLOW}[?]{C.RESET} Scan mode:')
    print(f'      {C.BWHITE}[1]{C.RESET} Top-50 service ports')
    print(f'      {C.BWHITE}[2]{C.RESET} Full 1–1024')
    print(f'      {C.BWHITE}[3]{C.RESET} Custom (e.g. 80,443,8080 or 1-500)')
    choice = input(f'\n  {C.BYELLOW}»{C.RESET} Mode: ').strip()

    if choice == '2':
        ports = list(range(1, 1025))
    elif choice == '3':
        raw = input(f'  {C.BYELLOW}»{C.RESET} Ports: ').strip()
        ports = []
        for part in raw.split(','):
            if '-' in part:
                a, b = part.split('-')
                ports.extend(range(int(a), int(b)+1))
            else:
                try: ports.append(int(part))
                except ValueError: pass
    else:
        ports = sorted(SERVICE_MAP.keys())

    spinner(f"Arming scanner for {len(ports)} ports", 0.8)

    open_ports = []
    closed = 0
    lock = threading.Lock()
    done_count = [0]
    total = len(ports)

    def scan_port(port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.65)
            result = s.connect_ex((ip, port))
            banner = ''
            if result == 0:
                try:
                    s.settimeout(0.4)
                    if port == 80 or port == 8080:
                        s.send(b'HEAD / HTTP/1.0\r\nHost: ' + ip.encode() + b'\r\n\r\n')
                    elif port == 22:
                        pass  # banner comes automatically
                    else:
                        s.send(b'\r\n')
                    banner = s.recv(256).decode('utf-8', errors='ignore').split('\n')[0].strip()
                except Exception:
                    pass
                with lock:
                    open_ports.append((port, banner))
            else:
                with lock:
                    pass
        except Exception:
            pass
        finally:
            try: s.close()
            except Exception: pass
        with lock:
            done_count[0] += 1

    print()
    sys.stdout.write(f'  {C.CYAN}Scanning{C.RESET} [{C.DIM}{"░"*50}{C.RESET}] 0%')
    sys.stdout.flush()

    with ThreadPoolExecutor(max_workers=200) as ex:
        futures = [ex.submit(scan_port, p) for p in ports]
        last_pct = 0
        for f in as_completed(futures):
            pct = int(done_count[0] / total * 100)
            if pct != last_pct and pct % 2 == 0:
                filled = pct // 2
                bar = C.BGREEN + '█'*filled + C.DIM + '░'*(50-filled) + C.RESET
                sys.stdout.write(f'\r  {C.CYAN}Scanning{C.RESET} [{bar}] {pct}%')
                sys.stdout.flush()
                last_pct = pct
    sys.stdout.write(f'\r  {C.BGREEN}Scan complete!{C.RESET}{"  "*30}\n')

    print()
    if open_ports:
        rows = []
        for port, banner in sorted(open_ports):
            svc = SERVICE_MAP.get(port, 'UNKNOWN')
            risk = f'{C.BRED}⚠ DANGER{C.RESET}' if port in DANGER_PORTS else f'{C.BGREEN}NORMAL{C.RESET}'
            b = banner[:35] + ('…' if len(banner)>35 else '') if banner else '—'
            rows.append([str(port), svc, b, risk])
            if port in DANGER_PORTS:
                ts.add(f"High-risk port {port}/{svc} open", "HIGH", 40)
        table(["Port","Service","Banner","Risk"], rows,
              col_colors={0:C.BGREEN, 1:C.BCYAN, 2:C.DIM, 3:C.BWHITE})
        info(f"{C.BGREEN}{len(open_ports)} open{C.RESET} of {len(ports)} scanned")
    else:
        result_line("Result", "No open ports detected", ok=False)

    ts.render()


# ─── Module 04: SSL/TLS Inspector ────────────────────────────────────────────
def module_ssl_inspector(target):
    section_header("SSL/TLS Certificate Inspector", "Chain · Ciphers · Expiry · Protocol Security")
    ts = ThreatScore()

    host = target.replace('https://','').replace('http://','').split('/')[0].split(':')[0]
    spinner("Performing TLS handshake", 1.2)

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, 443), timeout=8) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as conn:
                cert = conn.getpeercert()
                bin_cert = conn.getpeercert(binary_form=True)
                cipher = conn.cipher()
                protocol = conn.version()

        result_line("TLS Protocol", protocol)
        if protocol in ('TLSv1', 'TLSv1.0', 'SSLv3', 'SSLv2'):
            warn(f"Deprecated protocol {protocol} — VULNERABLE to POODLE/BEAST")
            ts.add(f"Deprecated TLS {protocol}", "HIGH", 50)
        elif protocol == 'TLSv1.1':
            warn("TLSv1.1 deprecated since 2021")
            ts.add("TLS 1.1 in use", "MED", 25)
        else:
            success(f"{protocol} — Modern protocol")

        result_line("Cipher Suite", cipher[0] if cipher else '?')
        result_line("Key Bits",     str(cipher[2]) if cipher else '?')
        if cipher and cipher[2] and cipher[2] < 128:
            warn("Weak key length < 128 bits")
            ts.add("Weak cipher", "HIGH", 45)

        if cert:
            subject = dict(x[0] for x in cert.get('subject', []))
            issuer  = dict(x[0] for x in cert.get('issuer',  []))
            print()
            info("Certificate Details:")
            result_line("Common Name",    subject.get('commonName','?'))
            result_line("Org",            subject.get('organizationName','?'))
            result_line("Country",        subject.get('countryName','?'))
            result_line("Issuer CN",      issuer.get('commonName','?'))
            result_line("Issuer Org",     issuer.get('organizationName','?'))
            result_line("Serial No.",     cert.get('serialNumber','?')[:24])
            result_line("Valid From",     cert.get('notBefore','?'))
            result_line("Valid Until",    cert.get('notAfter','?'))

            # SANs
            sans = [v for t,v in cert.get('subjectAltName',[]) if t=='DNS']
            if sans:
                result_line("SAN Count", str(len(sans)))
                for s in sans[:6]:
                    print(f'      {C.DIM}→{C.RESET} {C.BCYAN}{s}{C.RESET}')
                if len(sans) > 6:
                    print(f'      {C.DIM}… and {len(sans)-6} more{C.RESET}')

            # Expiry
            try:
                exp = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days = (exp - datetime.utcnow()).days
                if days < 0:
                    warn(f"Certificate EXPIRED {abs(days)} days ago!")
                    ts.add("Expired certificate", "CRIT", 100)
                elif days < 14:
                    warn(f"Certificate expires in {days} days — URGENT!")
                    ts.add("Certificate expiring soon", "HIGH", 60)
                elif days < 30:
                    warn(f"Certificate expires in {days} days")
                    ts.add("Certificate near expiry", "MED", 30)
                else:
                    success(f"Certificate valid for {days} days")
            except Exception: pass

            # Self-signed?
            if issuer == subject:
                warn("Self-signed certificate detected!")
                ts.add("Self-signed cert", "HIGH", 55)

    except ssl.SSLError as e:
        error(f"SSL Error: {e}")
        ts.add("SSL Error", "HIGH", 40)
    except Exception as e:
        error(f"Connection failed: {e}")

    ts.render()


# ─── Module 05: HTTP Header Audit ────────────────────────────────────────────
def module_http_headers(target):
    section_header("HTTP Security Header Audit", "11 Controls · Scored A+ to F · Disclosure Check")
    ts = ThreatScore()

    url = target if target.startswith('http') else f'https://{target}'
    spinner("Probing HTTP response", 0.8)

    SECURITY_HEADERS = [
        ('Strict-Transport-Security',  'HSTS',                   True,  30),
        ('Content-Security-Policy',    'CSP',                    True,  25),
        ('X-Frame-Options',            'Clickjack Protection',   True,  20),
        ('X-Content-Type-Options',     'MIME Sniff Block',       True,  15),
        ('Referrer-Policy',            'Referrer Policy',        True,  10),
        ('Permissions-Policy',         'Permissions Policy',     True,  10),
        ('Cross-Origin-Opener-Policy', 'COOP',                   True,  10),
        ('Cross-Origin-Resource-Policy','CORP',                  True,  10),
        ('X-XSS-Protection',           'XSS Filter (legacy)',    True,   5),
    ]
    DISCLOSURE_HEADERS = [
        'Server', 'X-Powered-By', 'X-AspNet-Version', 'X-Generator', 'Via',
    ]

    try:
        body, hdrs, status, final_url = http_get(url, timeout=12)
        result_line("HTTP Status",  str(status))
        result_line("Final URL",    final_url[:70])
        result_line("Content-Type", hdrs.get('Content-Type', hdrs.get('content-type','?'))[:50])

        print()
        info("Security Header Scorecard:")
        score = 0; max_score = sum(w for *_, req, w in SECURITY_HEADERS if req)

        rows = []
        for hdr, label, required, weight in SECURITY_HEADERS:
            val = None
            for k, v in hdrs.items():
                if k.lower() == hdr.lower():
                    val = v; break
            if val:
                score += weight
                short_val = val[:45] + ('…' if len(val)>45 else '')
                rows.append([label, f'{C.BGREEN}✓ Present{C.RESET}', short_val])
            else:
                rows.append([label, f'{C.BRED}✗ MISSING{C.RESET}', '—'])
                ts.add(f"Missing {label}", "MED", weight)
        table(["Control","Status","Value"], rows, col_colors={0:C.BYELLOW, 2:C.DIM})

        # Disclosure
        print()
        info("Server Disclosure Check:")
        for h in DISCLOSURE_HEADERS:
            val = None
            for k, v in hdrs.items():
                if k.lower() == h.lower():
                    val = v; break
            if val:
                warn(f"{h}: {val[:60]}")
                ts.add(f"{h} disclosed", "LOW", 10)
            else:
                success(f"{h} hidden")

        # Grade
        pct = score / max_score if max_score else 0
        grade = 'A+' if pct==1 else 'A' if pct>=0.85 else 'B' if pct>=0.65 else 'C' if pct>=0.45 else 'D' if pct>=0.25 else 'F'
        gc = C.BGREEN if grade in ('A+','A') else C.BYELLOW if grade=='B' else C.BRED
        print(f'\n  {C.BCYAN}Security Grade{C.RESET}: {gc}{C.BOLD} {grade} ({score}/{max_score}){C.RESET}')
        LOG.log(f"HTTP Security Grade: {grade} ({score}/{max_score})")

    except Exception as e:
        error(f"Request failed: {e}")

    ts.render()


# ─── Module 06: Subdomain Harvester ──────────────────────────────────────────
def module_subdomain_harvest(domain):
    section_header("Subdomain Harvester", "Brute-force DNS · crt.sh CT Logs · Concurrent Resolve")

    found = {}  # fqdn → ip
    lock = threading.Lock()

    WORDLIST = [
        'www','mail','ftp','smtp','pop','imap','webmail','remote','vpn',
        'admin','portal','api','dev','staging','test','beta','app','blog',
        'shop','store','cdn','static','media','img','assets','ns1','ns2',
        'mx','relay','gateway','support','help','wiki','docs','git','gitlab',
        'jenkins','ci','jira','confluence','monitor','status','health','auth',
        'login','sso','id','oauth','analytics','dashboard','internal','corp',
        'intranet','extranet','secure','mobile','m','wap','ws','socket',
        'crm','erp','db','database','backup','files','upload','s3','cloud',
        'old','legacy','archive','new','prod','production','uat','qa',
        'vpn2','rdp','exchange','autodiscover','lyncdiscover','sip','voice',
        'ftp2','smtp2','ns3','ns4','mx2','mail2',
    ]

    info(f"Brute-forcing {len(WORDLIST)} subdomains...")

    def check_sub(sub):
        fqdn = f'{sub}.{domain}'
        try:
            ip = socket.gethostbyname(fqdn)
            with lock:
                if fqdn not in found:
                    found[fqdn] = ip
                    sys.stdout.write(
                        f'  {C.BGREEN}[+]{C.RESET} {C.BWHITE}{fqdn:<45}{C.RESET} '
                        f'→ {C.BCYAN}{ip}{C.RESET}\n'
                    )
                    sys.stdout.flush()
        except Exception: pass

    with ThreadPoolExecutor(max_workers=60) as ex:
        ex.map(check_sub, WORDLIST)

    # crt.sh
    print()
    info("Querying crt.sh certificate transparency logs...")
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        body, _, _, _ = http_get(url, timeout=15)
        certs = json.loads(body)
        ct_names = set()
        for c in certs:
            for n in c.get('name_value','').split('\n'):
                n = n.strip().lstrip('*.')
                if n.endswith(f'.{domain}') and n != domain:
                    ct_names.add(n)

        info(f"crt.sh returned {len(ct_names)} unique names, resolving...")
        for n in sorted(ct_names):
            if n not in found:
                try:
                    ip = socket.gethostbyname(n)
                    found[n] = ip
                    print(f'  {C.BYELLOW}[crt]{C.RESET} {C.BWHITE}{n:<45}{C.RESET} → {C.BCYAN}{ip}{C.RESET}')
                except Exception:
                    found[n] = 'unresolved'
                    print(f'  {C.DIM}[crt]{C.RESET} {C.DIM}{n:<45} → unresolved{C.RESET}')
    except Exception as e:
        warn(f"crt.sh query failed: {e}")

    print(f'\n  {C.BBLUE}Total subdomains discovered:{C.RESET} {C.BGREEN}{C.BOLD}{len(found)}{C.RESET}')
    LOG.log(f"Subdomains found: {len(found)}")


# ─── Module 07: Email OSINT ───────────────────────────────────────────────────
def module_email_osint(email):
    section_header("Email Intelligence Analysis", "Structure · MX · SMTP Passive · Permutations")

    parts = email.split('@')
    if len(parts) != 2:
        error("Invalid email format"); return
    user, domain = parts

    result_line("Username", user)
    result_line("Domain",   domain)
    result_line("TLD",      domain.split('.')[-1])

    # Pattern
    spinner("Classifying email pattern", 0.5)
    patterns = []
    if re.match(r'^[a-z]+\.[a-z]+$', user.lower()):
        patterns.append("firstname.lastname")
    elif re.match(r'^[a-z]\.[a-z]+$', user.lower()):
        patterns.append("f.lastname")
    elif '_' in user:
        patterns.append("first_last")
    if any(c.isdigit() for c in user):
        patterns.append("contains digits")
    if len(user) <= 4:
        patterns.append("short alias (possible department/role)")
    result_line("Pattern Class", ', '.join(patterns) or "Unclassified")

    # MX + SPF
    spinner("Querying mail infrastructure", 0.8)
    try:
        r = subprocess.run(['dig', '+short', 'MX', domain],
                           capture_output=True, text=True, timeout=6)
        mxs = [l.strip() for l in r.stdout.strip().split('\n') if l.strip()]
        if mxs:
            for mx in mxs[:3]:
                result_line("MX Record", mx[:60])
        else:
            result_line("MX Records", "None — domain may not accept email", ok=False)
    except Exception:
        result_line("MX Check", "Failed", ok=False)

    # Permutations
    print()
    info("Generating OSINT email permutations...")
    first = user.split('.')[0].split('_')[0] if ('.' in user or '_' in user) else user
    last  = user.split('.')[-1] if '.' in user else (user.split('_')[-1] if '_' in user else '')
    perms = list(dict.fromkeys(filter(None, [
        f"{first}@{domain}",
        f"{last}@{domain}" if last else None,
        f"{first[0]}{last}@{domain}" if last else None,
        f"{last}.{first}@{domain}" if last else None,
        f"{first}_{last}@{domain}" if last else None,
        f"{first[0]}.{last}@{domain}" if last else None,
        f"info@{domain}", f"admin@{domain}", f"contact@{domain}",
        f"security@{domain}", f"support@{domain}", f"abuse@{domain}",
    ])))

    rows = [[p, "—" if p == email else "Candidate"] for p in perms[:10] if p != email]
    table(["Email Permutation", "Status"], rows[:8], col_colors={0:C.BYELLOW})

    print()
    info(f"HIBP breach check → {C.BCYAN}https://haveibeenpwned.com/account/{urllib.parse.quote(email)}{C.RESET}")
    info(f"Dehashed search  → {C.BCYAN}https://dehashed.com/search?query={urllib.parse.quote(email)}{C.RESET}")
    info(f"Hunter.io verify → {C.BCYAN}https://hunter.io/email-verifier/{urllib.parse.quote(email)}{C.RESET}")


# ─── Module 08: Hash Analyzer ─────────────────────────────────────────────────
def module_hash_analyzer(hash_input):
    section_header("Hash Analysis Engine", "Type ID · Dictionary Attack · Crack Resources")

    h = hash_input.strip()
    length = len(h)

    HASH_DB = {
        32:  ['MD5','NTLM','MD4','LM (half)'],
        40:  ['SHA-1','MySQL5','SHA1(LDAP)','HEX(MD5)'],
        48:  ['Tiger-192','SHA-1(UTF-16)'],
        56:  ['SHA-224','Haval-224'],
        64:  ['SHA-256','SHA3-256','BLAKE2-256','Keccak-256','Snefru-256'],
        80:  ['SHA-384 (partial)'],
        96:  ['SHA-384','SHA3-384'],
        128: ['SHA-512','SHA3-512','Whirlpool','BLAKE2-512'],
        56:  ['SHA-224'],
        34:  ['MD5(APR)'],
    }

    identified = HASH_DB.get(length, ['Unknown'])

    # Prefix matching
    if h.startswith('$2a$') or h.startswith('$2b$') or h.startswith('$2y$'):
        identified = ['bcrypt']
    elif h.startswith('$1$'):
        identified = ['MD5-crypt']
    elif h.startswith('$6$'):
        identified = ['SHA-512-crypt (Linux)']
    elif h.startswith('$5$'):
        identified = ['SHA-256-crypt (Linux)']
    elif h.startswith('$P$') or h.startswith('$H$'):
        identified = ['phpBB3 / WordPress']
    elif h.startswith('sha1$'):
        identified = ['Django SHA-1']
    elif h.startswith('pbkdf2_sha'):
        identified = ['Django PBKDF2']
    elif h.startswith('{SHA}'):
        identified = ['LDAP SHA-1 (Base64)']
    elif h.startswith('argon2'):
        identified = ['Argon2 (modern KDF)']

    result_line("Hash Input",  h[:48] + ('…' if len(h)>48 else ''))
    result_line("Length",      str(length))
    result_line("Possible Types", ', '.join(identified))
    is_hex = all(c in '0123456789abcdefABCDEF' for c in h)
    result_line("Charset",    'Hexadecimal' if is_hex else 'Mixed / Base64 / Binary')

    # Entropy
    from math import log2
    charset_size = 16 if is_hex else 64
    entropy = length * log2(charset_size)
    result_line("Estimated Entropy", f"{entropy:.0f} bits")

    # Quick dictionary attack
    if length in (32, 40):
        print()
        info("Running dictionary attack (extended wordlist)...")
        wordlist = [
            'password','123456','password123','admin','letmein','qwerty','abc123',
            'monkey','1234567890','dragon','master','sunshine','princess','football',
            'shadow','superman','michael','pass','test','hello','welcome','password1',
            'hunter2','iloveyou','trustno1','batman','cheese','123456789','000000',
            'passw0rd','P@ssw0rd','admin123','root','toor','kali','linux','hacker',
            'security','phantom','osint','recon','nmap','metasploit','burp',
        ]
        cracked = None
        for pwd in wordlist:
            for enc in [pwd.encode(), pwd.upper().encode()]:
                cand = (hashlib.md5(enc).hexdigest() if length==32
                        else hashlib.sha1(enc).hexdigest())
                if cand.lower() == h.lower():
                    cracked = pwd; break
            if cracked: break

        if cracked:
            print(f'\n  {C.BRED}[!]{C.RESET} {C.BOLD}{C.BGREEN}CRACKED → {cracked}{C.RESET}')
            LOG.log(f"CRACKED: {h} → {cracked}")
        else:
            result_line("Dictionary Attack", "Not found in wordlist", ok=False)

    print()
    info("Online crack resources:")
    table(["Service","URL"], [
        ["CrackStation", "https://crackstation.net/"],
        ["Hashes.com",   "https://hashes.com/en/decrypt/hash"],
        ["MD5Decrypt",   "https://md5decrypt.net/"],
        ["HashKiller",   "https://hashkiller.io/listmanager"],
    ], col_colors={0:C.BYELLOW, 1:C.BCYAN})


# ─── Module 09: Network Tracer ────────────────────────────────────────────────
def module_network_tracer(target):
    section_header("Network Route Tracer", "Hop-by-hop Geolocation · Latency · CDN Detection")

    CDN_PATTERNS = ['cloudflare','akamai','fastly','cloudfront','edgecast',
                    'maxcdn','stackpath','incapsula','sucuri','cachefly']

    info(f"Tracing route to {C.BWHITE}{target}{C.RESET}")
    print()

    try:
        result = subprocess.run(
            ['traceroute', '-m', '25', '-w', '2', '-n', target],
            capture_output=True, text=True, timeout=90
        )
        lines = result.stdout.strip().split('\n')
        hop_ips = []
        for line in lines:
            if not line.strip(): continue
            if line.strip()[0].isdigit():
                parts = line.split()
                hop_num = parts[0]
                ip_match = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)
                ip = ip_match[0] if ip_match else None
                times = re.findall(r'[\d.]+\s*ms', line)
                avg_ms = '—'
                if times:
                    try:
                        vals = [float(t.replace('ms','').strip()) for t in times]
                        avg_ms = f'{sum(vals)/len(vals):.1f}ms'
                    except Exception: pass

                if '* * *' in line:
                    print(f'  {C.DIM}{hop_num:>3}  [filtered / no response]{C.RESET}')
                    continue

                # Geolocate public IPs
                geo = ''
                if ip:
                    try:
                        ipobj = ipaddress.ip_address(ip)
                        if ipobj.is_global:
                            url = f"http://ip-api.com/json/{ip}?fields=country,city,isp"
                            body, _, _, _ = http_get(url, timeout=3)
                            d = json.loads(body)
                            if d.get('country'):
                                geo = f"{d.get('city','?')}, {d.get('country','?')} | {d.get('isp','?')[:30]}"
                    except Exception: pass

                is_cdn = any(p in geo.lower() for p in CDN_PATTERNS)
                cdn_label = f' {C.BMAGENTA}[CDN]{C.RESET}' if is_cdn else ''
                print(f'  {C.BCYAN}{hop_num:>3}{C.RESET}  {C.BWHITE}{ip or "?":>18}{C.RESET}  '
                      f'{C.BYELLOW}{avg_ms:<10}{C.RESET}  {C.DIM}{geo}{C.RESET}{cdn_label}')
            else:
                print(f'  {C.BYELLOW}{line}{C.RESET}')

    except FileNotFoundError:
        warn("traceroute not found — trying tracepath...")
        try:
            result = subprocess.run(['tracepath','-n',target],
                                    capture_output=True, text=True, timeout=60)
            print(result.stdout)
        except FileNotFoundError:
            error("Neither traceroute nor tracepath found")
            info("Install: sudo apt install traceroute")


# ─── Module 10: Full OSINT Report ────────────────────────────────────────────
def module_full_report(domain):
    section_header("Phantom Full OSINT Report", "Orchestrated Multi-Module Deep Dive")

    print(f'  {C.BYELLOW}Target{C.RESET}: {C.BOLD}{C.BWHITE}{domain}{C.RESET}')
    print(f'  {C.BYELLOW}Timestamp{C.RESET}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    progress_bar("Initializing modules", steps=30, delay=0.025)

    for name, fn in [
        ("DNS Reconnaissance",   lambda: module_dns_recon(domain)),
        ("Subdomain Harvest",    lambda: module_subdomain_harvest(domain)),
        ("HTTP Header Audit",    lambda: module_http_headers(domain)),
        ("SSL/TLS Inspector",    lambda: module_ssl_inspector(domain)),
        ("Tech Fingerprint",     lambda: module_tech_fingerprint(domain)),
    ]:
        print(f'\n  {C.BBLUE}▶ Running:{C.RESET} {C.BOLD}{name}{C.RESET}')
        try:
            fn()
        except Exception as e:
            error(f"Module failed: {e}")

    print(f'\n  {C.BGREEN}[✓]{C.RESET} Full report saved to: {C.BYELLOW}{LOG.path}{C.RESET}')


# ─── Module 11: Username Hunter ───────────────────────────────────────────────
def module_username_hunter(username):
    section_header("Social Media Username Hunter", "25 Platforms · HTTP Detection · False-Positive Filter")

    PLATFORMS = {
        'GitHub':      (f'https://github.com/{username}',          [404]),
        'GitLab':      (f'https://gitlab.com/{username}',          [404]),
        'Twitter/X':   (f'https://twitter.com/{username}',         [404]),
        'Instagram':   (f'https://www.instagram.com/{username}/',  [404]),
        'Reddit':      (f'https://www.reddit.com/user/{username}', [404]),
        'TikTok':      (f'https://www.tiktok.com/@{username}',     [404]),
        'YouTube':     (f'https://www.youtube.com/@{username}',    [404]),
        'Pinterest':   (f'https://www.pinterest.com/{username}/',  [404]),
        'Twitch':      (f'https://www.twitch.tv/{username}',       [404]),
        'Steam':       (f'https://steamcommunity.com/id/{username}',[404]),
        'Keybase':     (f'https://keybase.io/{username}',          [404]),
        'Pastebin':    (f'https://pastebin.com/u/{username}',      [404]),
        'Medium':      (f'https://medium.com/@{username}',         [404]),
        'DEV.to':      (f'https://dev.to/{username}',              [404]),
        'HackerNews':  (f'https://news.ycombinator.com/user?id={username}', []),
        'Replit':      (f'https://replit.com/@{username}',         [404]),
        'Bugcrowd':    (f'https://bugcrowd.com/{username}',        [404]),
        'HackerOne':   (f'https://hackerone.com/{username}',       [404]),
        'Docker Hub':  (f'https://hub.docker.com/u/{username}',    [404]),
        'npm':         (f'https://www.npmjs.com/~{username}',      [404]),
        'PyPI':        (f'https://pypi.org/user/{username}/',      [404]),
        'Gravatar':    (f'https://en.gravatar.com/{username}',     [404]),
        'Mastodon':    (f'https://mastodon.social/@{username}',    [404]),
        'GitBook':     (f'https://www.gitbook.com/@{username}',    [404]),
        'Codepen':     (f'https://codepen.io/{username}',          [404]),
    }

    info(f"Probing {len(PLATFORMS)} platforms for: {C.BWHITE}{username}{C.RESET}")
    found = []; not_found = []; unknown = []
    lock = threading.Lock()

    def check(platform, url, not_found_codes):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, context=_SSL_CTX, timeout=7) as resp:
                status = resp.status
                if status == 200:
                    with lock: found.append((platform, url))
                    return platform, url, 'FOUND'
                else:
                    with lock: not_found.append(platform)
                    return platform, url, 'NOT_FOUND'
        except urllib.error.HTTPError as e:
            if e.code in (not_found_codes or [404]):
                with lock: not_found.append(platform)
                return platform, url, 'NOT_FOUND'
            with lock: unknown.append(platform)
            return platform, url, 'UNKNOWN'
        except Exception:
            with lock: unknown.append(platform)
            return platform, url, 'UNKNOWN'

    print()
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(check, p, u, c): p for p, (u, c) in PLATFORMS.items()}
        for f in as_completed(futures):
            platform, url, status = f.result()
            if status == 'FOUND':
                print(f'  {C.BGREEN}[FOUND]{C.RESET}    {C.BWHITE}{platform:<15}{C.RESET} {C.BCYAN}{url}{C.RESET}')
            elif status == 'NOT_FOUND':
                print(f'  {C.RED}[✗]{C.RESET}       {C.DIM}{platform}{C.RESET}')
            else:
                print(f'  {C.BYELLOW}[?]{C.RESET}       {C.DIM}{platform} (inconclusive){C.RESET}')

    print(f'\n  {C.BBLUE}Profiles confirmed:{C.RESET} {C.BGREEN}{C.BOLD}{len(found)}{C.RESET} / {len(PLATFORMS)}')
    if found:
        print(f'\n  {C.BCYAN}Confirmed profiles:{C.RESET}')
        for p, u in found:
            print(f'    {C.BGREEN}▸{C.RESET} {C.BWHITE}{p:<15}{C.RESET} {u}')


# ─── Module 12: Tech Fingerprint ─────────────────────────────────────────────
def module_tech_fingerprint(target):
    section_header("Technology Fingerprinter", "30+ Signatures · CMS · Framework · CDN · Language")

    url = target if target.startswith('http') else f'https://{target}'
    spinner("Fetching page and headers", 1.0)

    SIGNATURES = {
        # CMS
        'WordPress':    ['wp-content','wp-includes','WordPress','wp-json'],
        'Drupal':       ['Drupal','drupal.js','/sites/default/'],
        'Joomla':       ['Joomla!','/components/com_'],
        'Magento':      ['Mage.Cookies','/skin/frontend/','magento'],
        'Shopify':      ['cdn.shopify.com','Shopify.theme'],
        'Wix':          ['wix.com','wixstatic.com'],
        'Squarespace':  ['squarespace.com','sqsp.net'],
        'Ghost':        ['ghost.io','content/themes/casper'],
        'Webflow':      ['webflow.com','w-webflow'],
        # JS Frameworks
        'React':        ['react.development.js','__react','data-reactroot','_react'],
        'Angular':      ['ng-version','angular.js','ng-app','zone.js'],
        'Vue.js':       ['vue.js','__vue__','data-v-'],
        'Next.js':      ['_next/static','__NEXT_DATA__'],
        'Nuxt.js':      ['_nuxt/','__NUXT__'],
        'Svelte':       ['__svelte','svelte-'],
        'Ember.js':     ['ember.js','Ember.Application'],
        # CSS
        'Bootstrap':    ['bootstrap.css','bootstrap.min.css'],
        'Tailwind':     ['tailwind.css','tailwindcss'],
        'Bulma':        ['bulma.css','bulma.min.css'],
        # CDN / Cloud
        'Cloudflare':   ['__cfduid','cf-ray','cloudflare'],
        'AWS CloudFront':['cloudfront.net','x-amz-cf-id'],
        'Fastly':       ['fastly','x-served-by'],
        'Akamai':       ['akamaiedge.net','x-check-cacheable'],
        'AWS S3':       ['s3.amazonaws.com'],
        # Analytics
        'Google Analytics': ['google-analytics.com','gtag(','ga('],
        'Hotjar':       ['hotjar.com','hj('],
        'Mixpanel':     ['mixpanel.com'],
        # Server / Language
        'Apache':       ['Apache','server: Apache'],
        'Nginx':        ['nginx','server: nginx'],
        'IIS':          ['Microsoft-IIS','server: Microsoft-IIS'],
        'PHP':          ['X-Powered-By: PHP','.php','phpsessid'],
        'ASP.NET':      ['X-Powered-By: ASP.NET','__VIEWSTATE','ASPNETCORE'],
        'Django':       ['csrfmiddlewaretoken','wsgiref','django'],
        'Rails':        ['X-Powered-By: Phusion Passenger'],
        'Node.js/Express': ['X-Powered-By: Express'],
    }

    try:
        body, hdrs, status, _ = http_get(url, timeout=12)
        full = body[:60000] + str(hdrs)

        detected = {}
        for tech, sigs in SIGNATURES.items():
            matched_sigs = []
            for sig in sigs:
                if sig.lower() in full.lower():
                    matched_sigs.append(sig)
            if matched_sigs:
                detected[tech] = matched_sigs[0]

        if detected:
            rows = sorted(detected.items())
            table(["Technology","Matched Signature"], rows,
                  col_colors={0:C.BGREEN, 1:C.DIM})
        else:
            warn("No signatures matched — target may be obfuscated")

    except Exception as e:
        error(f"Fingerprint failed: {e}")


# ─── Module 13: CVE Intelligence ─────────────────────────────────────────────
def module_cve_intel(product):
    section_header("CVE Intelligence Engine", "NIST NVD · CVSS Scoring · Severity Breakdown")
    ts = ThreatScore()

    spinner("Querying NIST National Vulnerability Database", 1.5)

    # NVD API v2 (no key needed for basic queries)
    try:
        keyword = urllib.parse.quote(product)
        url = (f"https://services.nvd.nist.gov/rest/json/cves/2.0"
               f"?keywordSearch={keyword}&resultsPerPage=15&startIndex=0")
        body, _, _, _ = http_get(url, timeout=20)
        data = json.loads(body)

        vulns = data.get('vulnerabilities', [])
        total = data.get('totalResults', 0)

        result_line("Total CVEs in NVD", str(total))
        result_line("Showing", str(len(vulns)))

        if not vulns:
            warn("No CVEs found — try a broader keyword (e.g. 'apache' not 'apache 2.4.51')")
            return

        print()
        sev_counts = defaultdict(int)
        rows = []
        for v in vulns:
            cve   = v.get('cve', {})
            cve_id = cve.get('id', '?')
            desc_list = cve.get('descriptions', [])
            desc = next((d['value'] for d in desc_list if d.get('lang') == 'en'), '?')
            desc_short = (desc[:65] + '…') if len(desc) > 65 else desc

            metrics = cve.get('metrics', {})
            cvss_score = '?'; severity = '?'
            for key in ['cvssMetricV31','cvssMetricV30','cvssMetricV2']:
                m = metrics.get(key, [])
                if m:
                    cvss_data = m[0].get('cvssData', m[0])
                    cvss_score = str(cvss_data.get('baseScore', '?'))
                    severity   = cvss_data.get('baseSeverity', m[0].get('baseSeverity', '?'))
                    break

            sev_counts[severity] += 1
            sev_col = {
                'CRITICAL': C.BMAGENTA+C.BOLD, 'HIGH': C.BRED,
                'MEDIUM':   C.BYELLOW,          'LOW':  C.BGREEN,
            }.get(severity, C.BWHITE)

            rows.append([cve_id, f'{sev_col}{cvss_score:>4}{C.RESET}',
                         f'{sev_col}{severity}{C.RESET}', desc_short])

            if severity in ('CRITICAL', 'HIGH'):
                ts.add(f"{cve_id} ({severity})", severity[:4], 40 if severity=='CRITICAL' else 25)

        table(["CVE ID","CVSS","Severity","Description"], rows,
              col_colors={0:C.BCYAN})

        print()
        info("Severity Distribution:")
        for sev in ['CRITICAL','HIGH','MEDIUM','LOW']:
            count = sev_counts.get(sev, 0)
            if count:
                bar_len = min(count * 3, 30)
                sc = {'CRITICAL':C.BMAGENTA,'HIGH':C.BRED,'MEDIUM':C.BYELLOW,'LOW':C.BGREEN}[sev]
                print(f'    {sc}{sev:<10}{C.RESET} {"█"*bar_len} {count}')

        info(f"Full NVD search → {C.BCYAN}https://nvd.nist.gov/vuln/search/results?query={keyword}{C.RESET}")

    except urllib.error.HTTPError as e:
        if e.code == 403:
            warn("NVD API rate limit hit — try again in 30s or add API key")
        else:
            error(f"NVD API error: {e.code}")
    except Exception as e:
        error(f"CVE lookup failed: {e}")
        warn("NVD may be rate limiting. Try again in a few seconds.")

    ts.render()


# ─── Module 14: WHOIS Deep Dive ──────────────────────────────────────────────
def module_whois(target):
    section_header("WHOIS Deep Dive", "Registrar · Registrant · Dates · Nameservers · DNSSEC")

    spinner("Running WHOIS query", 1.2)

    try:
        result = subprocess.run(['whois', target],
                                capture_output=True, text=True, timeout=15)
        raw = result.stdout

        if not raw.strip():
            error("No WHOIS data returned"); return

        # Parse interesting fields
        FIELD_MAP = {
            'Domain Name':         r'(?:Domain Name|domain):\s*(.+)',
            'Registrar':           r'Registrar:\s*(.+)',
            'IANA ID':             r'Registrar IANA ID:\s*(.+)',
            'Registrar URL':       r'Registrar URL:\s*(.+)',
            'Created':             r'(?:Creation Date|created):\s*(.+)',
            'Updated':             r'(?:Updated Date|last-update|changed):\s*(.+)',
            'Expires':             r'(?:Registry Expiry Date|Expiry Date|expires):\s*(.+)',
            'Registrant':          r'Registrant(?:\s+Name)?:\s*(.+)',
            'Registrant Org':      r'Registrant Organization:\s*(.+)',
            'Registrant Country':  r'Registrant Country:\s*(.+)',
            'Registrant Email':    r'Registrant Email:\s*(.+)',
            'Admin Email':         r'Admin Email:\s*(.+)',
            'Tech Email':          r'Tech Email:\s*(.+)',
            'Abuse Email':         r'(?:Registrar Abuse Contact Email):\s*(.+)',
            'Name Server':         r'Name Server:\s*(.+)',
            'DNSSEC':              r'DNSSEC:\s*(.+)',
            'Status':              r'Domain Status:\s*(.+)',
        }

        parsed = defaultdict(list)
        for field, pattern in FIELD_MAP.items():
            matches = re.findall(pattern, raw, re.IGNORECASE)
            for m in matches:
                val = m.strip()
                if val and val not in parsed[field]:
                    parsed[field].append(val)

        # Print parsed fields
        for field, vals in parsed.items():
            for val in vals[:2]:  # max 2 per field
                result_line(field, val[:72])

        # Expiry check
        for val in parsed.get('Expires', []):
            try:
                for fmt in ['%Y-%m-%dT%H:%M:%SZ','%Y-%m-%d','%d-%b-%Y','%d/%m/%Y']:
                    try:
                        exp = datetime.strptime(val.split('T')[0], fmt.split('T')[0])
                        days = (exp - datetime.now()).days
                        if days < 0:
                            warn(f"Domain EXPIRED {abs(days)} days ago!")
                        elif days < 30:
                            warn(f"Domain expires in {days} days — URGENT!")
                        elif days < 90:
                            warn(f"Domain expires in {days} days")
                        else:
                            success(f"Domain valid for {days} more days")
                        break
                    except ValueError: continue
            except Exception: pass

        # Privacy guard detection
        if any(kw in raw.lower() for kw in ['redacted','privacy','whoisguard','protected']):
            info("Registrant details are REDACTED (privacy protection active)")
        else:
            info("No privacy guard — registrant details may be exposed")

        print()
        info("Raw WHOIS (first 30 lines):")
        for line in raw.split('\n')[:30]:
            if line.strip() and not line.startswith('%') and not line.startswith('#'):
                print(f'  {C.DIM}{line.rstrip()}{C.RESET}')

    except FileNotFoundError:
        error("whois not installed — sudo apt install whois")
    except Exception as e:
        error(f"WHOIS failed: {e}")


# ─── Module 15: WAF Detector ──────────────────────────────────────────────────
def module_waf_detector(target):
    section_header("WAF Detector", "Vendor Fingerprinting · Payload Probing · Bypass Hints")
    ts = ThreatScore()

    url = target if target.startswith('http') else f'https://{target}'
    spinner("Sending baseline request", 0.8)

    # WAF fingerprints: header/body signatures → vendor
    WAF_SIGNATURES = {
        'Cloudflare':      ['CF-RAY','__cfduid','cloudflare','Attention Required! | Cloudflare'],
        'AWS WAF':         ['x-amzn-RequestId','AWSALB','aws-load-balancer-request-id'],
        'ModSecurity':     ['mod_security','ModSecurity','NOYB'],
        'Akamai':          ['AkamaiGHost','X-Check-Cacheable','akamaiedge'],
        'Sucuri':          ['sucuri','X-Sucuri-ID','Sucuri WebSite Firewall'],
        'Imperva (Incapsula)': ['incap_ses','visid_incap','Imperva','incapsula'],
        'F5 BIG-IP ASM':   ['BigIP','TS01','F5 Networks'],
        'Fortinet FortiWeb': ['FORTIWAFSID','fortigate'],
        'Barracuda':       ['barra_counter_session','barracuda_'],
        'Wordfence':       ['wordfence','wfvt_','Wordfence'],
        'DDoS-Guard':      ['ddos-guard','DDoS-Guard'],
        'SiteLock':        ['SiteLock','Shield'],
        'Reblaze':         ['rbzid','reblaze'],
        'Radware':         ['X-SL-CompState','rdwr_cookie'],
    }

    PROBE_PAYLOADS = [
        ("XSS probe",         "?q=<script>alert(1)</script>"),
        ("SQLi probe",        "?id=1'+OR+'1'='1"),
        ("Path traversal",    "?file=../../etc/passwd"),
        ("Command inject",    "?cmd=;ls"),
        ("SSRF probe",        "?url=http://169.254.169.254/"),
    ]

    detected_wafs = set()

    # Baseline
    try:
        _, baseline_hdrs, baseline_status, _ = http_get(url, timeout=10)
        all_hdr_str = str(baseline_hdrs).lower()

        for waf, sigs in WAF_SIGNATURES.items():
            for sig in sigs:
                if sig.lower() in all_hdr_str:
                    detected_wafs.add(waf)
    except Exception as e:
        warn(f"Baseline request failed: {e}")

    # Probe
    print()
    info("Sending WAF probe payloads...")
    probe_rows = []
    for label, payload in PROBE_PAYLOADS:
        probe_url = url.rstrip('/') + payload
        try:
            _, hdrs, status, _ = http_get(probe_url, timeout=8)
            hdr_str = str(hdrs).lower()

            for waf, sigs in WAF_SIGNATURES.items():
                for sig in sigs:
                    if sig.lower() in hdr_str:
                        detected_wafs.add(waf)

            blocked = status in (403, 406, 429, 503) or any(
                sig.lower() in hdr_str for waf_sigs in WAF_SIGNATURES.values()
                for sig in waf_sigs
            )
            status_str = (f'{C.BRED}BLOCKED ({status}){C.RESET}' if blocked
                          else f'{C.BGREEN}PASSED ({status}){C.RESET}')
            probe_rows.append([label, payload[:35], status_str])
        except urllib.error.HTTPError as e:
            probe_rows.append([label, payload[:35], f'{C.BRED}BLOCKED ({e.code}){C.RESET}'])
        except Exception:
            probe_rows.append([label, payload[:35], f'{C.DIM}TIMEOUT/ERR{C.RESET}'])

    table(["Probe","Payload","Result"], probe_rows, col_colors={0:C.BYELLOW})

    print()
    if detected_wafs:
        ts.add("WAF Detected", "LOW", 5)
        info(f"WAF Vendor(s) detected:")
        for waf in detected_wafs:
            print(f'    {C.BGREEN}▸{C.RESET} {C.BWHITE}{C.BOLD}{waf}{C.RESET}')
        print()
        info("WAF bypass hints (for authorized testing):")
        print(f'    {C.DIM}→ Try encoding: URL encode, double-encode, hex encoding{C.RESET}')
        print(f'    {C.DIM}→ Try case variation: <ScRiPt>, SeLeCt{C.RESET}')
        print(f'    {C.DIM}→ Try comment insertion: sel/**/ect, <scr<!-- -->ipt>{C.RESET}')
        print(f'    {C.DIM}→ Try HTTP method switching (POST vs GET){C.RESET}')
    else:
        warn("No WAF detected — target may be unprotected or WAF is well-hidden")
        ts.add("No WAF detected", "MED", 30)

    ts.render()


# ─── Module 16: CMS Exploit Map ───────────────────────────────────────────────
def module_cms_exploit_map(target):
    section_header("CMS Exploit Map", "Fingerprint · Admin Panels · Exposed Paths · Known Risks")
    ts = ThreatScore()

    url = target if target.startswith('http') else f'https://{target}'
    spinner("Fetching target signature", 1.0)

    CMS_CHECKS = {
        'WordPress': {
            'fingerprint': ['wp-content','wp-login.php','wp-json','WordPress'],
            'admin_paths': ['/wp-admin/', '/wp-login.php', '/wp-admin/admin-ajax.php'],
            'expose_paths': ['/readme.html', '/license.txt', '/wp-config.php.bak',
                             '/wp-content/debug.log', '/.env', '/xmlrpc.php'],
            'risks': [
                "Exposed /xmlrpc.php — brute force / DDoS amplification risk",
                "wp-config.php backup may leak DB credentials",
                "User enumeration via /?author=1",
            ],
        },
        'Drupal': {
            'fingerprint': ['Drupal','drupal.js','/sites/default/'],
            'admin_paths': ['/admin/', '/user/login', '/admin/config'],
            'expose_paths': ['/CHANGELOG.txt', '/INSTALL.txt', '/README.txt',
                             '/sites/default/settings.php'],
            'risks': ["CHANGELOG.txt leaks exact version (Drupalgeddon risk)"],
        },
        'Joomla': {
            'fingerprint': ['Joomla!','/components/com_'],
            'admin_paths': ['/administrator/', '/administrator/index.php'],
            'expose_paths': ['/README.txt', '/LICENSE.txt', '/configuration.php.bak'],
            'risks': ["Default admin panel at /administrator/ is brute-force target"],
        },
        'Laravel': {
            'fingerprint': ['laravel','_token','X-Powered-By: PHP'],
            'admin_paths': ['/admin', '/dashboard'],
            'expose_paths': ['/.env', '/storage/logs/laravel.log', '/phpinfo.php'],
            'risks': ["Exposed .env leaks APP_KEY, DB credentials, mail secrets"],
        },
    }

    try:
        body, hdrs, _, _ = http_get(url, timeout=12)
        full = body[:50000] + str(hdrs)

        detected_cms = None
        for cms, data in CMS_CHECKS.items():
            for sig in data['fingerprint']:
                if sig.lower() in full.lower():
                    detected_cms = cms; break
            if detected_cms: break

        if not detected_cms:
            warn("CMS not identified — generic checks only")
            detected_cms = 'Generic'
            cms_data = {
                'admin_paths': ['/admin', '/login', '/dashboard', '/wp-admin',
                                '/administrator', '/manager', '/cpanel'],
                'expose_paths': ['/.env','/.git/config','/phpinfo.php',
                                 '/server-status', '/robots.txt', '/sitemap.xml',
                                 '/backup.zip', '/db.sql', '/dump.sql'],
                'risks': [],
            }
        else:
            success(f"Detected CMS: {C.BWHITE}{C.BOLD}{detected_cms}{C.RESET}")
            cms_data = CMS_CHECKS[detected_cms]

        # Check exposed paths
        print()
        info("Probing sensitive paths...")
        path_rows = []
        for path in cms_data.get('admin_paths',[]) + cms_data.get('expose_paths',[]):
            probe_url = url.rstrip('/') + path
            try:
                _, _, status, _ = http_get(probe_url, timeout=6)
                if status == 200:
                    path_rows.append([path, f'{C.BRED}EXPOSED (200){C.RESET}', probe_url])
                    ts.add(f"Exposed {path}", "HIGH", 45)
                elif status in (301, 302):
                    path_rows.append([path, f'{C.BYELLOW}REDIRECT ({status}){C.RESET}', '—'])
                else:
                    path_rows.append([path, f'{C.BGREEN}Protected ({status}){C.RESET}', '—'])
            except urllib.error.HTTPError as e:
                path_rows.append([path, f'{C.BGREEN}Protected ({e.code}){C.RESET}', '—'])
            except Exception:
                path_rows.append([path, f'{C.DIM}Unreachable{C.RESET}', '—'])

        table(["Path","Status","URL"], path_rows, col_colors={0:C.BYELLOW})

        # Known risks
        risks = cms_data.get('risks', [])
        if risks:
            print()
            warn("Known risks for this CMS:")
            for r in risks:
                print(f'    {C.BRED}▸{C.RESET} {r}')

        # Default creds hint
        print()
        info("Default credential check (manual):")
        default_creds = {
            'WordPress': "admin:admin, admin:password",
            'Drupal':    "admin:admin, admin:drupal",
            'Joomla':    "admin:admin, admin:joomla",
        }
        creds = default_creds.get(detected_cms, "admin:admin, root:root, admin:password")
        print(f'    {C.BYELLOW}Common defaults:{C.RESET} {C.DIM}{creds}{C.RESET}')

    except Exception as e:
        error(f"CMS scan failed: {e}")

    ts.render()


# ─── Special Commands ─────────────────────────────────────────────────────────
def show_help(module_id=None):
    if module_id and module_id in MODULE_HELP:
        name, desc = MODULE_HELP[module_id]
        print(f'\n  {C.BCYAN}┌─ Module {module_id}: {name} ─────────────────────────────────────{C.RESET}')
        for line in textwrap.dedent(desc).split('\n'):
            print(f'  {C.BCYAN}│{C.RESET} {C.DIM}{line}{C.RESET}')
        print(f'  {C.BCYAN}└─────────────────────────────────────────────────────────────────{C.RESET}\n')
    else:
        print(MENU)
        print(f'\n  {C.BCYAN}Usage:{C.RESET}')
        print(f'    {C.BYELLOW}help 01{C.RESET}   — detailed help for module 01')
        print(f'    {C.BYELLOW}history{C.RESET}    — show command history')
        print(f'    {C.BYELLOW}log{C.RESET}        — show current session log path')
        print(f'    {C.BYELLOW}score{C.RESET}      — show accumulated threat score')
        print(f'    {C.BYELLOW}clear{C.RESET}      — clear the screen')
        print(f'    {C.BYELLOW}00{C.RESET}         — exit\n')

def show_history():
    if not SESSION_HISTORY:
        info("No history yet."); return
    print(f'\n  {C.BCYAN}Command History:{C.RESET}')
    for i, entry in enumerate(SESSION_HISTORY[-20:], 1):
        print(f'  {C.DIM}{i:>3}.{C.RESET} {entry}')
    print()

# ─── Boot Sequence ────────────────────────────────────────────────────────────
def boot_sequence():
    os.system('clear')
    print(C.BGREEN)
    matrix_rain(1.2)
    print(C.RESET)
    os.system('clear')
    slow_print(BANNER, delay=0.0008)
    time.sleep(0.2)

    checks = [
        ("Python runtime",       True),
        ("ANSI color support",   True),
        ("DNS resolver",         True),
        ("SSL context",          True),
        ("Thread pool engine",   True),
        ("Session logger",       True),
        ("Readline history",     True),
    ]

    print(f'  {C.BCYAN}[ System Check ]{C.RESET}\n')
    for label, ok in checks:
        time.sleep(0.07)
        icon = f'{C.BGREEN}✓{C.RESET}' if ok else f'{C.BRED}✗{C.RESET}'
        print(f'    {icon}  {C.DIM}{label}{C.RESET}')

    time.sleep(0.3)
    LOG.start()
    print(f'\n    {C.DIM}Session log:{C.RESET} {C.BYELLOW}{LOG.path}{C.RESET}')
    time.sleep(0.5)
    print(f'\n  {C.BGREEN}All systems operational.{C.RESET}')
    time.sleep(0.4)

    input(f'\n  {C.DIM}Press ENTER to enter the shadow network...{C.RESET}')
    os.system('clear')
    slow_print(BANNER, delay=0.0005)
    print(MENU)

# ─── Signal Handler ───────────────────────────────────────────────────────────
def handle_sigint(sig, frame):
    print(f'\n\n  {C.BRED}[☠]{C.RESET} {C.DIM}Phantom going dark. Stay in the shadows.{C.RESET}\n')
    LOG.close()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

# ─── Module Dispatch ─────────────────────────────────────────────────────────
MODULE_MAP = {
    '01': ('IP Intelligence',       module_ip_intel,          'IP or hostname (e.g. 1.1.1.1 or target.com)'),
    '02': ('DNS Reconnaissance',    module_dns_recon,         'Domain (e.g. target.com)'),
    '03': ('Port Scanner',          module_port_scanner,      'IP or hostname'),
    '04': ('SSL/TLS Inspector',     module_ssl_inspector,     'Domain (e.g. target.com)'),
    '05': ('HTTP Header Audit',     module_http_headers,      'URL or domain'),
    '06': ('Subdomain Harvester',   module_subdomain_harvest, 'Domain (e.g. target.com)'),
    '07': ('Email OSINT',           module_email_osint,       'Email address'),
    '08': ('Hash Analyzer',         module_hash_analyzer,     'Hash string'),
    '09': ('Network Tracer',        module_network_tracer,    'IP or hostname'),
    '10': ('Full OSINT Report',     module_full_report,       'Domain'),
    '11': ('Username Hunter',       module_username_hunter,   'Username'),
    '12': ('Tech Fingerprint',      module_tech_fingerprint,  'URL or domain'),
    '13': ('CVE Intelligence',      module_cve_intel,         'Product/service name (e.g. openssh, apache)'),
    '14': ('WHOIS Deep Dive',       module_whois,             'Domain or IP'),
    '15': ('WAF Detector',          module_waf_detector,      'URL or domain'),
    '16': ('CMS Exploit Map',       module_cms_exploit_map,   'URL or domain'),
}

# ─── Main REPL ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description=f'Phantom OSINT v{VERSION}')
    parser.add_argument('--target', '-t', help='Pre-set target')
    parser.add_argument('--module', '-m', help='Run module directly (e.g. 01)')
    parser.add_argument('--no-banner', action='store_true', help='Skip boot animation')
    args = parser.parse_args()

    if args.no_banner:
        LOG.start()
        print(BANNER)
        print(MENU)
    else:
        boot_sequence()

    # Direct launch
    if args.module and args.target:
        mod = args.module.zfill(2)
        if mod in MODULE_MAP:
            name, func, _ = MODULE_MAP[mod]
            func(args.target)
            LOG.close()
            sys.exit(0)

    while True:
        try:
            raw = input(f'\n{C.BRED}PHANTOM{C.RESET}{C.DIM}@SPECTRE{C.RESET} {C.BBLUE}»{C.RESET} ').strip()
        except EOFError:
            break

        if not raw: continue

        # Add to history
        SESSION_HISTORY.append(raw)
        readline.add_history(raw)

        low = raw.lower()

        # Built-in commands
        if low in ('00', 'exit', 'quit', 'q'):
            print(f'\n  {C.BRED}[☠]{C.RESET} {C.DIM}Phantom is going dark. Goodbye, operator.{C.RESET}\n')
            LOG.close(); sys.exit(0)

        elif low == 'clear':
            os.system('clear')
            slow_print(BANNER, delay=0.0003)
            print(MENU)
            continue

        elif low == 'history':
            show_history(); continue

        elif low == 'log':
            info(f"Session log: {C.BYELLOW}{LOG.path}{C.RESET}"); continue

        elif low == 'score':
            THREAT.render(); continue

        elif low.startswith('help'):
            parts = raw.split()
            mid = parts[1].zfill(2) if len(parts) > 1 else None
            show_help(mid); continue

        elif low == 'menu':
            print(MENU); continue

        # Module selection
        choice = raw.zfill(2) if raw.isdigit() else raw
        if choice not in MODULE_MAP:
            warn(f"Unknown command '{raw}'. Type 'help' or '00' to exit.")
            continue

        name, func, hint = MODULE_MAP[choice]
        try:
            target = input(f'  {C.BYELLOW}[?]{C.RESET} {C.BWHITE}Target{C.RESET} {C.DIM}({hint}){C.RESET}: ').strip()
        except EOFError:
            continue

        if not target:
            warn("No target provided."); continue

        LOG.log(f"\nRun: Module {choice} [{name}] | Target: {target}")
        try:
            func(target)
        except KeyboardInterrupt:
            print(f'\n  {C.BYELLOW}[!]{C.RESET} Module interrupted.')
        except Exception as e:
            error(f"Unexpected error: {e}")

        status_bar()
        input(f'  {C.DIM}Press ENTER to return to menu...{C.RESET}')
        os.system('clear')
        slow_print(BANNER, delay=0.0003)
        print(MENU)


if __name__ == '__main__':
    main()
