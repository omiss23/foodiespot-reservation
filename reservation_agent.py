# reservation_agent.py
import os
import json
import openai
from pydantic import BaseModel
from datetime import datetime as dt
from sqlalchemy import select
from models import SessionLocal, Restaurant, Reservation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'llama-3.1-8b')

# Pydantic schemas for function arguments
class AvailabilityArgs(BaseModel):
    restaurant_id: int
    datetime: str  # ISO format
    party_size: int

class BookingArgs(BaseModel):
    restaurant_id: int
    customer_name: str
    datetime: str
    party_size: int

# Tool implementations

def recommend_restaurants(cuisine: str | None, party_size: int) -> list[dict]:
    """Return top 5 restaurants matching cuisine and capacity."""
    with SessionLocal() as session:
        query = select(Restaurant).where(Restaurant.capacity >= party_size)
        if cuisine:
            query = query.where(Restaurant.cuisine.ilike(f"%{cuisine}%"))
        results = session.execute(query).scalars().all()
        results.sort(key=lambda r: r.rating, reverse=True)
        return [
            { 'id': r.id, 'name': r.name, 'location': r.location, 'cuisine': r.cuisine, 'rating': r.rating }
            for r in results[:5]
        ]

def availability_tool(restaurant_id: int, datetime: str, party_size: int) -> dict:
    """Check seating availability at a restaurant."""
    dt_obj = dt.fromisoformat(datetime)
    with SessionLocal() as session:
        existing = session.execute(
            select(Reservation)
            .where(Reservation.restaurant_id == restaurant_id)
            .where(Reservation.datetime == dt_obj)
            .where(Reservation.status == 'CONFIRMED')
        ).scalars().all()
        rest = session.get(Restaurant, restaurant_id)
        used = sum(r.party_size for r in existing)
        available = rest.capacity - used
        return { 'available_seats': available, 'fits': available >= party_size }

def booking_tool(restaurant_id: int, customer_name: str, datetime: str, party_size: int) -> dict:
    """Create a reservation record."""
    dt_obj = dt.fromisoformat(datetime)
    with SessionLocal() as session:
        new = Reservation(
            restaurant_id=restaurant_id,
            customer_name=customer_name,
            party_size=party_size,
            datetime=dt_obj,
            status='CONFIRMED'
        )
        session.add(new)
        session.commit()
        session.refresh(new)
        return { 'reservation_id': new.id, 'status': new.status }

class ReservationAgent:
    SYSTEM_PROMPT = (
        "You are FoodieSpot's reservation assistant. "
        "Use the available tools to recommend restaurants, check availability, and make bookings. "
        "Always respond concisely."
    )

    FUNCTIONS = [
        {
            'name': 'recommend_restaurants',
            'description': 'Suggest restaurants based on cuisine preference and party size',
            'parameters': {
                'type': 'object',
                'properties': {
                    'cuisine': {'type': 'string'},
                    'party_size': {'type': 'integer'}
                },
                'required': ['party_size']
            }
        },
        {
            'name': 'availability_tool',
            'description': 'Check seating availability at a restaurant',
            'parameters': AvailabilityArgs.schema()
        },
        {
            'name': 'booking_tool',
            'description': 'Book a reservation at a restaurant',
            'parameters': BookingArgs.schema()
        }
    ]

    def __init__(self):
        self.history: list[dict] = []

    def handle(self, user_input: str) -> str:
        self.history.append({'role': 'user', 'content': user_input})
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[{'role':'system','content':self.SYSTEM_PROMPT}] + self.history,
            functions=self.FUNCTIONS,
            function_call='auto'
        )
        msg = response.choices[0].message
        if msg.get('function_call'):
            fn_name = msg.function_call.name
            args = json.loads(msg.function_call.arguments)
            if fn_name == 'availability_tool':
                results = availability_tool(**AvailabilityArgs(**args).dict())
            elif fn_name == 'booking_tool':
                results = booking_tool(**BookingArgs(**args).dict())
            else:
                results = recommend_restaurants(**args)
            self.history.append({ 'role': 'function', 'name': fn_name, 'content': json.dumps(results) })
            followup = openai.ChatCompletion.create(
                model=MODEL_NAME,
                messages=[{'role':'system','content':self.SYSTEM_PROMPT}] + self.history
            )
            final_msg = followup.choices[0].message.content
            self.history.append({'role':'assistant','content':final_msg})
            return final_msg
        else:
            text = msg.content
            self.history.append({'role':'assistant','content':text})
            return text