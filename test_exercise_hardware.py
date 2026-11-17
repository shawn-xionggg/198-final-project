"""Simulated exercise results to verify LED/buzzer/OLED, no camera required."""
import argparse
import time
from exercise_link import ExerciseLink


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    args=parser.parse_args()
    link=ExerciseLink(args.port)
    print('SIMULATED reps: one passing LED flash, then one range-warning buzz. Do not exercise.')
    try:
        limit=time.monotonic()+6
        mode=None
        while not mode and not link.error and time.monotonic()<limit:
            mode=link.poll_mode();time.sleep(.05)
        if not mode or link.error:
            raise SystemExit(link.error or 'No mode message: upload exercise_oled.ino first.')
        s=dict(mode=mode,attempts=0,passed=0,status='START',angle=175,event_id=0,result='NONE',duration=None)
        for event,result,passed in [(0,'NONE',0),(1,'OK',1),(2,'RANGE',1)]:
            s.update(attempts=event,event_id=event,result=result,passed=passed,duration=None if event==0 else 3.0)
            print(f'{mode}: {result}')
            until=time.monotonic()+2
            while time.monotonic()<until:
                latest=link.poll_mode()
                if latest!=mode:
                    raise SystemExit('Mode changed during test. Restart the test with your selected exercise.')
                link.update(s)
                if link.error:raise SystemExit(link.error)
                time.sleep(.05)
    finally:link.close()
    print('Test done. Start the phone receiver to reset the simulated counts.')


if __name__=='__main__':main()
