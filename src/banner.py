"""ASCII art banner with ANSI 256-color gradient rendering."""

import shutil

BANNER = """\
 ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███╗   ███╗██╗  ██╗███████╗██╗ █████╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗████╗ ████║██║  ██║██╔════╝██║██╔══██╗
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██╔████╔██║███████║█████╗  ██║███████║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║╚██╔╝██║╚════██║██╔══╝  ██║██╔══██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║██║ ╚═╝ ██║     ██║██║     ██║██║  ██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝
                // NETMASK // MAC/IP CHANGER // DAEMON //"""

GRADIENT_START = 255
GRADIENT_STEP = 4


def render_gradient(text, start=GRADIENT_START, step=GRADIENT_STEP):
    """Render text with a vertical white-to-gray gradient.

    Each line gets a progressively darker shade using 256-color ANSI codes.
    Grayscale palette: 232 (darkest) to 255 (brightest white).
    """
    lines = text.split("\n")
    result = []
    for i, line in enumerate(lines):
        color = max(start - i * step, 232)
        result.append(f"\033[38;5;{color}m{line}\033[0m")
    return "\n".join(result)


def print_banner():
    """Print the CYBERM4FIA banner with gradient effect."""
    term_width = shutil.get_terminal_size().columns
    banner_lines = BANNER.split("\n")
    banner_width = max(len(line) for line in banner_lines)

    padding = max((term_width - banner_width) // 2, 0)

    colored = render_gradient(BANNER)
    for line in colored.split("\n"):
        if line.strip():
            print(" " * padding + line)

    print()
