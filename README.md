# Exercise tracker

An iPhone camera and laptop track squats and curls. An Arduino displays results and controls the touch sensor, LED, and buzzer.

From the repository folder in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\app\phone_server.py --host 172.20.10.6 --port COM6
```

Replace the example IP and COM port with your laptop's hotspot address and Arduino port. Open the newly printed camera URL on your phone.

- [Arduino wiring and demo setup](docs/EXERCISE_SETUP.md)
- [First-time phone and hotspot setup](docs/PHONE_SETUP.md)
- [Presentation guide](docs/PRESENTATION_GUIDE.md)

Edit `exercise_config.json` to change the range and timing targets. The model downloads on first run.
