"""Knowledge Promotion Engine - the sole path to modify enterprise knowledge (SECTION 34/79/103)."""

from ecms.promotion.interfaces.engine import PromotionEngine
from ecms.promotion.services.engine import DefaultPromotionEngine

__all__ = ["DefaultPromotionEngine", "PromotionEngine"]
