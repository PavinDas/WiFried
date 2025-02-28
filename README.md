# Wi-Fried

<img src="https://socialify.git.ci/PavinDas/WiFried/image?description=1&font=KoHo&language=1&name=1&owner=1&pattern=Solid&theme=Dark" alt="Socket" width="640" height="320" />

A Python-based tool designed to scan Wi-Fi networks, perform deauthentication attacks, capture WPA handshakes, and attempt password cracking. Features a vibrant, colorized terminal output for an impressive user experience.

**Creator**: Pavin Das  
**GitHub**: [PavinDas](https://github.com/PavinDas)  
**Instagram**: [pavin__das](https://www.instagram.com/pavin__das)

---

## Features
- **Wi-Fi Scanning**: Detects nearby Wi-Fi networks using `airodump-ng` and lists them by signal strength.
- **Monitor Mode**: Automatically enables monitor mode on compatible interfaces (excluding `wlan*` names).
- **Deauthentication Attacks**: Disconnects clients from target networks using `aireplay-ng`.
- **WPA Handshake Capture**: Captures WPA/WPA2 handshakes for cracking.
- **Password Cracking**: Attempts to crack captured handshakes using `aircrack-ng` with a wordlist.
- **Colorized Output**: Eye-catching terminal output with distinct colors for info, success, errors, and debug messages.

---

## Prerequisites
- **Operating System**: Linux (e.g., Kali Linux, Ubuntu, Parrot OS recommended).
- **Hardware**: A Wi-Fi adapter supporting monitor mode and packet injection (e.g., Alfa AWUS036NHA).
- **Root Privileges**: Must run with `sudo`.

### Dependencies
- Python 3.x
- `colorama` (for colorized output)
- `aircrack-ng` suite (`airmon-ng`, `airodump-ng`, `aireplay-ng`, `aircrack-ng`)
- `wireless-tools` (`iwconfig`)
- `iw`

---

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/PavinDas/Wi-Fried.git
   cd Wi-Frie```

2. **Download Wordlist**
   Download the wordlist file: [Wordlist](https://github.com/PavinDas/WiFried/releases/tag/Wordlist)
   Add this file to WiFried directory

---

## Run Tool
 ``` sudo python3 wi_fried.py```
