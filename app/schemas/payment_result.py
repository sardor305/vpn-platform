from dataclasses import dataclass


@dataclass
class PaymentResult:

    success: bool
    message: str