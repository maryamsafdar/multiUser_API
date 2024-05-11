from fastapi import FastAPI, HTTPException, Request, Depends, Query
from sqlmodel import SQLModel, Field, create_engine, Session, select
from fastapi_todo import settings
from typing import Annotated
from contextlib import asynccontextmanager

# Step-1: Create Database on Neon
# Step-2: Create .env file for environment variables
# Step-3: Create setting.py file for encrypting DatabaseURL
# Step-4: Create a Model
# Step-5: Create Engine
# Step-6: Create function for table creation
# Step-7: Create function for session management
# Step-8: Create context manager for app lifespan
# Step-9: Create all endpoints of todo app


app = FastAPI()
class User(SQLModel, table=True):
    email: str = Field(primary_key=True, index=True)
    password: str = Field()


# Create engine
# engine is one for whole connection
connection_string: str = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={
                       "sslmode": "require"}, pool_recycle=300, pool_size=10, echo=True)

# Create table
def create_tables():
    SQLModel.metadata.create_all(engine)

# make dependency and then inject
def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Creating Tables')
    create_tables()
    print("Tables Created")
    yield


app: FastAPI = FastAPI(
    lifespan=lifespan, title="dailyDo Todo App", version='1.0.0')


@app.get('/')
async def root():
    return {"message": "Welcome to dailyDo todo app"}


@app.get('/login/')
async def login( email: str = Query(...), password: str = Query(...), session: Session = Depends(get_session)):
    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")
    user = session.exec(select(User).where(User.email == email)).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password != password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"message": "Login successful", "user": user}

@app.post('/signup/')
async def signup(email: str = Query(...), password: str = Query(...), session: Session = Depends(get_session)):
    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")
    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=email, password=password)
    session.add(new_user)
    session.commit()
    return {"message": "Signup successful"}
