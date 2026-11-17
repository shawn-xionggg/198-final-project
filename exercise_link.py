"""Nonblocking touch input and bounded-rate exercise feedback over USB."""
import time


def packet(s):
    angle = -1 if s['angle'] is None else round(s['angle'])
    duration = -1 if s['duration'] is None else round(s['duration'] * 1000)
    return f"EX,{s['mode']},{s['attempts']},{s['passed']},{s['status']},{angle},{s['event_id']},{s['result']},{duration}\n".encode('ascii')


class ExerciseLink:
    def __init__(self, port):
        import serial
        self.serial = serial.Serial(port, 115200, timeout=0, write_timeout=0.3)
        time.sleep(2)
        self.error = None
        self.buffer = b''
        self.last = 0
        self.previous = None
        self.mode = None
        self.mode_revision = None
        self.mode_changed = False
        self.opened = time.monotonic()

    def fail(self, error):
        self.error = f'Arduino disconnected: {error}. Check USB/COM port and restart.'
        print(self.error, flush=True)
        self.close()

    def poll_mode(self):
        self.mode_changed = False
        if self.error:
            return None
        import serial
        try:
            size = min(self.serial.in_waiting, 1024)
            if size:
                self.buffer += self.serial.read(size)
            while b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                parts = line.strip().split(b',')
                if len(parts) in (2, 3) and parts[0] == b'MODE' and parts[1] in (b'SQUAT', b'CURL'):
                    if len(parts) == 3 and (not parts[2].isdigit() or len(parts[2]) > 10):
                        continue
                    revision = int(parts[2]) if len(parts) == 3 else None
                    mode = parts[1].decode('ascii')
                    if mode != self.mode or revision != self.mode_revision:
                        self.mode_changed = True
                    self.mode, self.mode_revision = mode, revision
            if len(self.buffer) > 128:
                self.buffer = b''
            if self.mode is None and time.monotonic() - self.opened > 5:
                self.fail('No exercise-mode response. Upload exercise_oled.ino and restart')
            return self.mode
        except (serial.SerialException, OSError) as error:
            self.fail(error)
            return None

    def update(self, snapshot):
        if self.error:
            return
        import serial
        now = time.monotonic()
        event = (snapshot['mode'], snapshot['event_id'], snapshot['attempts'])
        if now - self.last < 0.2 and event == self.previous:
            return
        data = packet(snapshot)
        try:
            if self.serial.write(data) != len(data):
                raise serial.SerialTimeoutException('Incomplete USB write')
            self.last, self.previous = now, event
        except (serial.SerialException, OSError) as error:
            self.fail(error)

    def close(self):
        import serial
        try:
            self.serial.close()
        except (serial.SerialException, OSError):
            pass
