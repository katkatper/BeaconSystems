from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def search_routes():
    return {"message": "All searches"}

@router.post("/")
def create_search(Search: dict):

    # replace with database logic
    return {"message": "Searches created", "data": Search}
