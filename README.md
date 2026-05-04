<h1 align="center">cyberm4fia-netmask</h1>

<p align="center">
  <img src="https://img.shields.io/badge/mission-identity%20rotation%20daemon-red?style=for-the-badge" alt="mission">
</p>

<pre>
 ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███╗   ███╗██╗  ██╗███████╗██╗ █████╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗████╗ ████║██║  ██║██╔════╝██║██╔══██╗
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██╔████╔██║███████║█████╗  ██║███████║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║╚██╔╝██║╚════██║██╔══╝  ██║██╔══██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║██║ ╚═╝ ██║     ██║██║     ██║██║  ██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝
</pre>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.6+-blue?style=flat-square&logo=python" alt="python">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20windows-purple?style=flat-square" alt="platform">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="license">
  <img src="https://img.shields.io/badge/deps-zero%20stdlib%20only-brightgreen?style=flat-square" alt="deps">
  <img src="https://img.shields.io/badge/mode-interactive%20%7C%20cli%20%7C%20daemon-orange?style=flat-square" alt="mode">
  <img src="https://img.shields.io/badge/anti--forensics-dns%20%7C%20arp%20%7C%20hostname-red?style=flat-square" alt="anti-forensics">
</p>

<p align="center">
  <b>cyberm4fia-netmask</b> is a cross-platform MAC &amp; IP changer with a built-in daemon for continuous network identity rotation. Features anti-forensics (DNS/ARP flush, hostname randomization), network kill switch, interactive box-drawn terminal menu, CLI scriptability, and safe shutdown that restores original settings — for both Linux and Windows.
</p>

---

## Features

### Core Operations

| Capability | Method | Description |
|---|---|---|
| MAC Spoofing | `ip link set address` / Registry | Change hardware address of any network interface |
| Static IP Assignment | `ip addr add` / `netsh` | Set a custom static IP with configurable netmask |
| DHCP Renew | `dhclient` / `ipconfig /renew` | Release current lease and request a new IP from router |
| Restore | JSON backup | Return interface to original MAC + IP in one command |

### Random Generators

| Feature | Implementation | Description |
|---|---|---|
| Unicast MAC | `random_mac()` | Generates valid locally-administered unicast MAC (bit 0 = 0) |
| Private IP | `random_private_ip()` | Picks from 10.0.0.0/8, 172.16.0.0/12, or 192.168.0.0/16 |
| Quick Mode | `-rm -ri` | One-shot random MAC + random IP |

### Anti-Forensics Suite

| Operation | Command | Effect |
|---|---|---|
| DNS Flush | `resolvectl flush-caches` + `systemd-resolved` restart | Wipes all cached DNS resolutions |
| ARP Flush | `ip neigh flush all` | Clears neighbor cache (device-to-MAC mappings) |
| Hostname Randomization | `hostnamectl set-hostname` | Spoofs system hostname (e.g. `DESKTOP-A7X3K9M`) |

### Daemon Engine

| Feature | Mechanism | Description |
|---|---|---|
| Continuous Rotation | Timer loop | Changes MAC + IP every N seconds (min 10s) |
| Duration Limit | `-d 5m` / `-d 2h` / `-d 1h30m` | Auto-stop and restore when time expires |
| Network Kill Switch | iptables DROP on interface | Blocks all traffic during rotation — daemon crash = permanent block |
| Safe Shutdown | `SIGTERM` / `SIGINT` handler | Restores original MAC + IP on exit |
| PID Lock | `netmask.pid` file | Prevents duplicate daemon instances per interface |
| Rotation Log | `netmask.log` with timestamps | Tracks every rotation for auditing |
| Live Status | `--status` command | Shows uptime, rotation count, current vs original values |

### User Interface

| Section | What It Shows |
|---|---|
| **Interface Picker** | All network adapters with MAC, IP, and UP/DOWN status |
| **Action Menu** | MAC, IP, Both, DHCP Renew, Quick Random, Restore, Daemon |
| **Value Input** | Manual entry or one-click random generation |
| **Confirmation** | Before/after summary with old → new values |
| **Result Display** | Success/failure with actual interface readback |
| **Daemon Status** | Box-drawn dashboard with PID, uptime, rotations, current settings |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     netmask.py (entry)                       │
│              argparse → CLI / Menu / Daemon router           │
└───────────────────────────┬──────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬──────────────┐
        │                   │                   │              │
  ┌─────▼──────┐  ┌─────────▼────────┐  ┌──────▼──────┐  ┌────▼──────┐
  │   menu.py  │  │    daemon.py     │  │   backup.py │  │antiforensi│
  │ Interactive│  │  Double-fork     │  │  JSON CRUD  │  │ cs.py     │
  │ Box UI     │  │  Rotate loop     │  │  Restore    │  │ DNS/ARP/  │
  └────────────┘  │  Kill switch     │  └─────────────┘  │ hostname  │
                  ├──────────────────┤                   └───────────┘
                  │  _rotate()       │
                  │  1. ks_block     │  ← iptables DROP
                  │  2. disable iface│
                  │  3. change MAC   │
                  │  4. change IP    │
                  │  5. enable iface │
                  │  6. ks_unblock   │  ← iptables remove
                  │  7. anti-forensics│ ← DNS+ARP+hostname
                  └────────┬─────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐      ┌────────▼────────┐
     │  interfaces/    │      │   changers/     │
     │  Abstract ABC   │      │  Abstract ABC   │
     ├─────────────────┤      ├─────────────────┤
     │  linux.py       │      │  linux.py       │
     │  windows.py     │      │  windows.py     │
     └─────────────────┘      └─────────────────┘
```

---

## Quick Start

### Linux

```bash
git clone https://github.com/erkanrzgc/cyberm4fia-netmask.git
cd cyberm4fia-netmask
sudo python netmask.py
```

### Windows

```batch
git clone https://github.com/erkanrzgc/cyberm4fia-netmask.git
cd cyberm4fia-netmask
python netmask.py
```

> **Note:** Zero pip install needed — Python 3.6+ standard library only. Administrative privileges required.

---

## Usage

### Interactive Mode

```
sudo python netmask.py
```

Opens a box-drawn terminal menu that walks you through interface selection, MAC/IP configuration, DHCP renew, daemon control with kill switch + anti-forensics toggles, and backup restore.

### CLI Mode

| Command | What It Does |
|---------|--------------|
| `sudo python netmask.py -i eth0 -m 00:11:22:33:44:55` | Change MAC only |
| `sudo python netmask.py -i eth0 -rm -ri` | Random MAC + random private IP |
| `sudo python netmask.py -i eth0 -rm --dhcp` | Random MAC + DHCP renew |
| `sudo python netmask.py -i eth0 --ip 192.168.1.100 -n 255.255.255.0` | Static IP only |
| `sudo python netmask.py -i eth0 --reset` | Restore original settings |

### CLI Reference

| Flag | Type | Description |
|------|------|-------------|
| `-i`, `--interface` | `string` | Network interface name (eth0, wlan0, Ethernet0) |
| `-m`, `--mac` | `string` | New MAC address (xx:xx:xx:xx:xx:xx) |
| `-rm`, `--random-mac` | `flag` | Generate random unicast MAC |
| `--ip` | `string` | New static IP address (e.g. 192.168.1.100) |
| `-ri`, `--random-ip` | `flag` | Generate random private IP |
| `-n`, `--netmask` | `string` | Subnet mask (default: 255.255.255.0) |
| `--dhcp` | `flag` | Release and renew DHCP lease |
| `--reset` | `flag` | Restore original MAC/IP from backup |

### Daemon Mode

```bash
# Basic — rotates MAC+IP every 30 seconds
sudo python netmask.py --daemon -i eth0 -t 30

# Duration — 5 minutes with kill switch + anti-forensics
sudo python netmask.py --daemon -i eth0 -t 3 -d 5m -ks -af

# Indefinite with full stealth
sudo python netmask.py --daemon -i eth0 -t 10 -ks -af

# Live status dashboard
sudo python netmask.py --status

# Stop and restore original settings
sudo python netmask.py --stop
```

| Flag | Type | Description |
|------|------|-------------|
| `--daemon` | `flag` | Start as background daemon |
| `-t`, `--interval` | `int` | Rotation interval in seconds (min 10, default 30) |
| `-d`, `--duration` | `string` | Total run time (`30s`, `5m`, `2h`, `1h30m`). Auto-stop + restore |
| `-ks`, `--kill-switch` | `flag` | Block network traffic during rotation (iptables DROP) |
| `-af`, `--anti-forensics` | `flag` | Flush DNS/ARP + randomize hostname on each rotation |
| `--status` | `flag` | Show daemon status dashboard |
| `--stop` | `flag` | Stop daemon and restore original settings |

### Daemon Status Output

```
┌──────────────────────────────────────────────────────────────┐
│                    NETMASK DAEMON STATUS                      │
├──────────────────────────────────────────────────────────────┤
│  Status:       RUNNING                                       │
│  PID:          12847                                         │
│  Interface:    eth0                                          │
│  Interval:     3s                                            │
│  Duration:     5m                                            │
│  Remaining:    2m 14s                                        │
│  Uptime:       2h 14m 37s                                    │
│  Rotations:    268                                           │
├──────────────────────────────────────────────────────────────┤
│  Current MAC:  4a:8f:11:e2:0d:73    Original MAC: 00:1a:2b  │
│  Current IP:   192.168.1.87/24      Original IP:  192.168.. │
└──────────────────────────────────────────────────────────────┘
```

---

## Platform Support

| Feature | Linux | Windows |
|---------|-------|---------|
| MAC change | `ip link set address` | Registry + netsh |
| IP change | `ip addr add` | `netsh interface ip set address` |
| DHCP renew | `dhclient -r && dhclient` | `ipconfig /release && /renew` |
| Interface discovery | `/sys/class/net/` | `netsh interface show interface` |
| DNS flush | `resolvectl` + `systemd-resolved` | `ipconfig /flushdns` |
| Kill switch | `iptables` | Not yet available |
| Daemon | Double-fork (Unix) | Detached subprocess |
| Config directory | `~/.config/cyberm4fia/` | `%APPDATA%\cyberm4fia\` |

---

## Project Structure

```
cyberm4fia-netmask/
│
├── netmask.py                    Entry point (argparse router)
├── banner.py                     CYBERM4FIA ASCII + ANSI gradient
├── validator.py                  MAC/IP validation + random generators + duration parser
├── menu.py                       Interactive box-drawn terminal UI
├── daemon.py                     Double-fork daemon + rotate loop + kill switch
├── backup.py                     JSON backup/restore per interface
├── antiforensics.py              DNS flush + ARP flush + hostname randomization
├── config.py                     Platform-aware paths + box-draw chars
├── interfaces/
│   ├── base.py                   AbstractInterface (ABC)
│   ├── linux.py                  Linux: /sys/class/net + ip addr
│   └── windows.py                Windows: netsh + getmac
├── changers/
│   ├── base.py                   AbstractChanger (ABC)
│   ├── linux.py                  Linux: ip link/addr + dhclient
│   └── windows.py                Windows: netsh + registry + ipconfig
├── utils/
│   └── platform.py               OS detection + admin check + subprocess
├── requirements.txt
├── README.md
└── LICENSE                       MIT
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Permission denied` | Run with `sudo` on Linux, or Admin terminal on Windows |
| `dhclient: command not found` | Install ISC DHCP client: `sudo apt install isc-dhcp-client` |
| Interface not found | Check available interfaces: `ip link show` (Linux) or `netsh interface show interface` (Windows) |
| MAC change not taking effect | Some NICs/drivers block MAC spoofing; try a different interface or driver |
| Kill switch blocks everything | `iptables -F OUTPUT` to flush all rules; `sudo netmask.py --stop` does this automatically |
| Kill switch rules persist | Run `sudo iptables -D OUTPUT -o <iface> -j DROP` manually |
| Daemon already running | Use `--stop` first, or delete stale `netmask.pid` from config dir |
| DHCP lease not renewing | Network may require MAC+IP to be consistent; try `-rm --dhcp` combined |
| Backup restore fails | Manual restore: check `~/.config/cyberm4fia/backup.json` for original values |
| DNS not flushing | Ensure `systemd-resolved` is active: `sudo systemctl enable --now systemd-resolved` |

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
