from dataclasses import dataclass

from app.models.plan import Plan
from app.models.subscription import Subscription


@dataclass
class PurchaseResult:

    success: bool
    message: str
    plan: Plan | None = None
    subscription: Subscription | None = None