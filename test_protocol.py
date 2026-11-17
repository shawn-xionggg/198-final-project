import unittest
from arduino_link import packet

class ProtocolTests(unittest.TestCase):
    def test_standing(self):
        self.assertEqual(packet(2, 'Standing', 171.7), b'STATE,2,STAND,172\n')

    def test_lost_overrides_phase(self):
        self.assertEqual(packet(2, 'Squatting', None), b'STATE,2,LOST,-1\n')

    def test_initial(self):
        self.assertEqual(packet(0, 'Stand to begin', 125), b'STATE,0,READY,125\n')
