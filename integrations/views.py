
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
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


def verify_donation(donation):
    if donation.status == Donation.Status.PAID:
        return donation

    if not donation.checkout_session_id:
        return donation

    checkout = retrieve_checkout_session(
        donation.checkout_session_id
    )

    expected_amount = int(
        donation.amount * Decimal("100")
    )

    if checkout_is_paid(checkout, expected_amount):
        with transaction.atomic():
            locked = (
                Donation.objects
                .select_for_update()
                .get(pk=donation.pk)
            )

            if locked.status != Donation.Status.PAID:
                locked.status = Donation.Status.PAID
                locked.paid_at = timezone.now()

                locked.save(
                    update_fields=[
                        "status",
                        "paid_at",
                    ]
                )

    donation.refresh_from_db()
    return donation


@login_required
def donate(request):
    return render(
        request,
        "donations/donate.html",
    )


@login_required
@require_POST
def create_donation(request):
    raw_amount = request.POST.get(
        "amount", ""
    ).strip()

    try:
        amount = Decimal(raw_amount)

        valid_amount = (
            amount.is_finite()
            and Decimal("20.00")
            <= amount
            <= Decimal("10000.00")
            and amount == amount.quantize(
                Decimal("0.01")
            )
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        valid_amount = False

    if not valid_amount:
        messages.error(
            request,
            "Enter an amount between PHP 20 "
            "and PHP 10,000 with up to "
            "two decimal places."
        )
        return redirect("donate")

    donation = Donation.objects.create(
        user=request.user,
        amount=amount,
        status=Donation.Status.PENDING,
    )

    result_url = request.build_absolute_uri(
        reverse(
            "donation_result",
            kwargs={"pk": donation.pk},
        )
    )

    try:
        session_id, checkout_url = (
            create_checkout_session(
                amount_centavos=int(
                    amount * Decimal("100")
                ),
                donation_id=donation.pk,
                success_url=result_url,
                cancel_url=result_url,
            )
        )

        donation.checkout_session_id = session_id
        donation.save(
            update_fields=[
                "checkout_session_id",
            ]
        )

    except PayMongoError as exc:
        donation.status = Donation.Status.FAILED
        donation.save(
            update_fields=["status"]
        )

        messages.error(
            request,
            str(exc),
        )
        return redirect("donate")

    return redirect(checkout_url)


@login_required
def donation_result(request, pk):
    donation = get_object_or_404(
        Donation,
        pk=pk,
        user=request.user,
    )

    try:
        donation = verify_donation(donation)

    except PayMongoError:
        messages.warning(
            request,
            "Payment verification is temporarily "
            "unavailable. Please check your "
            "Donation History again."
        )
        return redirect("donation_history")

    if donation.status == Donation.Status.PAID:
        messages.success(
            request,
            "Your simulated donation "
            "has been confirmed!"
        )

    elif donation.status == Donation.Status.PENDING:
        messages.info(
            request,
            "Your test payment is not confirmed yet. "
            "Please check Donation History "
            "to refresh its status."
        )

    else:
        messages.warning(
            request,
            "This donation has not been confirmed "
            "as paid."
        )

    return redirect("donation_history")


@login_required
def donation_history(request):
    donations = list(
        Donation.objects.filter(
            user=request.user
        )
    )

    pending = [
        item
        for item in donations
        if (
            item.status == Donation.Status.PENDING
            and item.checkout_session_id
        )
    ][:5]

    for donation in pending:
        try:
            verify_donation(donation)
        except PayMongoError:
            continue

    donations = Donation.objects.filter(
        user=request.user
    )

    return render(
        request,
        "donations/history.html",
        {
            "donations": donations,
        },
    )
