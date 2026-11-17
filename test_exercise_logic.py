import copy
import unittest
from exercise_logic import ExerciseTracker, DEFAULTS


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.c=ExerciseTracker()
        self.t=0.0

    def hold(self,angle,seconds):
        for _ in range(round(seconds/.05)):
            self.c.update(angle,self.t)
            self.t+=.05

    def ramp(self,start,end,seconds):
        n=round(seconds/.05)
        for i in range(1,n+1):
            self.hold(start+(end-start)*i/n,.05)

    def cycle(self,bottom=85,half=1.5,pause=.3):
        self.hold(175,.4)
        self.ramp(175,bottom,half)
        self.hold(bottom,pause)
        self.ramp(bottom,175,half)
        self.hold(175,.4)

    def test_full_squat(self):
        self.cycle()
        s=self.c.snapshot()
        self.assertEqual((s['attempts'],s['passed'],s['result']),(1,1,'OK'))
        self.assertGreater(s['duration'],2)
        self.assertLess(s['duration'],6)
        self.hold(175,3)
        self.assertEqual(self.c.snapshot()['attempts'],1)

    def test_shallow_counts_attempt_not_pass(self):
        self.cycle(bottom=125,half=2)
        self.assertEqual(self.c.snapshot()['result'],'RANGE')
        self.assertEqual(self.c.snapshot()['attempts'],1)
        self.assertEqual(self.c.snapshot()['passed'],0)

    def test_fast(self):
        self.cycle(half=.3)
        self.assertEqual(self.c.result,'FAST')

    def test_slow_whole_motion(self):
        self.cycle(half=4)
        self.assertEqual(self.c.result,'SLOW')

    def test_bottom_pause_included_but_wait_between_reps_not(self):
        self.hold(175,10)
        self.cycle(pause=5)
        self.assertEqual(self.c.result,'SLOW')
        self.cycle()
        self.assertEqual(self.c.result,'OK')
        self.assertEqual(self.c.snapshot()['attempts'],2)

    def test_start_crouched(self):
        self.hold(80,1);self.ramp(80,175,2);self.hold(175,1)
        self.assertEqual(self.c.event_id,0)

    def test_tracking_loss_cancels(self):
        self.hold(175,.5);self.ramp(175,80,1.5)
        self.hold(None,.1);self.ramp(80,175,1.5);self.hold(175,.5)
        self.assertEqual(self.c.event_id,0)

    def test_long_gap_cancels(self):
        self.hold(175,.5);self.ramp(175,80,1.5)
        self.t+=2
        self.ramp(80,175,1.5);self.hold(175,.5)
        self.assertEqual(self.c.event_id,0)

    def test_small_movements_and_single_frame_noise(self):
        self.hold(175,1);self.hold(50,.05);self.hold(175,1)
        self.ramp(175,150,1);self.ramp(150,175,1);self.hold(175,.5)
        self.assertEqual(self.c.event_id,0)

    def test_curl_and_mode_counts(self):
        self.cycle();self.c.toggle_mode();self.cycle(bottom=40)
        self.assertEqual(self.c.snapshot()['passed'],1)
        self.assertEqual(self.c.event_id,2)
        self.c.toggle_mode()
        self.assertEqual(self.c.snapshot()['attempts'],1)

    def test_switch_cancels_partial(self):
        self.hold(175,.5);self.ramp(175,80,1.5)
        self.c.toggle_mode();self.ramp(80,175,1.5);self.hold(175,.5)
        self.assertEqual(self.c.event_id,0)

    def test_partial_curl_extension_then_new_curl_flags_once(self):
        self.c.set_mode('CURL');self.hold(175,.5)
        self.ramp(175,40,1.5);self.hold(40,.3)
        self.ramp(40,110,1);self.hold(110,.3)
        self.ramp(110,40,1);self.hold(40,.5)
        self.assertEqual(self.c.result,'RANGE')
        self.assertEqual(self.c.snapshot()['attempts'],1)
        self.ramp(40,110,1);self.ramp(110,40,1)
        self.assertEqual(self.c.snapshot()['attempts'],1)

    def test_reset_does_not_reuse_event_id(self):
        self.cycle();event=self.c.event_id;self.c.reset()
        self.assertEqual(self.c.event_id,event)
        self.assertEqual(self.c.snapshot()['attempts'],0)
        self.cycle();self.assertEqual(self.c.event_id,event+1)

    def test_config_validation(self):
        for invalid in [None,[],{'SQUAT':[]}]:
            if invalid is None: continue
            with self.assertRaises(ValueError):ExerciseTracker(invalid)
        config=copy.deepcopy(DEFAULTS);config['CURL']['min_seconds']=float('nan')
        with self.assertRaises(ValueError):ExerciseTracker(config)


if __name__=='__main__':unittest.main()
