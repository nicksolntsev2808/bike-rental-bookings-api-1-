import os
from datetime import datetime, timezone
from typing import Optional, List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "bikerentaldb"
    mongo_collection: str = "bookings"
    host: str = "127.0.0.1"
    port: int = 8030

    class Config:
        env_file = ".env"


settings = Settings()

app = FastAPI(title="bike-rental-bookings-api")

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]
collection = db[settings.mongo_collection]


class BookingIn(BaseModel):
    customer_name: str
    bike_type: str
    returned: bool = False


class BookingUpdate(BaseModel):
    customer_name: Optional[str] = None
    bike_type: Optional[str] = None
    returned: Optional[bool] = None


class BookingOut(BaseModel):
    id: str
    customer_name: str
    bike_type: str
    returned: bool
    created_at: datetime
    updated_at: datetime


def doc_to_out(doc) -> BookingOut:
    return BookingOut(
        id=str(doc["_id"]),
        customer_name=doc["customer_name"],
        bike_type=doc["bike_type"],
        returned=doc["returned"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def parse_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid id format")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/bookings", response_model=BookingOut, status_code=201)
async def create_booking(payload: BookingIn):
    now = datetime.now(timezone.utc)
    doc = payload.model_dump()
    doc["created_at"] = now
    doc["updated_at"] = now
    result = await collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_out(doc)


@app.get("/api/v1/bookings", response_model=List[BookingOut])
async def list_bookings(
    returned: Optional[bool] = Query(default=None),
    bike_type: Optional[str] = Query(default=None),
):
    query = {}
    if returned is not None:
        query["returned"] = returned
    if bike_type:
        query["bike_type"] = bike_type
    cursor = collection.find(query)
    return [doc_to_out(doc) async for doc in cursor]


@app.get("/api/v1/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: str):
    oid = parse_object_id(booking_id)
    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Booking not found")
    return doc_to_out(doc)


@app.patch("/api/v1/bookings/{booking_id}", response_model=BookingOut)
async def update_booking(booking_id: str, payload: BookingUpdate):
    oid = parse_object_id(booking_id)
    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await collection.find_one_and_update(
        {"_id": oid}, {"$set": update_data}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Booking not found")
    return doc_to_out(result)


@app.delete("/api/v1/bookings/{booking_id}", status_code=204)
async def delete_booking(booking_id: str):
    oid = parse_object_id(booking_id)
    result = await collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
