
import requests

from urllib.parse import urlparse
from django.conf import settings


class PayMongoError(Exception):
    pass


def get_secret_key():
    key = getattr(
        settings, "PAYMONGO_SECRET_KEY", ""
    ).strip()

    if not key.startswith("sk_test_"):
        raise PayMongoError(
            "A valid PayMongo test secret key is required."
        )

    return key


def api_request(method, endpoint, payload=None):
    key = get_secret_key()

    base_url = getattr(
        settings,
        "PAYMONGO_API_URL",
        "https://api.paymongo.com/v1",
    ).rstrip("/")

    if not base_url.startswith(
        "https://api.paymongo.com/"
    ):
        raise PayMongoError(
            "Invalid PayMongo API URL configuration."
        )

    try:
        response = requests.request(
            method=method,
            url=f"{base_url}{endpoint}",
            auth=(key, ""),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )

        response.raise_for_status()
        result = response.json()

    except requests.Timeout as exc:
        raise PayMongoError(
            "PayMongo request timed out. "
            "Please try again later."
        ) from exc

    except requests.RequestException as exc:
        raise PayMongoError(
            "Unable to communicate with PayMongo. "
            "Please try again later."
        ) from exc

    except ValueError as exc:
        raise PayMongoError(
            "PayMongo returned an invalid response."
        ) from exc

    if not isinstance(result, dict):
        raise PayMongoError(
            "Unexpected PayMongo response format."
        )

    return result


def create_checkout_session(
    amount_centavos,
    donation_id,
    success_url,
    cancel_url,
):
    if (
        not isinstance(amount_centavos, int)
        or not 2000 <= amount_centavos <= 1000000
    ):
        raise PayMongoError(
            "Invalid donation amount."
        )

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
                    "SkyAware PH simulated "
                    "disaster relief donation"
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

    data = result.get("data")

    if not isinstance(data, dict):
        raise PayMongoError(
            "Invalid checkout session response."
        )

    attributes = data.get("attributes") or {}

    session_id = data.get("id")
    checkout_url = attributes.get("checkout_url")

    if (
        not isinstance(session_id, str)
        or not session_id.startswith("cs_")
    ):
        raise PayMongoError(
            "Invalid checkout session ID."
        )

    if not isinstance(checkout_url, str):
        raise PayMongoError(
            "PayMongo did not return a checkout URL."
        )

    parsed = urlparse(checkout_url)

    if (
        parsed.scheme != "https"
        or parsed.hostname != "checkout.paymongo.com"
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise PayMongoError(
            "PayMongo returned an unsafe checkout URL."
        )

    if attributes.get("livemode") is not False:
        raise PayMongoError(
            "Checkout was not confirmed as test mode."
        )

    return session_id, checkout_url


def retrieve_checkout_session(session_id):
    if (
        not isinstance(session_id, str)
        or not session_id.startswith("cs_")
        or not session_id[3:].isalnum()
    ):
        raise PayMongoError(
            "Invalid checkout session ID."
        )

    result = api_request(
        "GET",
        f"/checkout_sessions/{session_id}",
    )

    data = result.get("data")

    if not isinstance(data, dict):
        raise PayMongoError(
            "Invalid checkout session response."
        )

    if data.get("id") != session_id:
        raise PayMongoError(
            "Checkout session ID mismatch."
        )

    attributes = data.get("attributes") or {}

    if attributes.get("livemode") is not False:
        raise PayMongoError(
            "Payment is not confirmed as test mode."
        )

    return data


def checkout_is_paid(checkout_data, expected_amount):
    attributes = checkout_data.get("attributes") or {}
    payments = attributes.get("payments") or []

    if not isinstance(payments, list):
        return False

    for payment in payments:
        if not isinstance(payment, dict):
            continue

        details = payment.get("attributes") or {}

        if (
            details.get("status") == "paid"
            and details.get("currency") == "PHP"
            and type(details.get("amount")) is int
            and details.get("amount") == expected_amount
            and details.get("livemode") is False
        ):
            return True

    return False
