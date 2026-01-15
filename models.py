from pydantic import BaseModel
from typing import List, Optional

class PublishRequest(BaseModel):
    render_job_id: Optional[str] = None 
    video_filename: Optional[str] = None
    accounts: List[str]
    caption_override: Optional[str] = None 

class BrandSettingsRequest(BaseModel):
    shop: str
    logo_url: Optional[str] = None
    primary_color: str = "#000000"
    font_choice: str = "Roboto"
    cta_text: str = "Shop Now"

class ReviewRequest(BaseModel):
    name: str
    rating: int
    comment: str
    designation: Optional[str] = "Store Owner"