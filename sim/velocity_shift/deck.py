from __future__ import annotations
"""Deck construction, draw, and discard lifecycle.

Cards are weighted by combatant stats (POW, EN, HAN -> Stance.POW / EN / HAN cards)
with a smoothing term to ensure every deck has at least some of each stance.
"""

from random import Random

from .models import Stance, Card


class Deck:
    """A 72-card draw-discard pile built proportionally from combatant stats.

    When *reshuffle_on_end* is True, all cards go back into the draw pile
    after each turn (used by AI opponents to guarantee pattern-consistent hands).
    """
    DECK_SIZE = 192

    def __init__(self, draw_pile: list[Card], rng: Random,
                 reshuffle_on_end: bool = False) -> None:
        self._draw: list[Card] = draw_pile
        self._discard: list[Card] = []
        self._rng = rng
        self.reshuffle_on_end = reshuffle_on_end

    @classmethod
    def _deck_weights(
        cls,
        pow_stat: float,
        en_stat: float,
        han_stat: float,
    ) -> tuple[float, float, float]:
        total = pow_stat + en_stat + han_stat
        if total == 0:
            return (1/3, 1/3, 1/3)
        alpha = 0.85
        beta = 1.0 - alpha
        wp = alpha * pow_stat / total + beta / 3.0
        wd = alpha * en_stat / total + beta / 3.0
        wn = alpha * han_stat / total + beta / 3.0
        tw = wp + wd + wn
        return (wp / tw, wd / tw, wn / tw)

    @classmethod
    def build(
        cls,
        pow_stat: float,
        en_stat: float,
        han_stat: float,
        rng: Random,
        reshuffle_on_end: bool = False,
    ) -> Deck:
        """Build and shuffle a full 72-card deck from stat proportions."""
        wp, wd, wn = cls._deck_weights(pow_stat, en_stat, han_stat)
        a = round(cls.DECK_SIZE * wp)
        d = round(cls.DECK_SIZE * wd)
        n = cls.DECK_SIZE - a - d
        raw: list[Card] = [Card(Stance.POW) for _ in range(a)]
        raw += [Card(Stance.EN) for _ in range(d)]
        raw += [Card(Stance.HAN) for _ in range(n)]
        rng.shuffle(raw)
        return cls(raw, rng, reshuffle_on_end)

    def draw(self, n: int = 6) -> list[Card]:
        """Draw up to *n* cards from the draw pile (no reshuffling)."""
        available = min(n, len(self._draw))
        hand = self._draw[:available]
        self._draw = self._draw[available:]
        return hand

    def prepare_turn_hand(
        self,
        requirements: dict | None = None,
        max_retries: int = 10,
    ) -> list[Card]:
        """Draw 6 cards, redrawing if *requirements* are not met.

        Cards are returned to the draw pile and reshuffled on each retry.
        This guarantees AI opponents can always produce pattern-consistent hands.
        """
        hand = self.draw(6)
        if not requirements:
            return hand
        retries = 0
        while not self._hand_satisfies(hand, requirements) and retries < max_retries:
            self._draw.extend(hand)
            self._rng.shuffle(self._draw)
            hand = self.draw(6)
            retries += 1
        return hand

    @staticmethod
    def _hand_satisfies(hand: list[Card], requirements: dict) -> bool:
        for stance, min_count in requirements.items():
            count = sum(1 for c in hand if c == stance)
            if count < min_count:
                return False
        return True

    def end_turn(self, played: list[Card], unpicked: list[Card]) -> None:
        """Return played and unpicked cards to the appropriate pile.

        When *reshuffle_on_end* is True, all cards go back into the draw
        pile and are reshuffled (opponent decks).  Otherwise they are
        discarded (player decks).
        """
        if self.reshuffle_on_end:
            self._draw.extend(played)
            self._draw.extend(unpicked)
            self._rng.shuffle(self._draw)
        else:
            self._discard.extend(played)
            self._discard.extend(unpicked)

    @property
    def remaining(self) -> int:
        """Number of cards left in the draw pile."""
        return len(self._draw)

    def __repr__(self) -> str:
        return f"Deck(draw={len(self._draw)}, discard={len(self._discard)})"
