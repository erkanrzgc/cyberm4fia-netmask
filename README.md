# CYBERM4FIA NETMASK

Cross-platform MAC/IP changer and daemon for continuous network identity rotation. Built with zero external dependencies.

```
 ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███╗   ███╗██╗  ██╗███████╗██╗ █████╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗████╗ ████║██║  ██║██╔════╝██║██╔══██╗
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██╔████╔██║███████║█████╗  ██║███████║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║╚██╔╝██║╚════██║██╔══╝  ██║██╔══██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║██║ ╚═╝ ██║     ██║██║     ██║██║  ██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝
                // NETMASK // MAC/IP CHANGER // DAEMON //
```

## Features

- **Interactive menu** — step-by-step box-drawn terminal UI
- **CLI mode** — one-shot for scripting and automation
- **Daemon mode** — continuous MAC/IP rotation with safe restore on exit
- **Random generators** — valid unicast MAC + private IP generation
- **DHCP renew** — release and renew DHCP leases
- **Backup & restore** — automatic backup of original settings, manual restore
- **Cross-platform** — Linux (iproute2) + Windows (netsh/registry)
- **Zero dependencies** — standard library only

## Installation

```bash
git clone https://github.com/erkanrzgc/cyberm4fia-netmask.git
cd cyberm4fia-netmask
```

No `pip install` needed. Only Python 3.6+ required.

## Usage

### Interactive Mode

```bash
sudo python netmask.py
```

Opens a box-drawn menu with interface selection, MAC/IP configuration, daemon control, and more.

### CLI Mode

```bash
# Change MAC only
sudo python netmask.py -i eth0 -m 00:11:22:33:44:55

# Random MAC + random IP
sudo python netmask.py -i eth0 -rm -ri

# Random MAC + DHCP renew (new IP from router)
sudo python netmask.py -i eth0 -rm --dhcp

# Static IP only (keeps current MAC)
sudo python netmask.py -i eth0 --ip 192.168.1.100 -n 255.255.255.0

# Restore original settings
sudo python netmask.py -i eth0 --reset
```

### Daemon Mode

```bash
# Start continuous rotation (every 30 seconds)
sudo python netmask.py --daemon -i eth0 -t 30

# Check status
sudo python netmask.py --status

# Stop and restore original settings
sudo python netmask.py --stop
```

### Options

| Flag | Description |
|------|-------------|
| `-i, --interface` | Network interface name |
| `-m, --mac` | New MAC address (xx:xx:xx:xx:xx:xx) |
| `-rm, --random-mac` | Generate random unicast MAC |
| `--ip` | New static IP address |
| `-ri, --random-ip` | Generate random private IP |
| `-n, --netmask` | Subnet mask (default: 255.255.255.0) |
| `--dhcp` | Release and renew DHCP lease |
| `--reset` | Restore original MAC/IP |
| `--daemon` | Start daemon with continuous rotation |
| `-t, --interval` | Daemon rotation interval in seconds (min 10) |
| `--status` | Show daemon status |
| `--stop` | Stop daemon and restore original settings |

## Platform Support

| Feature | Linux | Windows |
|---------|-------|---------|
| MAC change | `ip link set address` | Registry + netsh |
| IP change | `ip addr add` | `netsh interface ip set` |
| DHCP renew | `dhclient` | `ipconfig /release /renew` |
| Interface discovery | `/sys/class/net/` | `netsh interface show` |
| Daemon | Double-fork | Detached subprocess |
| Config directory | `~/.config/cyberm4fia/` | `%APPDATA%\cyberm4fia\` |

## Requirements

- **Linux**: `iproute2` (installed by default), `dhclient` (ISC DHCP client)
- **Windows**: Administrator privileges
- **Python**: 3.6+ (standard library only)

## Architecture

```
cyberm4fia-netmask/
├── netmask.py                    # Entry point / CLI routing
└── netmask/                      # Core package
    ├── banner.py                 # ASCII art + ANSI gradient
    ├── validator.py              # MAC/IP validation, random generators
    ├── config.py                 # Platform-aware constants
    ├── menu.py                   # Interactive terminal menu
    ├── daemon.py                 # Daemon with rotate loop
    ├── backup.py                 # JSON backup/restore
    ├── interfaces/               # Interface discovery (per-OS)
    │   ├── base.py               # AbstractInterface (ABC)
    │   ├── linux.py              # Linux backend
    │   └── windows.py            # Windows backend
    ├── changers/                 # MAC/IP change operations (per-OS)
    │   ├── base.py               # AbstractChanger (ABC)
    │   ├── linux.py              # Linux backend
    │   └── windows.py            # Windows backend
    └── utils/
        └── platform.py           # OS detection, admin check
```

## Disclaimer

This tool is intended for educational purposes, network testing, and legitimate security research. Users are responsible for complying with applicable laws and regulations.

## License

MIT — Copyright (c) 2024 erkanrzgc
