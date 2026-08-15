from dataclasses import dataclass


@dataclass
class StatisticsResult:
    total_users: int
    active_users: int
    inactive_users: int
    users_today: int
    users_this_month: int

    total_subscriptions: int
    active_subscriptions: int
    expired_subscriptions: int

    total_vpn_accounts: int
    active_vpn_accounts: int
    protocol_counts: dict[str, int]

    total_tickets: int
    new_tickets: int
    open_tickets: int
    closed_tickets: int