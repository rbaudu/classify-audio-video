"""
Tests unitaires pour le module utils.formatting
"""
import unittest
from server.utils.formatting import format_time

class TestFormatting(unittest.TestCase):
    """Tests pour les fonctions de formatage"""
    
    def test_format_time_seconds_only(self):
        """Test du formatage avec des secondes uniquement"""
        self.assertEqual(format_time(45), "00:45")
        self.assertEqual(format_time(0), "00:00")
        self.assertEqual(format_time(59), "00:59")
    
    def test_format_time_minutes_seconds(self):
        """Test du formatage avec minutes et secondes"""
        self.assertEqual(format_time(60), "01:00")
        self.assertEqual(format_time(61), "01:01")
        self.assertEqual(format_time(125), "02:05")
        self.assertEqual(format_time(3599), "59:59")
    
    def test_format_time_hours_minutes_seconds(self):
        """Test du formatage avec heures, minutes et secondes"""
        self.assertEqual(format_time(3600), "01:00:00")
        self.assertEqual(format_time(3661), "01:01:01")
        self.assertEqual(format_time(7262), "02:01:02")
        self.assertEqual(format_time(86399), "23:59:59")
    
    def test_format_time_large_values(self):
        """Test du formatage avec de grandes valeurs"""
        self.assertEqual(format_time(90000), "25:00:00")
        self.assertEqual(format_time(356400), "99:00:00")
    
    def test_format_time_float_input(self):
        """Test du formatage avec des entrées à virgule flottante"""
        self.assertEqual(format_time(45.2), "00:45")
        self.assertEqual(format_time(60.9), "01:00")
    
    def test_format_time_negative_input(self):
        """Test du formatage avec des entrées négatives"""
        with self.assertRaises(ValueError):
            format_time(-1)
        with self.assertRaises(ValueError):
            format_time(-60)

if __name__ == '__main__':
    unittest.main()
