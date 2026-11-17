"""Single-person, side-view squat counter. Run with --help for options."""
import argparse
import math
import time


def knee_angle(hip, knee, ankle):
    u = (hip[0] - knee[0], hip[1] - knee[1])
    v = (ankle[0] - knee[0], ankle[1] - knee[1])
    length = math.hypot(*u) * math.hypot(*v)
    if length < 1e-6:
        return None
    return math.degrees(math.acos(max(-1, min(1, (u[0]*v[0] + u[1]*v[1])/length))))


class Counter:
    def __init__(self, down=100, up=160, hold=0.15):
        self.down, self.up, self.hold = down, up, hold
        self.reps = 0
        self.reset_motion()

    def reset_motion(self):
        self.phase = 'Stand to begin'
        self.smooth = None
        self.pending = None
        self.since = None
        self.last = None

    def update(self, angle, now):
        # Missing joints invalidate the unfinished cycle, but preserve the count.
        if angle is None:
            self.reset_motion()
            return
        dt = now - self.last if self.last is not None else 1
        self.last = now
        alpha = 1 - math.exp(-max(0, dt) / 0.08)
        self.smooth = angle if self.smooth is None else self.smooth + alpha*(angle-self.smooth)
        target = 'Standing' if self.smooth >= self.up else 'Squatting' if self.smooth <= self.down else None
        if target != self.pending:
            self.pending, self.since = target, now
        if target is None or now - self.since < self.hold:
            return
        if target == 'Standing':
            if self.phase == 'Squatting':
                self.reps += 1
            self.phase = 'Standing'
        elif self.phase == 'Standing':
            self.phase = 'Squatting'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='0', help='Webcam number or video filename')
    parser.add_argument('--model', default='yolo26n-pose.pt')
    parser.add_argument('--side', choices=['left', 'right'], default='left', help='Body side facing camera')
    parser.add_argument('--down', type=float, default=100, help='Bent knee threshold in degrees')
    parser.add_argument('--up', type=float, default=160, help='Standing knee threshold in degrees')
    parser.add_argument('--confidence', type=float, default=0.5)
    parser.add_argument('--save', help='Optional annotated output .mp4')
    parser.add_argument('--port', help='Optional Arduino USB port, for example COM3')
    args = parser.parse_args()
    if not 0 < args.down < args.up < 180:
        parser.error('Use 0 < down < up < 180')
    if not 0 < args.confidence <= 1:
        parser.error('Confidence must be between 0 and 1')

    import cv2
    from ultralytics import YOLO

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit('Cannot open camera/video. Check --source and camera permissions.')
    writer = None
    link = None
    counter = Counter(args.down, args.up)
    indices = (11, 13, 15) if args.side == 'left' else (12, 14, 16)
    frame_number = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if math.isfinite(fps) and fps > 0 else 30
    try:
        model = YOLO(args.model)
        if args.port:
            from arduino_link import ArduinoLink
            link = ArduinoLink(args.port)
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            now = time.monotonic() if isinstance(source, int) else frame_number / fps
            result = model.predict(frame, verbose=False, conf=0.5)[0]
            angle = None
            message = 'Keep one person in frame, with hip, knee and ankle visible'
            if result.keypoints is not None and len(result.keypoints) == 1:
                points = result.keypoints.data[0].cpu().tolist()
                joints = [points[i] for i in indices]
                if all(len(p) >= 3 and p[2] >= args.confidence for p in joints):
                    angle = knee_angle(*joints)
                    message = 'Stand -> squat -> stand | Q: quit | R: reset'
                    for a, b in zip(joints, joints[1:]):
                        cv2.line(frame, tuple(map(int, a[:2])), tuple(map(int, b[:2])), (0, 255, 255), 4)
                    for point in joints:
                        cv2.circle(frame, tuple(map(int, point[:2])), 7, (0, 255, 0), -1)
            counter.update(angle, now)
            if link is not None:
                link.update(counter.reps, counter.phase, counter.smooth)
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 110), (25, 25, 25), -1)
            label = f'Reps: {counter.reps} | {counter.phase}'
            if counter.smooth is not None:
                label += f' | Knee: {counter.smooth:.0f} deg'
            cv2.putText(frame, label, (12, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            cv2.putText(frame, message, (12, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            if args.save:
                if writer is None:
                    writer = cv2.VideoWriter(args.save, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame.shape[1], frame.shape[0]))
                    if not writer.isOpened():
                        raise RuntimeError('Cannot create output video. Check output folder and filename.')
                writer.write(frame)
            cv2.imshow('Squat counter', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord('r'):
                counter = Counter(args.down, args.up)
    finally:
        if link is not None:
            link.close()
        cap.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()
    print(f'Completed squats: {counter.reps}')


if __name__ == '__main__':
    main()
