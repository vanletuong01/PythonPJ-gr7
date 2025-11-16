from pydantic import BaseModel

class MajorResponse(BaseModel):
    MajorID: int
    MajorName: str
    Full_name_mj: str | None = None

    model_config = {
        "from_attributes": True
    }
