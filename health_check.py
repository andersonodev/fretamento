from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def health_check(request):
    """Simple health check endpoint for Heroku and monitoring"""
    return HttpResponse("OK - Django is running!", content_type="text/plain")