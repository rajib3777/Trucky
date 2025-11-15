from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripInputSerializer
from .models import Trip
from .services.map_service import generate_route_map
from .services.log_service import generate_log_sheet


class TripPlanView(APIView):
    """
    POST /api/trips/plan/

    Expected frontend payload:
    {
      "currentLocation": "Dhaka",
      "pickupLocation": "Dhaka",
      "dropoffLocation": "Chittagong",
      "currentCycleUsed": 30
    }

    Response:
    {
      "logSheet": { ...shape LogSheet.js expects... },
      "mapInfo": { ...shape MapDisplay.js expects... }
    }
    """

    def post(self, request):
        # camelCase → snake_case mapping
        payload = {
            "current_location": request.data.get("currentLocation"),
            "pickup_location": request.data.get("pickupLocation"),
            "dropoff_location": request.data.get("dropoffLocation"),
            "current_cycle_used": request.data.get("currentCycleUsed"),
        }

        serializer = TripInputSerializer(data=payload)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 1) Map + distance/duration
        map_result = generate_route_map(
            serializer.validated_data["pickup_location"],
            serializer.validated_data["dropoff_location"],
        )
        
        distance_miles = map_result["distance_miles"]

        # 2) HOS LogSheet (FMCSA-based)
        log_sheet = generate_log_sheet(
            distance_miles=distance_miles,
            current_cycle_used=serializer.validated_data["current_cycle_used"],
        )

        # 3) Save Trip (for history, analytics)
        Trip.objects.create(
            current_location=serializer.validated_data["current_location"],
            pickup_location=serializer.validated_data["pickup_location"],
            dropoff_location=serializer.validated_data["dropoff_location"],
            current_cycle_used=serializer.validated_data["current_cycle_used"],
            distance_miles=distance_miles,
            duration_hours=map_result["duration_hours"],
        )

        return Response(
            {
                "logSheet": log_sheet,
                "mapInfo": map_result["mapInfo"],
            },
            status=status.HTTP_200_OK,
        )

