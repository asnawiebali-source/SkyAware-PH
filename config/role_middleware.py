
"""
SkyAware PH - Role-Based Interface Separation

Two application roles:
    Admin: is_staff=True
    User:  is_staff=False

Admin accounts access custom administration pages only.
Regular users access the regular SkyAware PH website.
"""

from django.shortcuts import redirect


class SeparateAdminInterfaceMiddleware:

    ADMIN_ROUTES = {
        "admin_dashboard",
        "admin_users",
        "admin_user_detail",
        "logout",
    }

    PROTECTED_ROUTES = {
        "admin_dashboard",
        "admin_users",
        "admin_user_detail",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(
        self,
        request,
        view_func,
        view_args,
        view_kwargs,
    ):
        user = getattr(request, "user", None)

        if user is None or not user.is_authenticated:
            return None

        match = request.resolver_match

        if match is None:
            return None

        route = match.url_name
        namespaces = match.namespaces or []

        # ADMIN ACCOUNT
        if user.is_staff:
            if route in self.ADMIN_ROUTES:
                return None

            # Every other regular-user page
            # redirects to custom Admin Dashboard.
            return redirect("admin_dashboard")

        # REGULAR USER ACCOUNT
        if route in self.PROTECTED_ROUTES:
            return redirect("dashboard")

        # Block the /admin/ compatibility redirect
        # for regular users.
        if "admin" in namespaces:
            return redirect("dashboard")

        return None
