#!/usr/bin/env python3
import argparse
import os
import re
import sys
import subprocess

# --- constants ---
CONFIG_FILE = "/etc/ampurr.conf"
SERVICE_NAME = "ampurr.service"
SERVICE_FILE_PATH = f"/etc/systemd/system/{SERVICE_NAME}"
INSTALL_PATH = "/usr/local/bin/ampurr"

# --- system interaction logic (runs with root) ---
def _create_systemd_service():
    """creates the systemd service file content"""
    # note: the service executes this very script with a special flag
    service_content = f"""[Unit]
Description=ampurr: persistently sets the battery charge threshold
After=multi-user.target

[Service]
Type=oneshot
ExecStart={INSTALL_PATH} --apply-on-boot

[Install]
WantedBy=multi-user.target
"""
    return service_content

def _apply_on_boot():
    """
    this function is executed by the systemd service on startup
    it reads the config and applies the limit with no user output
    """
    try:
        if not os.path.exists(CONFIG_FILE):
            return # no config, nothing to do

        with open(CONFIG_FILE, 'r') as f:
            limit = f.read().strip()

        # find the battery control file dynamically
        battery_path = find_supported_battery()
        if battery_path:
            control_file = os.path.join(battery_path, "charge_control_end_threshold")
            with open(control_file, 'w') as f:
                f.write(limit)
    except Exception:
        # fail silently, as this runs in the background during boot
        pass

def install():
    """handles the full installation and service setup process"""
    print("  [1/4] creating systemd service...")
    try:
        service_content = _create_systemd_service()
        with open(SERVICE_FILE_PATH, "w") as f:
            f.write(service_content)

        # create a default config file if it doesn't exist
        if not os.path.exists(CONFIG_FILE):
            print("  [2/4] creating default config file with limit 100...")
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                f.write("100")
        else:
            print("  [2/4] config file already exists...")

        print("  [3/4] reloading systemd and enabling service...")
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", "--now", SERVICE_NAME], check=True)
        print("  [4/4] service enabled. the limit will now persist after reboots.")
    except Exception as e:
        print(f"❌ error during installation: {e}", file=sys.stderr)
        sys.exit(1)
    print("")
    print("ampurr - a simple utility to manage your battery ᓚ₍ ^. .^₎")
    print("\t. ݁₊ ⊹݁ made with ❤️  to extend your battery's lifespan ݁˖ . ")

def uninstall():
    """disables and removes the systemd service and config"""
    print("  [1/3] disabling and removing systemd service...")
    try:
        if os.path.exists(SERVICE_FILE_PATH):
            subprocess.run(["systemctl", "disable", "--now", SERVICE_NAME], check=True, stderr=subprocess.DEVNULL)
            os.remove(SERVICE_FILE_PATH)
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            print("  [2/3] service disabled and removed.")
        else:
            print("  [2/3] service file not found, skipping.")
    except Exception as e:
        print(f"❌ error during uninstallation: {e}", file=sys.stderr)

    print("  [3/3] resetting charge limit to 100%...")
    battery_path = find_supported_battery()
    if battery_path:
        try:
            control_file = os.path.join(battery_path, "charge_control_end_threshold")
            with open(control_file, 'w') as f:
                f.write("100")
            print("✅ charge limit has been reset to 100%.")
        except Exception as e:
            print(f"⚠️ warning: could not reset the charge limit to 100%. you may need to do it manually.",
                  file=sys.stderr)
            print(f"details: {e}", file=sys.stderr)
    else:
        print("supported battery not found, skipping reset.")

# --- hardware detection ---
def find_supported_battery():
    """
    scans /sys/class/power_supply/ for a battery that supports
    charge limiting via charge_control_end_threshold
    """
    base_path = "/sys/class/power_supply/"
    if not os.path.isdir(base_path): return None
    battery_dirs = [d for d in os.listdir(base_path) if d.startswith('BAT')]
    for bat_dir in battery_dirs:
        if os.path.exists(os.path.join(base_path, bat_dir, "charge_control_end_threshold")):
            return os.path.join(base_path, bat_dir)
    return None

def _get_cpu_cores():
    """finds all cpu core directories (e.g., cpu0, cpu1)"""
    base_path = "/sys/devices/system/cpu/"
    try:
        return [d for d in os.listdir(base_path) if re.match(r'cpu\d+', d)]
    except FileNotFoundError:
        return []

def get_available_governors():
    """reads and returns available cpu governors from sysfs"""
    gov_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
    try:
        with open(gov_file, 'r') as f:
            return f.read().strip().split()
    except FileNotFoundError:
        return []

def get_current_governor():
    """reads and returns the current cpu governor from sysfs"""
    gov_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
    try:
        with open(gov_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "not available"

def set_cpu_governor(governor_name):
    """sets the scaling governor for all cpu cores"""
    if os.geteuid() != 0:
        print("❌ error: modifying the CPU governor requires superuser privileges.", file=sys.stderr)
        sys.exit(1)

    available = get_available_governors()
    if not available:
        print("❌ error: could not detect available CPU governors. your system may not support this.", file=sys.stderr)
        sys.exit(1)

    if governor_name not in available:
        print(f"❌ error: '{governor_name}' is not a valid governor.", file=sys.stderr)
        print(f"available options for your system: {' '.join(available)}", file=sys.stderr)
        sys.exit(1)

    cores = _get_cpu_cores()
    if not cores:
        print("❌ error: could not find any CPU cores.", file=sys.stderr)
        sys.exit(1)

    print(f"setting CPU governor to '{governor_name}' for all cores...")
    try:
        for core in cores:
            gov_file = f"/sys/devices/system/cpu/{core}/cpufreq/scaling_governor"
            if os.path.exists(gov_file):
                with open(gov_file, 'w') as f:
                    f.write(governor_name)
        print(f"✅ CPU governor successfully set to '{governor_name}'.")
    except Exception as e:
        print(f"❌ error setting the CPU governor: {e}", file=sys.stderr)
        sys.exit(1)

# --- core user-facing functions ---
def get_current_limit(battery_path):
    """returns the currently set charge limit from sysfs"""
    try:
        with open(os.path.join(battery_path, "charge_control_end_threshold"), 'r') as f:
            return int(f.read().strip())
    except Exception as e:
        print(f"❌ error reading the limit: {e}", file=sys.stderr)
        sys.exit(1)

def set_charge_limit(limit_value, battery_path):
    """sets a new charge limit and saves it to the config file"""
    if os.geteuid() != 0:
        print("❌ error: modifying the charge limit requires superuser privileges.", file=sys.stderr)
        sys.exit(1)
    if not (50 <= limit_value <= 100):
        print(f"❌ error: the limit value must be between 50 and 100.", file=sys.stderr)
        sys.exit(1)
    try:
        # apply for current session
        with open(os.path.join(battery_path, "charge_control_end_threshold"), 'w') as f:
            f.write(str(limit_value))
        print(f"✅ charge limit successfully set to {limit_value}% for the current session.")
        # save for persistence
        with open(CONFIG_FILE, 'w') as f:
            f.write(str(limit_value))
        print(f"✅ limit of {limit_value}% saved and will be applied on next boot.")
    except Exception as e:
        print(f"❌ error setting the limit: {e}", file=sys.stderr)
        sys.exit(1)

def get_current_capacity(battery_path):
    """returns the current battery capacity percentage"""
    capacity_file = os.path.join(battery_path, "capacity")
    if not os.path.exists(capacity_file): return None
    try:
        with open(capacity_file, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return None

def run_cli():
    """defines and executes the command-line interface logic"""
    parser = argparse.ArgumentParser(
        prog="ampurr",
        description="ampurr - a simple utility to manage your battery ᓚ₍ ^. .^₎",
        epilog=". ݁₊ ⊹݁ made with ❤️ to extend your battery's lifespan ݁˖ . "
    )
    subparsers = parser.add_subparsers(dest="module", required=True)

    # --- "battery" module ---
    parser_battery = subparsers.add_parser("battery", help="manage battery settings")
    battery_subparsers = parser_battery.add_subparsers(dest="command", required=True)
    cmd_battery_set = battery_subparsers.add_parser("set", help="set a new charge limit (requires sudo)")
    cmd_battery_set.add_argument("limit", type=int, help="the charge percentage to stop at (50-100)")
    battery_subparsers.add_parser("get", help="show the currently set limit")
    battery_subparsers.add_parser("status", help="show the current limit and battery capacity")

    # --- "cpu" module ---
    parser_cpu = subparsers.add_parser("cpu", help="manage cpu power profiles (governors)")
    cpu_subparsers = parser_cpu.add_subparsers(dest="command", required=True)
    cmd_cpu_set = cpu_subparsers.add_parser("set", help="set a new cpu governor (requires sudo)")
    cmd_cpu_set.add_argument("governor", type=str, help="the governor to apply (e.g., powersave, performance)")
    cpu_subparsers.add_parser("status", help="show the current cpu governor")
    cpu_subparsers.add_parser("list", help="list available cpu governors for your system")

    args = parser.parse_args()

    # find battery and exit if not supported
    battery_path = find_supported_battery()
    if battery_path is None:
        print("❌ error: no supported battery found.", file=sys.stderr)
        sys.exit(1)

    # execute commands based on module
    if args.module == "battery":
        if args.command == "set":
            set_charge_limit(args.limit, battery_path)
        elif args.command == "get":
            limit = get_current_limit(battery_path)
            print(f"current charge limit: {limit}%")
        elif args.command == "status":
            limit = get_current_limit(battery_path)
            capacity = get_current_capacity(battery_path)
            print(f"set charge limit: {limit}%")
            if capacity is not None:
                print(f"current capacity:   {capacity}%")
            else:
                print("could not determine current capacity")

    elif args.module == "cpu":
        if args.command == "set":
            set_cpu_governor(args.governor)
        elif args.command == "status":
            governor = get_current_governor()
            print(f"current CPU governor: {governor}")
        elif args.command == "list":
            governors = get_available_governors()
            if governors:
                print("available governors for your system:")
                print(f"  {' '.join(governors)}")
            else:
                print("could not find any available governors.")

# --- main router ---
if __name__ == "__main__":
    # this router decides what the script should do based on special flags
    # it runs before the main cli parser
    if len(sys.argv) > 1:
        if sys.argv[1] == '--install':
            if os.geteuid() != 0: sys.exit("❌ error: installation requires superuser privileges.")
            install()
            sys.exit(0)
        elif sys.argv[1] == '--uninstall':
            if os.geteuid() != 0: sys.exit("❌ error: uninstallation requires superuser privileges.")
            uninstall()
            sys.exit(0)
        elif sys.argv[1] == '--apply-on-boot':
            _apply_on_boot()
            sys.exit(0)

    # if no special flags were found, run the normal user-facing cli
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\nexiting...")
        sys.exit(0)