import unittest
import time
from unittest.mock import Mock
import serial
from exercise_logic import ExerciseTracker
from exercise_link import ExerciseLink,packet


class LinkTests(unittest.TestCase):
    def link(self):
        link=ExerciseLink.__new__(ExerciseLink)
        link.serial=Mock();link.serial.in_waiting=0
        link.error=None;link.buffer=b'';link.last=0;link.previous=None;link.mode=None;link.mode_revision=None;link.mode_changed=False
        link.opened=time.monotonic()
        return link

    def test_packet(self):
        self.assertEqual(packet(ExerciseTracker().snapshot()),b'EX,SQUAT,0,0,READY,-1,0,NONE,-1\n')

    def test_fragmented_mode_and_noise(self):
        link=self.link();link.serial.in_waiting=8;link.serial.read.return_value=b'MODE,CU'
        self.assertIsNone(link.poll_mode())
        link.serial.read.return_value=b'RL\nnoise\nMODE,SQUAT\n'
        self.assertEqual(link.poll_mode(),'SQUAT')

    def test_usb_timeout_isolated(self):
        link=self.link();link.serial.write.side_effect=serial.SerialTimeoutException('Write timeout')
        link.update(ExerciseTracker().snapshot())
        self.assertIsNotNone(link.error)
        link.update(ExerciseTracker().snapshot());link.serial.write.assert_called_once()

    def test_double_touch_still_reports_change(self):
        link=self.link();link.mode='SQUAT';link.mode_revision=0
        link.serial.in_waiting=40;link.serial.read.return_value=b'MODE,CURL,1\nMODE,SQUAT,2\n'
        self.assertEqual(link.poll_mode(),'SQUAT');self.assertTrue(link.mode_changed)
        link.serial.read.return_value=b'MODE,SQUAT,2\n'
        link.poll_mode();self.assertFalse(link.mode_changed)

    def test_read_failure_isolated(self):
        link=self.link();link.serial.in_waiting=1;link.serial.read.side_effect=serial.SerialException('Disconnected')
        self.assertIsNone(link.poll_mode());self.assertIsNotNone(link.error)

    def test_old_firmware_detected(self):
        link=self.link();link.opened-=6;link.poll_mode()
        self.assertIn('exercise_oled.ino',link.error)

    def test_repeated_snapshot_throttled(self):
        link=self.link();link.serial.write.side_effect=lambda data:len(data)
        s=ExerciseTracker().snapshot();link.update(s);link.update(s)
        link.serial.write.assert_called_once()
        s['event_id']=1;link.update(s)
        self.assertEqual(link.serial.write.call_count,2)
