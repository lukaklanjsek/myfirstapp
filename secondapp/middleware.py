# from django.conf import settings
# from django.shortcuts import redirect
# from django.urls import reverse
# #from django.utils.deprecation import MiddlewareMixin
#
# class LoginRequiredMiddleware:#(MiddlewareMixin):
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         if not request.user.is_authenticated:
#
#             public_urls = [
#                 reverse("login"),
#                 reverse("logout"),
#             ]
#
#             public_patterns = [
#                 "/static/",
#                 "/admin/login/",
#             ]
#
#             path = request.path
#
#             is_public = (
#                     path in public_urls or
#                     any(path.startswith(pattern) for pattern in public_patterns)
#             )
#
#             if not is_public:
#                 login_url = settings.LOGIN_URL or reverse("login")
#                 return redirect(f"{login_url}?next={path}")
#
#         return self.get_response(request)
