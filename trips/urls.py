from django.urls import path
from django.http import JsonResponse

def ping(request):
    return JsonResponse({"status": "ok", "message": "Alive"})

urlpatterns = [
    path("plan/", TripPlanView.as_view(), name="trip-plan"),
    path("ping/", ping, name="ping"),
]
