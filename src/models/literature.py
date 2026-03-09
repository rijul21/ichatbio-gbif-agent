from pydantic import Field
from uuid import UUID
from src.models.base import ProductionBaseModel


class GBIFLiteratureByIdParams(ProductionBaseModel):
    uuid: UUID = Field(
        ...,
        description="UUID of the literature item to retrieve.",
        examples=["83a00190-7038-3970-a7e8-5e5563c40e37"],
    )