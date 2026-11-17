import unittest
from squat_counter import Counter, knee_angle


class CounterTests(unittest.TestCase):
    def feed(self, counter, values):
        for value in values:
            counter.update(value, self.t)
            self.t += 0.05

    def setUp(self):
        self.t = 0

    def test_full_cycles_and_bottom_pause(self):
        c = Counter()
        self.feed(c, [175]*20 + [85]*40 + [175]*20)
        self.assertEqual(c.reps, 1)
        self.feed(c, [85]*20 + [175]*20)
        self.assertEqual(c.reps, 2)

    def test_start_crouched_and_partial(self):
        c = Counter()
        self.feed(c, [85]*20 + [175]*20 + [125]*20 + [175]*20)
        self.assertEqual(c.reps, 0)

    def test_tracking_gap_cancels_rep(self):
        c = Counter()
        self.feed(c, [175]*20 + [85]*20 + [None] + [175]*20)
        self.assertEqual(c.reps, 0)

    def test_single_frame_noise(self):
        c = Counter()
        self.feed(c, [175]*20 + [80] + [175]*20)
        self.assertEqual(c.reps, 0)

    def test_angles(self):
        self.assertAlmostEqual(knee_angle((0, 0), (0, 1), (0, 2)), 180)
        self.assertAlmostEqual(knee_angle((0, 0), (0, 1), (1, 1)), 90)
        self.assertIsNone(knee_angle((0, 0), (0, 0), (1, 1)))


if __name__ == '__main__':
    unittest.main()
