"""
Telegram Stars payment integration.
Users pay with Stars (built-in Telegram currency) to unlock Premium.
No bank account needed. Works from Russia.
"""
from aiogram.types import (
    LabeledPrice, Message, PreCheckoutQuery, SuccessfulPayment
)
from aiogram.filters import Command
import database as db
from datetime import date, timedelta

# Telegram Stars prices (1 Star ≈ $0.013)
PREMIUM_1_MONTH_STARS = 150   # ≈ $2
PREMIUM_3_MONTH_STARS = 350   # ≈ $4.5

PAYMENT_DESCRIPTIONS = {
    150: "1 месяц Premium — безлимитные сообщения",
    350: "3 месяца Premium — безлимитные сообщения",
}


async def send_premium_invoice(message: Message, stars: int):
    """Send a Stars payment invoice."""
    await message.answer_invoice(
        title="Premium подписка",
        description=PAYMENT_DESCRIPTIONS.get(stars, f"{stars} Stars"),
        payload=f"premium_{stars}_{message.from_user.id}",
        currency="XTR",  # XTR = Telegram Stars
        prices=[LabeledPrice(label="Premium", amount=stars)],
    )


async def process_pre_checkout(query: PreCheckoutQuery):
    """Always approve pre-checkout."""
    await query.answer(ok=True)


async def process_successful_payment(message: Message):
    """Grant premium after successful payment."""
    payment: SuccessfulPayment = message.successful_payment
    payload = payment.invoice_payload  # e.g. "premium_150_12345678"

    parts = payload.split("_")
    stars = int(parts[1]) if len(parts) > 1 else 150

    # Determine subscription length
    months = 1 if stars <= 150 else 3
    until = (date.today() + timedelta(days=30 * months)).isoformat()

    user_id = message.from_user.id
    db.set_premium(user_id, until)

    await message.answer(
        f"✅ *Оплата получена! {payment.total_amount} ⭐*\n\n"
        f"Premium активирован до *{until}*\n"
        f"Безлимитные сообщения включены!",
        parse_mode="Markdown"
    )
