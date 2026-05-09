import unittest
import pandas as pd
import numpy as np
import io
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_loader import get_column_summary, validate_bounds

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.dummy_data = pd.DataFrame({
            "Timestamp": pd.date_range("2024-01-01", periods=5, freq="15T"),
            "Site_ID": ["SiteA"] * 5,
            "Inverter_ID": ["Inv1"] * 5,
            "MPPT_ID": ["1"] * 5,
            "DC_Voltage_V": [500, 600, 1600, 400, np.nan],  # 1600 is out of bounds
            "DC_Current_A": [10, 20, -5, 15, 10],           # -5 is out of bounds
            "DC_Power_kW": [5, 12, -1, 6, 5]               # -1 is out of bounds
        })

    def test_get_column_summary(self):
        summary = get_column_summary(self.dummy_data)
        self.assertEqual(len(summary), 3) # 3 numeric cols
        self.assertTrue("Missing" in summary.columns)

    def test_validate_bounds(self):
        warnings = validate_bounds(self.dummy_data)
        self.assertEqual(len(warnings), 3)
        self.assertTrue(any("DC_Voltage_V" in w for w in warnings))
        self.assertTrue(any("DC_Current_A" in w for w in warnings))
        self.assertTrue(any("DC_Power_kW" in w for w in warnings))

if __name__ == '__main__':
    unittest.main()
