"""Adapter port for a production digital resident.

NR-M1-bot does not construct this object. The local bot policy does not call
it. `controller=local_bot` stays a separate field from `digital_resident`.

A future resident would choose whether to join, pick a legal faction, and
decide from the same perceived targets and teammate signals a human gets.
These methods stay unimplemented so nothing behind the port can play a match.
"""

from __future__ import annotations


class DigitalResidentPort:
    """Empty port. No faction choice, no pass, no score."""

    def select_match(self, perceived: dict) -> None:
        """A resident would choose whether to join and which legal faction to take."""
        del perceived
        raise NotImplementedError("digital_resident port is not connected")

    def decide(self, perceived: dict) -> None:
        """A resident would return an intent. This card does not."""
        del perceived
        raise NotImplementedError("digital_resident port is not connected")
