from fastapi import APIRouter, Depends, HTTPException, Query

from models.user import User
from security.auth import get_current_user
from services.geocoding_service import geocode_address


router = APIRouter(prefix="/geocoding", tags=["Geocoding"])


@router.get("/address")
def geocode_address_lookup(
    address: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
):
    result = geocode_address(address)

    if not result:
        raise HTTPException(status_code=404, detail="Address could not be geocoded")

    return result
