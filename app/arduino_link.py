"""USB display protocol: STATE,count,phase,angle followed by newline."""
import time


def packet(reps, phase, angle):
    status = 'LOST' if angle is None else {'Standing': 'STAND', 'Squatting': 'DOWN'}.get(phase, 'READY')
    value = -1 if angle is None else round(angle)
    return f'STATE,{reps},{status},{value}\n'.encode('ascii')


class ArduinoLink:
    def __init__(self, port):
        import serial
        self.serial = serial.Serial(port, 115200, timeout=0.2, write_timeout=0.5)
        time.sleep(2)  # Allow board startup after opening USB.
        self.last = 0
        self.previous = None
        self.error = None

    def update(self, reps, phase, angle):
        if self.error:
            return
        import serial
        now = time.monotonic()
        data = packet(reps, phase, angle)
        if now - self.last >= 0.2 or self.previous != reps:
            try:
                written = self.serial.write(data)
                if written != len(data):
                    raise serial.SerialTimeoutException('Incomplete USB write')
            except (serial.SerialException, OSError) as error:
                self.error = f'Arduino display disconnected: {error}. Check USB/COM port and restart the receiver.'
                print(self.error, flush=True)
                self.close()
                return
            self.last, self.previous = now, reps

    def close(self):
        import serial
        try:
            self.serial.close()
        except (serial.SerialException, OSError):
            pass
