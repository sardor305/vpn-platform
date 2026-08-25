from dataclasses import dataclass

from app.models.daily_subscription import DailySubscription
from app.models.plan import Plan
from app.models.subscription import Subscription


@dataclass
class PurchaseResult:

    success: bool
    message: str

    plan: Plan | None = None
    subscription: Subscription | None = None

    daily_subscription: DailySubscription | None = None

    vpn_link: str | None = None
    subscription_url: str | None = None