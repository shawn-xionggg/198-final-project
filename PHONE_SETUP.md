# iPhone camera over your hotspot

Built: Safari camera page -> local HTTPS laptop receiver -> existing YOLO counting logic -> optional Arduino USB display. No phone app, public tunnel, router forwarding, cloud video service, or video recording. Browser sends one resized JPEG at a time, waits for processing, then sends the next. This is a prototype, not a high-frame-rate video stream.

## 1. Connect

Enable iPhone Settings > Personal Hotspot > Allow Others to Join. Connect Windows Wi-Fi to that hotspot. In Windows Settings > Network & internet > Wi-Fi > your hotspot properties, set this trusted hotspot to Private (not a campus/public network).

Open PowerShell:

```powershell
cd C:\coding\squat_counter
ipconfig
```

Find the IPv4 address under Wireless LAN adapter Wi-Fi. Use the laptop's address, not its Default Gateway, Tailscale, WSL, or an address copied from this document. `172.20.10.2` below is ONLY AN EXAMPLE. If the IP changes later, repeat the firewall step and restart the receiver with the new address. The root certificate remains the same.

## 2. Install laptop dependencies if not already installed

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-phone.txt
```

The first model download needs internet if yolo26n-pose.pt is absent. Otherwise video processing is local; laptop updates and other apps may still use hotspot mobile data.

## 3. Narrow firewall rule (Administrator PowerShell)

Replace the example IP. This script checks that the address belongs to the laptop and its network is Private. It allows the project's Python launcher and its underlying Python runtime, on that address, ports 8080/8443, from the local subnet. It does not change router settings or turn off the firewall.

```powershell
cd C:\coding\squat_counter
powershell -NoProfile -ExecutionPolicy Bypass -File .\phone-firewall.ps1 -LaptopIP 172.20.10.2
```

ExecutionPolicy Bypass applies to this one script invocation, not a permanent system setting. You can inspect phone-firewall.ps1 first. Do not additionally accept a broad Public-networks firewall exception.

## 4. First run (normal PowerShell)

```powershell
cd C:\coding\squat_counter
.\.venv\Scripts\python.exe phone_server.py --host 172.20.10.2 --pair
```

Leave it running. It prints a ONE-TIME CERTIFICATE address, a CAMERA PAGE address and a session code. The HTTP certificate download exists for 10 minutes, serves only the public certificate, and never accepts camera frames. If Safari cannot reach this address, first check the laptop IP and firewall. Host-to-client access over a hotspot must be verified on your phone; it is not guaranteed by the hotspot simply providing internet.

## 5. Trust this local camera certificate on your iPhone (once)

1. Open the printed ONE-TIME CERTIFICATE address in Safari on your hotspot-hosting iPhone. Type it exactly, including http://, port 8080 and the random path. This also tests whether the phone can reach the laptop.
2. Allow the profile download. In Settings > General > VPN & Device Management (or Profile Downloaded), inspect and install **Squat Counter Local Camera**. If shown, compare its SHA-256 fingerprint to the laptop's printed fingerprint. Download it only from the address your own laptop printed on your own hotspot.
3. Open Settings > General > About > Certificate Trust Settings and enable full trust for **Squat Counter Local Camera**.
4. Return to Safari and open the printed HTTPS CAMERA PAGE. If typing the shorter https://LAPTOP-IP:8443 address, paste the session code into the page.

This installs a local root certificate: it makes your phone trust certificates signed by this project's private key. Keep the .phone-tls folder private, never upload or share it, and remove the certificate profile when you finish the project. Nothing is installed in the laptop's system trust store. The root expires after 90 days. No VPN, device management enrollment, or app is installed by this certificate.

Apple instructions: https://support.apple.com/en-ca/102390

## 6. Start camera

Choose rear/front camera and tap Start camera. Allow camera permission. Keep Safari in the foreground and frame the full hip, knee and ankle from the side. The page shows reps, stage and knee angle. It sends images only while Start camera is active. Stop camera releases the camera; switching apps also stops it. Reset count restarts the counter. The laptop never saves the frames.

This uses the left hip/knee/ankle by default. Use --side right if that side faces the phone. A processing gap over one second cancels an unfinished rep; very slow connections may prevent counting. This is still a threshold counter, not a full form assessment or calibrated depth/tempo tracker.

## 7. Add the Arduino display

First upload the sketch described in HARDWARE.md. Close Arduino Serial Monitor. Stop the receiver with Ctrl+C and restart it using your actual COM port:

```powershell
.\.venv\Scripts\python.exe -m serial.tools.list_ports
.\.venv\Scripts\python.exe phone_server.py --host 172.20.10.2 --port COM3
```

Reopen the new printed camera URL (session code changes each run). No --pair needed once the root is trusted. The Arduino detects missing updates after 3 seconds; stopping the phone camera therefore changes its display to disconnected. The original webcam command still works.

## Stop and remove

Tap Stop camera and press Ctrl+C in the laptop terminal. No receiver remains listening. To remove the firewall rule, run in Administrator PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\phone-firewall.ps1 -LaptopIP 172.20.10.2 -Remove
```

Remove the Squat Counter Local Camera profile in iPhone Settings > General > VPN & Device Management when no longer needed. Do not delete or replace the private certificate folder during normal use; doing so requires trusting a new certificate.

## Limits and troubleshooting

- This has not been tested on your actual iPhone, hotspot, or Arduino yet.
- No certificate download: verify the current Wi-Fi IPv4, Private profile, narrow firewall rule, and that --pair is running (10-minute limit).
- If iPhone hotspot routing blocks reaching the laptop, try Windows Mobile Hotspot with the iPhone connected to it; recheck IP and firewall. Do not enable router forwarding.
- Safari cannot access camera: verify HTTPS and full certificate trust; reopen Safari. Simply bypassing a certificate warning is insufficient.
- Wrong session code: reopen the latest URL printed by the receiver.
- Display connection error: check COM port, close Serial Monitor, restart receiver after reconnecting USB.
- Only one phone should stream at a time. A session code grants control of this counter; keep it private.
