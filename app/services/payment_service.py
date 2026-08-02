from app.schemas.payment_result import PaymentResult

class PaymentService:

    async def create_test_payment(
        self,
    ) -> PaymentResult:

        return PaymentResult(
            success=True,
            message="Test to'lov muvaffaqiyatli bajarildi.",
        )