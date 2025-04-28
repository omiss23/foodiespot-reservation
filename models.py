# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    cuisine = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    rating = Column(Float, nullable=False)
    reservations = relationship('Reservation', back_populates='restaurant')

class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    customer_name = Column(String, nullable=False)
    party_size = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)
    status = Column(String, default='CONFIRMED')
    restaurant = relationship('Restaurant', back_populates='reservations')

# SQLite engine and session factory
engine = create_engine('sqlite:///data.db', echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, future=True)

# Create tables
if __name__ == '__main__':
    Base.metadata.create_all(engine)
    print("Database tables created.")