# Squats, curls, touch switching, and feedback

The laptop measures joint angles and times attempts. The Arduino selects the exercise using a Grove touch sensor, shows results on the OLED, and gives a brief feedback cue. The phone still supplies camera images through Safari over your local network.

## Connections

Unplug Arduino USB before changing connections. These instructions are for a standard **digital Grove Touch Sensor** and standard **Grove Buzzer**, not the I2C multi-touch board or an LED bar.

| Part | Connection |
| --- | --- |
| Grove digital touch sensor | Base Shield **D2** |
| Grove buzzer | Base Shield **D3** |
| Single Grove LED | Base Shield **D4** |
| OLED GND | Arduino/shield header **GND** |
| OLED VCC | Dedicated Arduino/shield header **3.3V** |
| OLED SDA | **SDA / A4** |
| OLED SCL | **SCL / A5** |

Keep the Base Shield's Grove power switch at **5V** for the Grove modules. The OLED must remain on the dedicated **3.3V header**, not a 5V Grove power pin. Disconnect the old Grove RGB LCD while testing. The OLED code assumes SSD1306, 128x64 pixels, and checks addresses 0x3C and 0x3D.

## Upload the new Arduino sketch

1. Stop the laptop receiver with Ctrl+C and close Arduino Serial Monitor/Plotter.
2. Open `C:\coding\squat_counter\arduino\exercise_oled\exercise_oled.ino` in Arduino IDE.
3. Install **Adafruit SSD1306** and **Adafruit GFX Library**, including their dependencies, if needed.
4. Select **Arduino UNO R4 Minima** and its actual port. The last detected port was COM6.
5. Upload. This replaces the previous squat-only sketch. Keep this new sketch running while using the phone camera.

## Start the laptop receiver

Check the current Wi-Fi IPv4 and Arduino port first:

```powershell
cd C:\coding\squat_counter
ipconfig
.\.venv\Scripts\python.exe -m serial.tools.list_ports
```

Use your laptop's Wi-Fi IPv4, not its gateway, Tailscale, or WSL address. The most recently observed hotspot address was `172.20.10.6`; it can change. If it changed, update the local firewall rule as described in PHONE_SETUP.md.

```powershell
.\.venv\Scripts\python.exe phone_server.py --host 172.20.10.6 --port COM6
```

Open the newly printed CAMERA PAGE URL in iPhone Safari and tap Start camera. The existing trusted certificate can still be used; do not repeat certificate installation unless the certificate was replaced or expired. Each receiver restart creates a new session code.

## Use it

- Start with the selected exercise's starting position: standing for squats, arm extended for curls.
- Tap and release D2's touch pad to switch **Squats ↔ Curls**. Holding it should switch only once. The OLED shows the mode.
- Switching cancels an unfinished attempt and requires the starting position again. It does not buzz or count the abandoned movement.
- Each mode retains its own attempts and passed count for the running session. These totals are not saved across restarting the laptop program.
- Keep the camera to the side. Show hip, knee, and ankle for squats; shoulder, elbow, and wrist for curls. Use `--side right` if you want the right-side joints instead of the default left-side joints.
- An attempt is a meaningful movement away from the starting position and a return, not a small position adjustment.
- A passed attempt reaches the configured bend target and finishes within the configured total time window.
- A flagged attempt produces **one short buzzer cue**, not continuous buzzing. A passed attempt flashes the D4 LED. Read the displayed result to distinguish missed range, too fast, and too slow.
- Tracking loss and communication loss are not exercise mistakes and must not trigger a form buzzer. Restore visibility and return to the starting position.

## Range and full-motion time

Edit `C:\coding\squat_counter\exercise_config.json`, save, and restart the receiver to apply new targets.

| Mode | Starting extension | Bend target | Whole-attempt time |
| --- | --- | --- | --- |
| Squat | Knee angle at least 160° | Knee angle at most 100° | 2–6 seconds |
| Curl | Elbow angle at least 155° | Elbow angle at most 55° | 2–6 seconds |

**These are prototype defaults, not universal clinical targets or proof of correct form.** Choose appropriate targets with the instructor. This version does not automatically calibrate the participant. The user-selected side and camera perspective affect measured 2D angles.

Time covers the entire detected motion: away from the starting position, through the bend, and back. A pause during the attempt counts toward the duration. Standing still between attempts does not. Movement confirmation and camera sampling introduce some measurement delay. This is not separate lowering/rising timing.

More precisely, timing begins when the smoothed angle crosses 15 degrees below the starting threshold, provided it remains there for 0.12 seconds. It ends when the starting threshold is reached again for 0.12 seconds. The confirmation delay is excluded by using the first threshold-crossing time. Thus, this measures a complete detected cycle, not the first tiny movement away from rest.

For curls, starting another bend before finishing extension can close an incomplete attempt: after the bend, the elbow must open at least 25 degrees above its minimum, then bend again by at least 15 degrees from that return peak for 0.12 seconds. This records one range flag and then requires full starting extension again. Simply holding a partly extended arm does not repeatedly create failed attempts. Tracking gaps longer than 1.5 seconds cancel unfinished motion without an exercise-failure cue.

Both exercise modes use a smaller angle for more bending. For example, increasing a squat target from 100° to 110° permits a shallower bend. The minimum time flags attempts that finish too fast; the maximum flags attempts that finish too slowly. A movement that is still in progress is not repeatedly buzzed for exceeding a time target.

This system does not evaluate spinal alignment, joint loading, pain, or overall exercise safety. The feedback means a configured movement target was missed.

## Physical acceptance checks

Optional no-camera output test (uses simulated reps and makes one short buzz):

```powershell
.\.venv\Scripts\python.exe test_exercise_hardware.py --port COM6
```

Use this new test for exercise_oled.ino. The older test_hardware.py sends the old squat-only protocol and will not work with this sketch. The receiver reports a missing mode handshake if the new firmware is not running.

Compare results against manual observations before presenting the prototype:

| Test | Expected behavior |
| --- | --- |
| Hold the touch pad for several seconds | One mode change, not repeated switching |
| Release and touch again | Switch back |
| Switch halfway through a rep | Cancel unfinished attempt; no buzz; require start again |
| Full squat/curl inside target time | Attempts +1, passed +1, one LED flash |
| Shallow attempt returning to start | Attempts +1, passed unchanged, one range cue |
| Complete cycle faster than configured minimum | One fast cue at completion |
| Complete cycle slower than configured maximum | One slow cue at completion |
| Hold at the bottom | No repeated count or repeated buzzer |
| Hide tracked joints mid-rep | Cancel movement without a form cue |
| Restore visibility while bent | Require starting position before counting |
| Change modes and return | Earlier mode totals retained |
| Disconnect USB | Phone counting continues with connection warning; no repeated cue |
| Stop phone streaming | Display reports loss rather than treating the user as failing |

The Python tests exercise simulated signals and serial data; they do not validate actual camera accuracy, sensor wiring, audible output, or the physical OLED. Compile/upload and perform these hardware checks on your board.

Stop the camera on the phone and press Ctrl+C in the laptop terminal when finished. On USB errors, reconnect the Arduino and restart the receiver with its actual COM port.

References: [Grove Touch Sensor](https://wiki.seeedstudio.com/Grove-Touch_Sensor/), [Grove Buzzer](https://wiki.seeedstudio.com/Grove-Buzzer/).
