# data_generator.py
import random
from faker import Faker
from models import Restaurant, engine, SessionLocal, Base

# Ensure tables exist
Base.metadata.create_all(engine)
fake = Faker()
cuisines = ['Italian','Indian','Chinese','Mexican','Japanese','French']

with SessionLocal() as session:
    for _ in range(50):
        restaurant = Restaurant(
            name=fake.company(),
            location=f"Zone {random.randint(1,10)}",
            cuisine=random.choice(cuisines),
            capacity=random.randint(20,100),
            rating=round(random.uniform(3.5,5.0),1)
        )
        session.add(restaurant)
    session.commit()
    print("Inserted 50 sample restaurants.")