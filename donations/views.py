
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from integrations.paymongo import (
    PayMongoError,
    checkout_is_paid,
    create_checkout_session,
    retrieve_checkout_session,
)

from .models import Donation


# ==========================================
# PAYMONGO TEST CONFIGURATION
# ==========================================

def is_paymongo_configured():
    key = getattr(settings, "PAYMONGO_SECRET_KEY", "")
    test_mode = getattr(settings, "PAYMONGO_TEST_MODE", False)

    return (
        test_mode is True
        and isinstance(key, str)
        and key.startswith("sk_test_")
        and len(key) > len("sk_test_")
    )


# ==========================================
# VERIFY TEST DONATION
# ==========================================

def verify_donation(donation):
    if (
        donation.status == Donation.Status.PAID
        or not donation.checkout_session_id
    ):
        return donation

    checkout = retrieve_checkout_session(
        donation.checkout_session_id
    )

    if checkout.get("id") != donation.checkout_session_id:
        raise PayMongoError(
            "Checkout session verification failed."
        )

    expected_amount = int(donation.amount * 100)

    if checkout_is_paid(checkout, expected_amount):
        with transaction.atomic():
            locked = Donation.objects.select_for_update().get(
                pk=donation.pk
            )

            if locked.status != Donation.Status.PAID:
                locked.status = Donation.Status.PAID
                locked.paid_at = timezone.now()
                locked.save(
                    update_fields=["status", "paid_at"]
                )

    donation.refresh_from_db()
    return donation


# ==========================================
# DONATION PAGE
# ==========================================

@login_required
def donate(request):
    return render(
        request,
        "donations/donate.html",
        {
            "paymongo_configured": is_paymongo_configured()
        }
    )


# ==========================================
# CREATE TEST DONATION
# ==========================================

@login_required
@require_POST
def create_donation(request):

    if not is_paymongo_configured():
        messages.warning(
            request,
            "PayMongo test checkout is not configured yet. "
            "No payment was attempted."
        )
        return redirect("donate")

    raw_amount = request.POST.get("amount", "").strip()

    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, ValueError):
        messages.error(
            request,
            "Please enter a valid donation amount."
        )
        return redirect("donate")

    if (
        not amount.is_finite()
        or amount < Decimal("20.00")
        or amount > Decimal("10000.00")
        or amount != amount.quantize(Decimal("0.01"))
    ):
        messages.error(
            request,
            "Enter an amount between PHP 20 and PHP 10,000 "
            "with no more than two decimal places."
        )
        return redirect("donate")

    donation = Donation.objects.create(
        user=request.user,
        amount=amount
    )

    result_url = request.build_absolute_uri(
        reverse(
            "donation_result",
            kwargs={"pk": donation.pk}
        )
    )

    try:
        session_id, checkout_url = create_checkout_session(
            amount_centavos=int(amount * 100),
            donation_id=donation.pk,
            success_url=result_url,
            cancel_url=result_url,
        )

        donation.checkout_session_id = session_id
        donation.save(
            update_fields=["checkout_session_id"]
        )

    except PayMongoError:
        donation.status = Donation.Status.FAILED
        donation.save(update_fields=["status"])

        messages.error(
            request,
            "Unable to start the PayMongo test checkout. "
            "Please try again later."
        )
        return redirect("donate")

    return redirect(checkout_url)


# ==========================================
# DONATION RESULT
# ==========================================

@login_required
def donation_result(request, pk):

    donation = get_object_or_404(
        Donation,
        pk=pk,
        user=request.user
    )

    if not is_paymongo_configured():
        messages.warning(
            request,
            "Payment verification is currently unavailable."
        )
        return redirect("donation_history")

    try:
        donation = verify_donation(donation)

    except PayMongoError:
        messages.warning(
            request,
            "Payment verification is temporarily unavailable."
        )
        return redirect("donation_history")

    if donation.status == Donation.Status.PAID:
        messages.success(
            request,
            "Your simulated donation was confirmed!"
        )
    else:
        messages.info(
            request,
            "Payment has not been confirmed yet."
        )

    return redirect("donation_history")


# ==========================================
# DONATION HISTORY
# ==========================================

@login_required
def donation_history(request):

    donations = list(
        Donation.objects.filter(user=request.user)
    )

    if is_paymongo_configured():
        pending = [
            item for item in donations
            if (
                item.status == Donation.Status.PENDING
                and item.checkout_session_id
            )
        ][:5]

        for donation in pending:
            try:
                verify_donation(donation)
            except PayMongoError:
                pass

    donations = Donation.objects.filter(
        user=request.user
    )

    return render(
        request,
        "donations/history.html",
        {
            "donations": donations,
            "paymongo_configured": is_paymongo_configured(),
        }
    )
