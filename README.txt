
╔══════════════════════════════════════════════════════════════════════════╗
║         PHANTOM v3.0 — SPECTRE OSINT Intelligence Framework             ║
║              Advanced Reconnaissance Platform for Kali Linux            ║
╚══════════════════════════════════════════════════════════════════════════╝

DESCRIPTION
───────────
Phantom SPECTRE is a terminal-based OSINT and reconnaissance framework
built for Kali Linux. It provides 16 intelligence modules covering
network reconnaissance, domain analysis, vulnerability mapping, WAF
detection, CMS auditing, and more — with zero external pip dependencies.

NEW IN v3.0 SPECTRE
────────────────────
  ✦ Matrix rain animated boot sequence
  ✦ Threat Score Engine — real-time risk gauge per module
  ✦ Session Logger — auto-saves all output to phantom_session_*.log
  ✦ Command history with ↑↓ navigation (readline)
  ✦ Hop-by-hop geolocation in Network Tracer
  ✦ ASCII table renderer for structured output
  ✦ 'help <module>' inline documentation
  ✦ CLI flags: --target / --module / --no-banner
  ✦ Status bar (timestamp + log path)
  ✦ 4 new modules: CVE Intel, WHOIS, WAF Detector, CMS Exploit Map

REQUIREMENTS
────────────
  • Kali Linux 2023.x+ (or any Debian-based)
  • Python 3.8+
  • dig / dnsutils   (sudo apt install dnsutils)
  • traceroute       (sudo apt install traceroute)
  • whois            (sudo apt install whois)
  • No pip installs required — stdlib only

QUICK SETUP
───────────
  git clone / extract phantom-v3/ into your directory
  chmod +x setup.sh
  sudo bash setup.sh
  phantom                        ← run from anywhere

MANUAL RUN
──────────
  python3 phantom.py             ← interactive menu with boot animation
  python3 phantom.py --no-banner ← skip animation
  python3 phantom.py -m 01 -t 8.8.8.8   ← direct module launch

MODULES
───────
  [01] IP Intelligence     → Geolocation, ASN, ISP, reverse DNS, port probe,
                             VPN/proxy detection via ip-api.com

  [02] DNS Reconnaissance  → A/AAAA/MX/NS/TXT/SOA/CNAME/CAA records,
                             AXFR zone transfer test, SPF/DMARC/DKIM check

  [03] Port Scanner        → Multi-threaded TCP connect (200 workers),
                             live progress bar, banner grabbing,
                             danger port annotation, top-50/1-1024/custom

  [04] SSL/TLS Inspector   → Full cert chain, SAN enumeration, expiry
                             countdown, cipher strength, protocol version,
                             self-signed detection

  [05] HTTP Header Audit   → 9 security controls scored A+–F,
                             server/tech disclosure detection

  [06] Subdomain Harvester → 65-word brute-force + crt.sh CT logs,
                             concurrent DNS resolution

  [07] Email OSINT         → Pattern classification, MX verify,
                             permutation generation, breach/OSINT links

  [08] Hash Analyzer       → 25+ hash type ID, entropy calc, dictionary
                             attack (MD5/SHA1), crack resource table

  [09] Network Tracer      → traceroute + hop-by-hop geolocation,
                             CDN node detection

  [10] Full OSINT Report   → Orchestrated: DNS + Subdomains + HTTP +
                             SSL + Tech, saves to session log

  [11] Username Hunter     → 25 platforms (GitHub, HackerOne, Docker Hub,
                             npm, PyPI, Mastodon, Codepen…)

  [12] Tech Fingerprint    → 35+ signatures: CMS, JS frameworks, CSS libs,
                             CDN, analytics, server/language

  [13] CVE Intelligence    → NIST NVD API, CVSS scoring, severity
       ★ NEW                 breakdown chart, top-15 CVEs per product

  [14] WHOIS Deep Dive     → Parsed registrar/dates/NSes/DNSSEC, privacy
       ★ NEW                 guard detection, expiry countdown

  [15] WAF Detector        → 14 WAF vendor fingerprints, 5 probe payloads
       ★ NEW                 (XSS/SQLi/LFI/SSRF/CMDi), bypass hints

  [16] CMS Exploit Map     → CMS fingerprint + admin panel scan +
       ★ NEW                 sensitive path probe + known CVE risks +
                             default credential hints

SPECIAL COMMANDS (in-menu)
───────────────────────────
  help <01-16>   Detailed help for any module
  history        Show last 20 commands
  log            Show current session log path
  score          Display accumulated threat score
  clear          Clear screen and redraw banner
  menu           Redraw module menu
  00 / q / exit  Exit Phantom

CLI FLAGS
─────────
  --target / -t  <value>   Pre-set target
  --module / -m  <01-16>   Module to run
  --no-banner              Skip boot animation

  Example: python3 phantom.py -m 13 -t apache

THREAT SCORE ENGINE
────────────────────
Each module tracks risk findings and produces a colored gauge:
  LOW RISK  (green)   < 30% weight triggered
  MODERATE  (yellow)  30–60%
  HIGH RISK (red)     60–80%
  CRITICAL  (magenta) > 80%

SESSION LOGGING
───────────────
All output is automatically saved to phantom_session_YYYYMMDD_HHMMSS.log
in the working directory. ANSI color codes are stripped for clean text.

LEGAL DISCLAIMER
────────────────
This tool is for authorized security testing and academic research only.
Use only against systems you own or have explicit written permission to test.
Unauthorized scanning is illegal in most jurisdictions.
The authors accept no liability for misuse.

AUTHOR
──────
PhantomCore Security Research
Version 3.0 SPECTRE | Build: 2026
For: Kali Linux / B.Tech CSE Cybersecurity Project
