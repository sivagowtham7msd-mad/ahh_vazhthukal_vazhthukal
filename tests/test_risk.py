import unittest

from app.risk import RiskEngine


class RiskEngineTest(unittest.TestCase):
    def test_alert_after_repeated_hip_events(self):
        engine = RiskEngine(alert_threshold=8)
        alerts = []
        for _ in range(4):
            _, alert, _ = engine.update(hand_near_hip=True, hand_above_shoulder=False)
            alerts.append(alert)
        self.assertIn(True, alerts)


if __name__ == "__main__":
    unittest.main()
