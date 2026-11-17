  # ECE 198 Exercise Tracker Presentation Guide

Preparation for the November 10 2026 progress presentation

## 1 Project overview and key talking points

This project is a single-person exercise-tracking prototype for the CCCARE context. An iPhone supplies camera images, a Windows laptop estimates body-joint positions and evaluates repetitions, and an Arduino UNO R4 Minima controls a touch sensor, OLED display, LED, and buzzer. The current software supports squats and biceps curls.

The main result to communicate is that the system separates **attempts** from **attempts that meet configured range and total-time targets**. It does not diagnose injuries or certify overall exercise form. A target miss is a measurable feedback event, not proof that a movement is unsafe.

### A short explanation to rehearse

“Our prototype uses a phone camera to track exercise movement without attaching a movement sensor to the participant. A pretrained pose model runs on a laptop and finds the joints we need. Our own rules calculate the knee or elbow angle, recognize a movement cycle, and check its range and total duration. An Arduino displays the results and gives physical feedback. A touch sensor switches between squats and curls.”

### The complete system in one line

```text
iPhone Safari -- Wi-Fi hotspot and HTTPS --> Laptop running YOLO
Laptop -- USB serial --> Arduino -- I2C --> OLED
Touch D2 --> Arduino -- USB mode message --> Laptop
Arduino --> Buzzer D3 and LED D4
```

### Five points to remember

- The phone is the camera; the laptop runs the AI; the Arduino handles physical controls and feedback.
- YOLO finds joints. The project code, not YOLO alone, decides when a rep ends and whether targets were met.
- A rep is judged after a meaningful movement cycle. Holding a position does not repeatedly add reps.
- “Met targets” increases only when both range and total time pass. The D4 LED then flashes for 0.5 seconds.
- A flagged attempt causes one short buzzer cue. Missing tracking, switching modes, and disconnection are not form errors.

### Presentation scope

The announced format is seven minutes presenting progress, followed by eight minutes of questions and feedback. Bring the prototype and a backup demonstration video. Verify the assigned room and time on Learn; they are not established in this guide. Treat the rest of this document as a reference, not a script to read in full.

## 2 User need and development history

The project summary describes an instructor supervising 10–12 patients or up to 30 graduated participants. The intended benefit is to make attempted reps and target completion easier to see, helping the instructor decide who needs a check-in. Those are the intended users and future operating context. The current prototype processes only one detected person at a time and does not provide a class dashboard.

### Original concept and current prototype

The earlier concept used an Arduino with a thigh-mounted ADXL335 accelerometer, a stationary HC-SR04 ultrasonic sensor, a MAX30102 finger sensor, and a display. The current camera-based implementation is a different measurement approach. Do not describe all of these sensors as operating together today.

| Component or idea | Original role | Current status |
| --- | --- | --- |
| ADXL335 accelerometer | Measure thigh movement or tilt | Earlier bench work; not used by the camera counter |
| HC-SR04 ultrasonic sensor | Distance as a squat-depth proxy | Earlier proposal; no current integration |
| MAX30102 optical sensor | Estimate heart rate | Earlier proposal; no current integration |
| Grove RGB LCD V4 | Show results with colored backlight | Troubleshooting was unsuccessful; replaced in the active sketch by OLED |
| Calibration button and knob | Set individual depth and tempo | Proposed; not implemented as physical calibration |
| Vibration motor | Quiet physical feedback | Proposed; current output is a buzzer and LED |
| Grove touch sensor | Initially proposed pause or assistance input | Now switches squat and curl modes |

### How to explain the design change

The camera approach allows the team to explore movement recognition without a thigh strap. It also creates new requirements: a clear side view, adequate lighting, a laptop, and a reliable local connection. Present this as a design tradeoff under evaluation, not evidence that cameras are always better than wearables.

The original brief should still guide the final design. Confirm whether a laptop is permitted in the final deliverable and whether the course expects more sensing or processing on the microcontroller. At present, the Arduino is a controller and feedback device, not the machine performing the pose inference.

### Engineering lesson from the sensor work

An accelerometer measures acceleration, including gravity. Tilting it changes the gravity component on its axes. Those readings are not a reliable direct measurement of position. If the wearable concept returns, it needs its own measurement model and validation rather than treating raw acceleration as squat depth.

## 3 Every active hardware component

| Component | What it does | Why it is present |
| --- | --- | --- |
| iPhone camera | Captures the participant in Safari | Reuses an available camera without a dedicated phone app |
| iPhone Personal Hotspot | Connects the laptop and phone locally | Avoids relying on campus device-to-device networking |
| Windows laptop | Receives images, runs YOLO, applies rules | Provides the processing and software environment |
| USB data cable | Connects laptop to Arduino and normally powers the board | Carries small result messages and exercise selections |
| UNO R4 Minima | Reads touch and drives feedback | Provides physical interaction with the software system |
| Grove Base Shield | Exposes labeled sockets and header connections | Simplifies connection of Grove modules |
| Digital Grove Touch Sensor | Reports touched or released state | Selects squats or curls without using the laptop keyboard |
| Grove buzzer | Produces a brief audible cue | Signals a completed attempt missed a target |
| Single Grove LED | Lights briefly on a passing attempt | Gives positive visual feedback |
| SSD1306 OLED | Shows exercise, counts, status, angle, and last duration | Makes feedback visible at the exercise station |

### Important hardware distinctions

The UNO R4 Minima does not provide built-in Wi-Fi. In this prototype the wireless link ends at the laptop; the Arduino remains connected by USB. No ESP32 is installed. “Wireless phone camera” does not mean the display station is fully wireless.

The OLED is assumed to be a 128 by 64 pixel SSD1306 module, matching the course material and the software configuration. It is different from the Grove RGB LCD. OLED pixels emit light directly, so there is no separate backlight to turn on. The OLED sketch checks the usual I2C addresses 0x3C and 0x3D; detecting an address alone does not prove the controller model.

The USB cable must carry data. The Arduino appearing as COM6 and the successful standalone D4 test are evidence that communication and a digital output worked in that test. They do not prove the entire exercise system is accurate or that every cable connection remains reliable.

### Inputs and outputs

Inputs are camera images, the touch sensor, and configuration settings. Outputs are the phone status page, OLED text, the D4 LED pulse, and the D3 buzzer cue. The model produces joint coordinates as an intermediate result, not a direct “good form” decision.

## 4 Wiring and electrical interfaces

Disconnect USB before moving wires. The following wiring describes the current exercise sketch, not the older Grove LCD tests.

| Part or pin | Connection | Signal or purpose |
| --- | --- | --- |
| Grove digital touch module | Shield D2 | Digital input; HIGH means touched |
| Grove buzzer module | Shield D3 | Tone output; 2300 Hz cue |
| Single Grove LED module | Shield D4 | Digital output; HIGH lights LED |
| OLED GND | Header GND | Common electrical reference |
| OLED VCC | Dedicated header 3.3V | Display power specified in the course handout |
| OLED SDA | SDA header or A4 | I2C data |
| OLED SCL | SCL header or A5 | I2C clock |
| Laptop USB | Arduino USB connector | Power and USB serial data |

Keep the Grove power switch at 5V for the Grove modules. The OLED remains on the dedicated 3.3V header, not on a 5V Grove power pin. Use the labeled header connections and appropriate jumper wires for the OLED. Disconnect the earlier Grove RGB LCD while testing this arrangement.

### What the communication terms mean

**Digital input or output:** a pin is read or driven as HIGH or LOW. The touch module handles touch sensing internally and presents a digital state to D2. The LED is switched using D4.

**I2C:** a two-signal communication bus using SDA for data and SCL for clock. Each responding device has an address. The OLED is driven through Arduino's Wire library at 100 kHz in this sketch. Screen contents are assembled in memory and sent with display.display().

**USB serial:** a stream of bytes between the laptop and Arduino. Both sides use 115200 as the configured serial baud rate. The application adds comma-separated fields and a newline so each message can be recognized. COM6 is a Windows device-port name, not a network port.

**Tone output:** tone(D3, 2300) produces the buzzer drive signal. The loop stops it after 180 milliseconds without deliberately pausing the whole program.

### Hardware limits to acknowledge

These instructions follow the supplied course power wiring. The exact OLED breakout's electrical characteristics and I2C pull-ups still matter when validating a final design, especially because the UNO R4 is a 5V board. Do not infer that every generic OLED accepts 5V simply because the Grove modules do. The D2 instructions assume the basic digital Grove Touch Sensor, not an I2C touch keypad.

## 5 Phone capture and local networking

The phone opens a local webpage in Safari. Start camera requests camera permission, selects the rear or front camera, and displays a preview. It does not request microphone audio. Safari must remain open; moving the page into the background stops camera capture in this implementation.

### One image through the connection

1. The page draws a camera frame into an HTML canvas.
2. It reduces the longest dimension to at most 640 pixels and encodes JPEG at a quality setting of 0.75.
3. It sends the JPEG to the laptop's /frame endpoint using HTTPS and the session-code header.
4. It waits for the laptop's result before scheduling another frame, with an additional 80 millisecond delay.
5. It updates the visible mode, attempts, passes, angle, last result, and duration.

This is a sequence of individual image requests, not a guaranteed 30 frames per second stream. Actual update speed depends on capture, network delay, image decoding, and YOLO inference. No measured frame rate or end-to-end latency has been established.

### Why HTTPS and the certificate are needed

Browser camera access requires a secure context. The project therefore serves the page on HTTPS port 8443 using a locally generated certificate. A one-time --pair option exposes only the public root certificate on HTTP port 8080 for ten minutes. The iPhone must install and trust that local certificate. The HTTP endpoint does not receive camera images.

The root certificate lasts 90 days; server certificates are generated for the selected laptop IP and last up to 30 days. The private keys stay in .phone-tls. Keep that folder private and remove the iPhone trust profile when it is no longer needed. Nothing in the project automatically changes the laptop's system certificate trust store.

### What is and is not exposed

The receiver binds to the chosen private laptop address. A firewall helper limits permitted Python traffic to that address, the local subnet, the Private profile, and ports 8080 and 8443. No router port forwarding or public tunnel is used. A random session code protects processing and control requests; a new code is created on each restart. The code also checks browser Origin when supplied, caps incoming image size, and avoids logging camera data or session codes.

Images are decoded and processed in memory, not intentionally recorded by this application or sent to an external AI service. Initial dependency/model downloads require internet. Other laptop applications may still use hotspot mobile data. This is a local prototype, not a security audit or a production authentication system.

## 6 Pose estimation and the angle calculation

The current model file is yolo26n-pose.pt. It is a pretrained Ultralytics YOLO Pose model. The team did not train a custom model for this prototype. YOLOE, discussed initially, is a different object detection and segmentation model; it is not the model used by the current counter.

### How the laptop turns an image into an angle

OpenCV decodes the incoming JPEG into an image array. YOLO returns detected people and body keypoints. The receiver accepts a measurement only when exactly one person is detected and all three required joints have confidence of at least 0.5. Detection also uses a 0.5 confidence threshold. These confidence values are filtering settings, not a claim of 50 percent or any other measured system accuracy.

| Mode | Angle location | Left keypoint indices | Right keypoint indices |
| --- | --- | --- | --- |
| Squat | Knee between hip and ankle | Hip 11, knee 13, ankle 15 | Hip 12, knee 14, ankle 16 |
| Curl | Elbow between shoulder and wrist | Shoulder 5, elbow 7, wrist 9 | Shoulder 6, elbow 8, wrist 10 |

The default is the left side. --side right selects the right side. The person should be filmed from the side with the relevant joints visible. The model does not automatically decide which exercise the person is doing; the touch-selected mode determines the joints and rules.

### The dot product formula

For three points A, B, and C, B is the joint at the middle. Define u = A - B and v = C - B. The angle comes from the dot-product relationship: u dot v = length(u) times length(v) times cos(theta).

```python
u = (A[0] - B[0], A[1] - B[1])
v = (C[0] - B[0], C[1] - B[1])
length = math.hypot(*u) * math.hypot(*v)
cosine = (u[0]*v[0] + u[1]*v[1]) / length
theta = math.degrees(math.acos(max(-1, min(1, cosine))))
```

The actual helper checks for a nearly zero denominator before dividing. Clamping cosine between -1 and 1 prevents small floating-point errors from breaking acos. Straight joints approach 180 degrees; bending reduces the angle.

This is a projected 2D angle, not a 3D anatomical measurement. Camera perspective, hidden joints, clothing, and position can affect it. The helper retains the name knee_angle() even when it is used to calculate the elbow angle; the mathematics is the same.

## 7 Movement recognition and noise handling

One frame cannot prove a repetition is complete. The tracker remembers the movement stage and follows the angle over time. Each exercise has its own attempt and pass totals, while one active movement is tracked at a time.

| State | Meaning | Next important event |
| --- | --- | --- |
| READY | Starting position has not been confirmed | Hold the configured starting extension |
| START | Starting position is confirmed | Move meaningfully away from it |
| MOVING | An attempt is underway | Return to the starting threshold |
| LOST | Required joints or recent frames are missing | Recover tracking and confirm start again |

### Starting and ending a movement

The start position must persist for 0.12 seconds. An attempt begins when the smoothed angle falls at least 15 degrees below the configured start angle and stays below that departure threshold for 0.12 seconds. For current settings, departure is at or below 145 degrees for squats and 140 degrees for curls.

While moving, the tracker remembers the smallest angle reached. On return, the starting angle must be reached for 0.12 seconds before the attempt is completed. The stored first threshold-crossing time is used for timing, excluding the extra confirmation delay. Staying at the top after completion does not count again because a new departure is required.

### Smoothing and hysteresis

Raw joint coordinates vary between frames. The code smooths the calculated angle using an exponential average:

```python
alpha = 1 - math.exp(-dt / 0.06)
smooth = smooth + alpha * (angle - smooth)
```

dt is the time between processed samples. The 0.06 second time constant makes the smoothing depend on elapsed time rather than a fixed number of frames. Smoothing reduces jitter but adds delay. The different departure and return thresholds provide hysteresis: a small movement around the standing threshold does not repeatedly start and end attempts.

### Tracking failures and exercise switches

Invalid angles, insufficient joint confidence, or multiple detected people cancel the unfinished attempt. A gap greater than 1.5 seconds also requires a fresh starting position. Completed totals remain. There is no buzzer for this cancellation.

Touching the mode sensor similarly cancels an unfinished attempt. The mode revision counter records even a rapid switch away and back, preventing an old partial movement from carrying across exercises. Starting already bent does not generate a rep merely by standing up or extending the arm.

## 8 Range checks and whole movement timing

| Setting | Squats | Curls |
| --- | --- | --- |
| Starting and ending angle | Knee at least 160 degrees | Elbow at least 155 degrees |
| Bend target | Knee at most 100 degrees | Elbow at most 55 degrees |
| Minimum total time | 2 seconds | 2 seconds |
| Maximum total time | 6 seconds | 6 seconds |

These are editable prototype defaults in exercise_config.json. They are not universal clinical standards, and there is no automatic participant calibration. An instructor should select suitable targets before use. The current timing rule evaluates the entire detected cycle, not separate lowering and rising phases.

### How attempts and passes differ

An attempt is counted when a recognized cycle closes. A shallow movement can count as an attempt if it crosses the departure threshold and returns, even if it never reaches the bend target. “Met targets” increases only if the range and time checks both pass.

```python
duration = end_time - start_time
missed_range = minimum_angle > target_angle
too_fast = duration < min_seconds
too_slow = duration > max_seconds
passed = not (missed_range or too_fast or too_slow)
```

This snippet summarizes the full-cycle decision; the real code also handles incomplete curl extension. Exactly 2 or 6 seconds is within the default window. A pause at the bottom counts toward duration. Waiting between reps does not. Because timing begins at the meaningful departure threshold, it does not measure the first tiny movement away from rest. Host processing and network timing also limit precision.

### Incomplete curl extension

If the elbow opens at least 25 degrees above the minimum angle reached and then bends again by at least 15 degrees from that return peak, held for 0.12 seconds, the tracker closes one incomplete attempt. It flags range and requires starting extension again. Holding a partially extended arm does not repeatedly generate failures. This rule is a heuristic that still needs camera testing.

### Reading the result

- OK means both targets passed: attempts and passes rise, and D4 flashes.
- RANGE means the bend target or required curl extension was missed.
- FAST or SLOW means the total detected cycle was outside the timing window.
- RANGE_FAST or RANGE_SLOW means both checks failed.
- NONE means there is no completed result to report yet.

If attempts rises but passes remains zero, read the result before blaming the LED. If attempts also stays zero, check starting position, departure, full return, visibility, and selected exercise. A movement still underway is not repeatedly buzzed for taking too long.

## 9 Arduino control and the USB message protocol

The active Arduino sketch is arduino\exercise_oled\exercise_oled.ino. Once uploaded, it keeps running on the board. Starting Python does not replace it; Python sends measurements to it. Only the last uploaded sketch runs, so do not upload the old LED-only or LCD test before the demonstration.

### Touch and mode selection

D2 is read as a digital input. A changed touch state must remain stable for 60 milliseconds. The code requires a release before another touch can switch mode, so holding the pad triggers only one change. The Arduino is the source of the selected exercise. It sends the selection immediately when possible and repeats it approximately every 500 milliseconds.

```text
MODE,CURL,3
```

This means curl mode, revision 3. The revision increments on each touch switch. The laptop checks for mode changes before and after pose inference and discards a frame if the mode changed during processing. Separate counts are retained on the laptop for each mode during that running session.

### Feedback from the laptop

```text
EX,SQUAT,4,3,START,171,7,OK,3200
```

The fields are prefix EX, exercise, attempts, passes, movement state, angle, event ID, result, and duration in milliseconds. This example means four attempts, three passes, a 171-degree current angle, event 7, and a last passing attempt lasting 3.2 seconds. A value of -1 represents an unavailable angle or duration.

Updates are normally limited to one every 0.2 seconds, with immediate sends when the mode, event ID, or attempt count changes. Newlines separate complete messages. Input lengths and recognized fields are checked so partial or malformed messages are not blindly interpreted.

### Why it does not buzz repeatedly

Each completed attempt receives a new event ID. The Arduino triggers feedback only for a new event while already connected. Repeated status packets cannot replay that event. The first packet after connection establishes a baseline rather than replaying an old result.

A passing result drives D4 HIGH for 500 milliseconds. A flagged result starts a 2300 Hz tone on D3 for 180 milliseconds. millis() checks stop those outputs while the main loop continues reading inputs. Tracking loss silences the buzzer; a mode switch or three-second communication timeout also clears feedback.

The OLED shows the selected exercise, attempts, passes, current state, last result, angle, and last duration. The old result can remain visible as history while the current state changes. “Waiting for PC” indicates there is no recent laptop connection.

## 10 Software files and responsibilities

The working project is in C:\coding\squat_counter. The active phone workflow uses the following files. Older sketches are historical tests or earlier display variants, not additional programs that must all run.

| File | Responsibility |
| --- | --- |
| phone_camera.html | Safari camera preview, JPEG capture, session code, results, reset |
| phone_server.py | HTTPS endpoints, image decoding, YOLO inference, mode polling, integration |
| exercise_logic.py | Pure Python movement states, range/time rules, per-mode counts |
| exercise_config.json | Editable squat/curl angles and timing windows |
| exercise_link.py | USB mode parsing, result packets, throttling, connection-error isolation |
| phone_tls.py | Generates local root and server certificates |
| phone-firewall.ps1 | Adds or removes restricted Windows firewall rules |
| arduino\exercise_oled\exercise_oled.ino | Active OLED, touch, buzzer, and LED firmware |
| squat_counter.py | Earlier webcam-only counter and the reusable angle helper |
| yolo26n-pose.pt | Downloaded pretrained pose-model weights |
| requirements.txt | Phone-receiver dependency entry point |
| test_exercise_hardware.py | Simulated good and flagged results for physical output testing |
| test_exercise_logic.py and test_exercise_link.py | Movement and serial-protocol unit tests |
| test_phone.py | Local HTTPS, session-code, payload, and endpoint checks |

### Libraries and what they contribute

Ultralytics loads the pretrained model; PyTorch runs its neural-network computations. OpenCV decodes images, NumPy represents image arrays, and Python's math module computes angles and filtering. PySerial connects to the Arduino. Cryptography creates certificates; Python's ssl and HTTP server modules handle the local secure connection. Threading allows physical controls to be polled between image requests.

On the Arduino, Wire provides I2C communication. Adafruit SSD1306 handles the OLED controller, Adafruit GFX supplies text and drawing functions, and installed dependencies such as BusIO support those libraries. The serial parser and movement feedback behavior are project code.

### Concurrency and failure handling

The receiver uses a lock so image processing, mode changes, reset, and status updates do not alter the tracker simultaneously. A control loop attempts to run every 50 milliseconds and skips a pass while inference holds the lock. It marks stale camera input as lost and keeps the Arduino informed even if no new frame arrives. Busy frame requests are retried by the phone.

USB read/write failures disable the display link and show a warning while phone counting can continue. Automatic USB reconnection is not implemented; reconnect and restart the receiver. If no mode message arrives within five seconds, the program asks for the new exercise firmware rather than silently assuming an older sketch supports the protocol.

## 11 Starting the demonstration and troubleshooting

### Before presenting

1. Wire the components, upload exercise_oled.ino, and verify the OLED startup screen.
2. Connect the laptop to the iPhone hotspot. Confirm the current laptop Wi-Fi IPv4 address and Arduino COM port.
3. Close Serial Monitor and Serial Plotter. They can interfere with access to the same serial port.
4. Verify the local certificate and restricted firewall setup. Do not reinstall the certificate unless it changed or expired.
5. Frame one person from the side and check all required joints are visible. Use realistic configured targets.

```powershell
cd C:\coding\squat_counter
ipconfig
.\.venv\Scripts\python.exe -m serial.tools.list_ports
.\.venv\Scripts\python.exe .\app\phone_server.py `
  --host 172.20.10.6 --port COM6
```

The address and port above are the last observed values, not permanent identifiers. Open the new CAMERA PAGE URL printed after each restart. Tap Start camera in Safari. For right-side tracking, append --side right. A first-time certificate download uses --pair; normal runs do not need it.

### Quick hardware check without movement

```powershell
.\.venv\Scripts\python.exe .\app\test_exercise_hardware.py --port COM6
```

Run this only while the receiver and Serial Monitor are stopped. It sends simulated results: a passing event should flash D4, and a range failure should buzz. These are synthetic test events, not actual measured reps. The older test_hardware.py uses the previous protocol and is not the right test for the exercise sketch.

| Symptom | First checks |
| --- | --- |
| Attempts rises but passes stays zero | Read RANGE, FAST, or SLOW; confirm settings and angle visibility |
| Both counts stay zero | Correct mode, clear joints, confirm start, depart, then return fully |
| D4 never flashes | Does passes increase? Try the simulated hardware test |
| USB Write timeout | Correct sketch and COM port; close Serial Monitor; reconnect data cable |
| OLED black | 3.3V and GND, SDA/SCL, detected address, SSD1306 libraries, correct sketch |
| Phone cannot open page | Current hotspot IP, private-network firewall, receiver running |
| Safari camera unavailable | Trusted HTTPS, camera permission, Safari in foreground |

Tap Stop camera and press Ctrl+C to end the session. The Arduino may remain powered and show its waiting state. Before the presentation, record a short backup video of a verified demonstration rather than relying entirely on live networking.

## 12 Evidence limitations and next engineering steps

### What can currently be claimed

The implementation has 42 passing Python tests covering the original counter, exercise rules, USB behavior, and local HTTPS endpoints. A desktop firmware simulation checked touch debounce, duplicate-event suppression, timed output shutoff, mode revisions, loss, and reconnection behavior. A real YOLO invocation on a blank image returned tracking loss for both exercise modes; that is a plumbing check, not a pose-accuracy benchmark.

The standalone D4 LED test was reported to work. The old Grove RGB LCD did not produce a successful display during troubleshooting. In the most recent exercise discussion, “Met targets” remained zero. That does not establish a faulty LED because the firmware intentionally flashes only for passing results. End-to-end passing-rep feedback still needs to be demonstrated and recorded.

The Arduino compiler invoked from the assistant environment failed with a Windows DLL relocation error. Desktop simulation is not equivalent to a successful UNO R4 build, upload, or physical buzzer test. Compile in Arduino IDE and verify the actual outputs before claiming the hardware integration is complete.

### Testing to complete tonight

| Test | Expected outcome | Record |
| --- | --- | --- |
| Ten full cycles per mode | One attempt per cycle | Manual count versus system count |
| Shallow cycle returning to start | Attempt but no pass; one range cue | Displayed result and observed feedback |
| Fast and slow complete cycles | Appropriate timing flag | Manual elapsed time versus reported time |
| Hold at bottom and top | No repeated counts or buzz | Any false events |
| Hold touch and then release | One switch per touch | Mode transitions |
| Switch halfway through a rep | Cancellation without failure cue | Counters before and after |
| Hide joints or pause camera | Lost state, no form cue | Recovery behavior |

Do not invent an accuracy percentage. Report measured count error, missed reps, false reps, timing error, and test conditions once data exists. Separate people or recordings used to tune thresholds from those used to evaluate the result.

### Remaining limitations and priorities

The system has no persistent participant records, no identity tracking, no class dashboard, and no custom model training. It requires a laptop and one visible person. A new person replacing another without an obvious gap may not be distinguished. Range is based on 2D angles, and timing is based on laptop processing timestamps, not a synchronized motion-capture clock.

Prioritize a reliable passing-rep demonstration, instructor-approved targets, calibration, varied-user testing, and setup simplicity. Later work could compare the wearable sensor approach, remove the laptop through on-phone processing, or add an instructor overview. Do not call these implemented features.

## 13 Seven minute presentation plan

### Zero to forty five seconds

Explain the user need: an instructor wants to see attempts and target completion without watching every rep continuously. Introduce the current scope as a single-person prototype for squats and curls.

Suggested wording: “We are measuring two specific things: whether a movement reaches its target range and whether the entire detected cycle fits the selected time window.”

### Forty five seconds to one minute thirty

Show the system diagram. Point to the phone, laptop, Arduino, touch sensor, OLED, buzzer, and LED. Explain that the phone sends images locally, the laptop performs inference and counting, and the Arduino controls physical feedback.

### One minute thirty to three minutes

Demonstrate only behavior verified before the presentation. Show the selected mode, a complete attempt, and the counts. If a passing example is verified, show the LED. Show a controlled flagged example or the explicitly labeled simulated output test. Touch to switch modes and show that the new exercise is selected.

If live networking fails, use the backup recording and explain the failure accurately. Do not describe simulated messages as camera-recognized exercise.

### Three to four minutes

Explain the angle and movement logic. Show the three joints, the dot-product formula, and the start–move–return sequence. Explain that state memory prevents repeated counting while holding a pose. Mention smoothing and the short confirmation interval.

### Four to five minutes

Explain attempts versus passes. Use a numerical illustration: a detected squat with a minimum knee angle of 95 degrees and duration of 3.2 seconds passes the current defaults; one reaching only 120 degrees misses range. These are illustrative cases, not measured experimental results.

### Five to six minutes

Discuss progress and engineering evidence. Explain the successful standalone LED test, the display change, the software tests, and the remaining live-validation work. Describe the USB-timeout fix: hardware communication failure now produces a separate warning rather than stopping camera processing.

### Six to seven minutes

Present the next steps and ask for targeted feedback. “Are the laptop-based architecture and our definition of an attempt appropriate for this project? What validation would you expect before using range and timing feedback with participants?” Confirm whether individualized calibration and instructor-set targets should be prioritized.

### What to have on the table

Bring the assembled prototype, data-capable USB cable, charged phone and laptop, known-good configuration, a backup video, the active sketch, and a small table of actual test results. Know where to find finish(), the angle helper, the firmware receive() function, and the touch logic if asked to show code.

## 14 Likely questions and concise answers

### Did you train YOLO

No. The prototype uses pretrained YOLO Pose weights to locate joints. The exercise rules, timing, communication, and feedback are implemented around those outputs. There is no project-specific training dataset or training run to report.

### Why use an Arduino if the laptop counts

It provides the physical interface: touch input, OLED feedback, buzzer, and LED. The current architecture splits compute-heavy vision from simple local hardware control. Whether this division meets the final course requirements should be confirmed with the teaching team.

### What exactly does bad form mean here

The implementation flags missed configured range or total-time targets. It does not assess every aspect of form, pain, load, balance, spinal alignment, or exercise safety. “Missed target” is the more accurate term.

### Why does the LED sometimes not light

The LED is a pass indicator, not an attempt indicator. Both range and total time must pass, the Arduino must be receiving the current protocol, and the event must be new. Read the result and passes count, then isolate hardware with the simulated test if necessary.

### Why not use a single angle threshold

A threshold only describes a position. The tracker needs a confirmed start, a meaningful departure, and a return to distinguish a full cycle from a hold, jitter, or startup while bent. Different departure and return thresholds reduce chatter.

### What happens if the camera loses the person

The unfinished attempt is cancelled without a form buzzer. The person must return to the starting position. Completed totals remain. If images stop, the background control loop marks tracking lost after 1.5 seconds.

### What happens if the touch pad is held or tapped twice

A 60 millisecond debounce and release requirement produce one switch per held touch. Each switch increments a revision counter, so even a quick switch away and back cancels the old unfinished movement.

### Is all of it wireless or stored in the cloud

No. Phone images travel locally over Wi-Fi to the laptop. The laptop connects to the Arduino by USB. The program does not intentionally save camera frames or use cloud inference. Initial software/model downloads are separate from runtime image processing.

### How accurate is it and how did you use AI assistance

Camera accuracy has not yet been quantified. Explain the test coverage and show only results actually collected. Code and documentation were developed with AI assistance; describe your own wiring, testing, decisions, and understanding accurately, and follow the course's disclosure rules. Do not claim to have independently authored or validated work you did not do.

## 15 Code walkthrough and reference sources

### Code locations worth knowing

- exercise_logic.py, update(): filters angles, confirms stages, tracks minimum bend, detects returns and incomplete curls.
- exercise_logic.py, finish(): computes total duration, checks range/time, increments attempts and passes, and assigns an event ID.
- phone_server.py, frame(): decodes a JPEG, runs the model, selects joints, and updates the tracker.
- phone_server.py, controls(): polls touch mode and marks stale camera input as lost between image requests.
- exercise_link.py, poll_mode() and update(): receives mode revisions and sends result packets with USB-failure isolation.
- exercise_oled.ino, touch(): debounces the sensor and switches mode.
- exercise_oled.ino, receive(): validates packets and triggers one feedback event.
- exercise_oled.ino, loop(): keeps processing touch and USB while timing the outputs.

### The passing decision in the actual code

```python
self.counts[self.mode]['attempts'] += 1
self.counts[self.mode]['passed'] += self.result == 'OK'
self.event_id += 1
```

The Boolean expression adds one only when the result is OK. The global event ID is not reused when counts are reset, preventing a repeated packet from being mistaken for a new feedback event.

```cpp
if (connected && event > lastEvent && strcmp(s, "LOST")) {
  if (!strcmp(r, "OK")) {
    digitalWrite(LED_PIN, HIGH);
    flashing = true;
    flashAt = now;
  } else if (strcmp(r, "NONE")) {
    tone(BUZZER_PIN, 2300);
    buzzing = true;
    buzzAt = now;
  }
}
```

strcmp returns zero for equal strings. Therefore !strcmp(r, "OK") means the result equals OK. The time checks later in loop() turn the LED off after 500 milliseconds and the buzzer off after 180 milliseconds.

### Sources for further explanation

- Current project code and configuration in C:\coding\squat_counter, reviewed for this guide; original project context from ece198-summary.md and the supplied presentation announcement.
- Ultralytics Pose documentation: https://docs.ultralytics.com/tasks/pose/
- Arduino UNO R4 Minima pinout: https://docs.arduino.cc/resources/pinouts/ABX00080-full-pinout.pdf
- Grove Base Shield: https://wiki.seeedstudio.com/Base_Shield_V2/
- Grove Touch Sensor: https://wiki.seeedstudio.com/Grove-Touch_Sensor/
- Grove Buzzer: https://wiki.seeedstudio.com/Grove-Buzzer/
- Adafruit SSD1306 library: https://github.com/adafruit/Adafruit_SSD1306
- Browser camera API: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- iPhone certificate trust: https://support.apple.com/en-ca/102390

For the presentation, lead with the problem, demonstrate what works, explain the engineering choices, and use the remaining uncertainties to ask useful questions.
