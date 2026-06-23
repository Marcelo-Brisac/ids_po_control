class DynamicCSRFMiddleware:
    """
    Dynamically adds the request's origin to CSRF_TRUSTED_ORIGINS.
    Useful in development when the hostname is dynamic (e.g., preview URLs).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.META.get("HTTP_ORIGIN", "")
        if origin:
            from django.conf import settings

            if origin not in settings.CSRF_TRUSTED_ORIGINS:
                settings.CSRF_TRUSTED_ORIGINS.append(origin)
        return self.get_response(request)
