
import requests

from django.conf import settings


class PayMongoError(Exception):
    pass


def get_secret_key():
    key = settings.PAYMONGO_SECRET_KEY.strip()

    if not key.startswith("sk_test_"):
        raise PayMongoError(
            "A valid PayMongo test secret key is required."
        )

    return key


def api_request(method, endpoint, payload=None):
    key = get_secret_key()

    try:
        response = requests.request(
            method=method,
            url=f"{settings.PAYMONGO_API_URL}{endpoint}",
            auth=(key, ""),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        raise PayMongoError(
            "Unable to communicate with PayMongo. "
            "Please check your configuration and try again."
        ) from exc


def create_checkout_session(
    amount_centavos,
    donation_id,
    success_url,
    cancel_url,
):
    payload = {
        "data": {
            "attributes": {
                "billing": {
                    "name": "SkyAware PH Test Donor",
                    "email": "test@example.com",
                },
                "send_email_receipt": False,
                "show_description": True,
                "show_line_items": True,
                "description": (
                    "SkyAware PH simulated disaster "
                    "relief donation"
                ),
                "line_items": [
                    {
                        "currency": "PHP",
                        "amount": amount_centavos,
                        "name": (
                            f"Test Donation #{donation_id}"
                        ),
                        "quantity": 1,
                    }
                ],
                "payment_method_types": [
                    "card",
                    "gcash",
                    "paymaya",
                ],
                "success_url": success_url,
                "cancel_url": cancel_url,
            }
        }
    }

    result = api_request(
        "POST",
        "/checkout_sessions",
        payload,
    )

    data = result.get("data") or {}
    attributes = data.get("attributes") or {}

    session_id = data.get("id")
    checkout_url = attributes.get("checkout_url")

    if not session_id or not checkout_url:
        raise PayMongoError(
            "PayMongo did not return a valid checkout session."
        )

    return session_id, checkout_url


def retrieve_checkout_session(session_id):
    if not session_id or not session_id.startswith("cs_"):
        raise PayMongoError("Invalid checkout session ID.")

    result = api_request(
        "GET",
        f"/checkout_sessions/{session_id}",
    )

    return result.get("data") or {}


def checkout_is_paid(checkout_data, expected_amount):
    attributes = checkout_data.get("attributes") or {}
    payments = attributes.get("payments") or []

    # Only trust a confirmed PayMongo payment.
    # Do not use the browser's success URL as proof.
    for payment in payments:
        payment_attributes = payment.get("attributes") or {}

        if (
            payment_attributes.get("status") == "paid"
            and payment_attributes.get("currency") == "PHP"
            and payment_attributes.get("amount") == expected_amount
        ):
            return True

    return False
