from fastapi import APIRouter, Query
from ..models.schemas import WeatherResponse
from ..services.weather_service import fetch_current_weather

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/current", response_model=WeatherResponse)
def get_current_weather_data(
    lat: float = Query(..., description="Latitude of the farm"),
    lng: float = Query(..., description="Longitude of the farm"),
):
    data = fetch_current_weather(lat, lng)
    return WeatherResponse(**data)
