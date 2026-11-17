import unittest
from unittest.mock import Mock
import serial
from arduino_link import ArduinoLink


class USBFailureTests(unittest.TestCase):
    def link(self):
        link=ArduinoLink.__new__(ArduinoLink)
        link.serial=Mock()
        link.last=0
        link.previous=None
        link.error=None
        return link

    def test_timeout_disables_usb_without_stopping_counter(self):
        link=self.link()
        link.serial.write.side_effect=serial.SerialTimeoutException('Write timeout')
        link.update(1,'Standing',170)
        self.assertIn('Write timeout',link.error)
        link.serial.close.assert_called_once()
        link.update(2,'Standing',170)
        link.serial.write.assert_called_once()

    def test_partial_write_is_failure(self):
        link=self.link()
        link.serial.write.return_value=2
        link.update(1,'Standing',170)
        self.assertIn('Incomplete',link.error)

    def test_success_preserves_connection(self):
        link=self.link()
        link.serial.write.side_effect=lambda data:len(data)
        link.update(3,'Standing',170)
        self.assertIsNone(link.error)
        self.assertEqual(link.previous,3)
        link.serial.close.assert_not_called()
