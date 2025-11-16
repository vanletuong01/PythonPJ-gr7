from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def get_types():
    return [
        {"id": 1, "name": "Chính quy"},
        {"id": 2, "name": "Liên thông"},
        {"id": 3, "name": "Tại chức"},
    ]
