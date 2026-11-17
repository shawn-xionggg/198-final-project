"""Range and whole-cycle duration checks, independent of camera and hardware."""
import copy
import math

DEFAULTS = {
    'SQUAT': dict(start_angle=160, target_angle=100, min_seconds=2, max_seconds=6),
    'CURL': dict(start_angle=155, target_angle=55, min_seconds=2, max_seconds=6),
}


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('Settings must be an object containing SQUAT and CURL')
    for mode in DEFAULTS:
        if mode not in config:
            raise ValueError(f'Missing {mode} settings')
        c = config[mode]
        if not isinstance(c, dict):
            raise ValueError(f'{mode} settings must be an object')
        for name in DEFAULTS[mode]:
            if name not in c or isinstance(c[name], bool) or not isinstance(c[name], (int, float)) or not math.isfinite(c[name]):
                raise ValueError(f'{mode}.{name} must be a finite number')
        if not 0 < c['target_angle'] < c['start_angle'] - 20 < 180:
            raise ValueError(f'{mode}: target must be at least 20 degrees below start')
        if not 0 < c['start_angle'] < 180:
            raise ValueError(f'{mode}: start angle must be below 180')
        if not 0 < c['min_seconds'] < c['max_seconds'] <= 120:
            raise ValueError(f'{mode}: require 0 < min_seconds < max_seconds <= 120')


class ExerciseTracker:
    def __init__(self, config=None):
        self.config = copy.deepcopy(config if config is not None else DEFAULTS)
        validate_config(self.config)
        self.mode = 'SQUAT'
        self.counts = {mode: {'attempts': 0, 'passed': 0} for mode in DEFAULTS}
        self.event_id = 0
        self.result = 'NONE'
        self.duration = None
        self.cancel('READY')

    def cancel(self, status='READY'):
        self.status = status
        self.smooth = None
        self.last = None
        self.armed = False
        self.started = None
        self.minimum = 180
        self.return_peak = None
        self.pending = None
        self.since = None

    def set_mode(self, mode):
        if mode not in self.counts:
            raise ValueError('Unknown exercise')
        if mode != self.mode:
            self.mode = mode
            self.result, self.duration = 'NONE', None
            self.cancel()

    def toggle_mode(self):
        self.set_mode('CURL' if self.mode == 'SQUAT' else 'SQUAT')

    def reset(self):
        self.counts[self.mode] = {'attempts': 0, 'passed': 0}
        self.result, self.duration = 'NONE', None
        self.cancel()

    def stable(self, label, now):
        if self.pending != label:
            self.pending, self.since = label, now
        return label is not None and now - self.since >= 0.12

    def finish(self, end, incomplete=False):
        c = self.config[self.mode]
        self.duration = max(0, end - self.started)
        missed = incomplete or self.minimum > c['target_angle']
        speed = 'FAST' if self.duration < c['min_seconds'] else 'SLOW' if self.duration > c['max_seconds'] else ''
        self.result = ('RANGE_' + speed if speed else 'RANGE') if missed else speed or 'OK'
        self.counts[self.mode]['attempts'] += 1
        self.counts[self.mode]['passed'] += self.result == 'OK'
        self.event_id += 1
        self.started = None
        self.pending = None
        self.return_peak = None
        self.minimum = 180
        self.armed = not incomplete
        self.status = 'START' if self.armed else 'READY'

    def update(self, angle, now):
        if angle is None or not math.isfinite(angle) or not 0 <= angle <= 180:
            self.cancel('LOST')
            return self.snapshot()
        if self.last is not None and (now - self.last > 1.5 or now < self.last):
            self.cancel()
        dt = now - self.last if self.last is not None else 1
        self.last = now
        alpha = 1 - math.exp(-max(0, dt) / 0.06)
        self.smooth = angle if self.smooth is None else self.smooth + alpha * (angle - self.smooth)
        c = self.config[self.mode]
        a = self.smooth
        if not self.armed:
            self.status = 'READY'
            if self.stable('start' if a >= c['start_angle'] else None, now):
                self.armed = True
                self.status = 'START'
                self.pending = None
            return self.snapshot()
        if self.started is None:
            self.status = 'START'
            if self.stable('depart' if a <= c['start_angle'] - 15 else None, now):
                self.started = self.since  # Exclude confirmation delay.
                self.minimum = a
                self.return_peak = None
                self.pending = None
                self.status = 'MOVING'
            return self.snapshot()
        self.status = 'MOVING'
        self.minimum = min(self.minimum, a)
        if a >= self.minimum + 25:
            self.return_peak = max(self.return_peak or a, a)
        # A new curl before reaching extension closes an incomplete attempt.
        partial = self.mode == 'CURL' and self.return_peak is not None and a <= self.return_peak - 15
        label = 'end' if a >= c['start_angle'] else 'partial' if partial else None
        if self.stable(label, now):
            self.finish(self.since, incomplete=label == 'partial')
        return self.snapshot()

    def snapshot(self):
        return dict(mode=self.mode, **self.counts[self.mode], status=self.status,
                    angle=None if self.smooth is None else round(self.smooth),
                    event_id=self.event_id, result=self.result, duration=self.duration)
