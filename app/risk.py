from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskState:
    score: int = 0
    cooldown: int = 0


class RiskEngine:
    """Simple temporal risk engine for suspicious concealment-like gestures."""

    def __init__(self, alert_threshold: int = 8, decay: int = 1) -> None:
        self.state = RiskState()
        self.alert_threshold = alert_threshold
        self.decay = decay

    def update(self, hand_near_hip: bool, hand_above_shoulder: bool) -> tuple[int, bool, str]:
        """
        Return (score, alert, reason).

        Heuristic:
        - near hip contributes +3 (concealment proxy)
        - hand above shoulder contributes +1 (normal browsing movement)
        - no activity decays score
        - cooldown suppresses repeated alerts
        """
        reason = "normal"

        if hand_near_hip:
            self.state.score += 3
            reason = "hand_near_hip"
        elif hand_above_shoulder:
            self.state.score += 1
            reason = "reaching"
        else:
            self.state.score = max(0, self.state.score - self.decay)

        alert = False
        if self.state.cooldown > 0:
            self.state.cooldown -= 1
        elif self.state.score >= self.alert_threshold:
            alert = True
            reason = "suspicious_concealment_pattern"
            self.state.cooldown = 30
            self.state.score = max(0, self.state.score - 4)

        return self.state.score, alert, reason
