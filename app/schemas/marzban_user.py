from dataclasses import dataclass


@dataclass
class MarzbanUser:

    username: str
    vpn_link: str
    subscription_url: str