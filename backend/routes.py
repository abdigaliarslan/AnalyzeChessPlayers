from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .db import get_db
from .models import User, Analysis
from .auth import hash_password, create_token, get_current_user
from .services import get_chess_analysis

router = APIRouter()

class UserSchema(BaseModel):
    username: str
    password: str

class AnalysisSchema(BaseModel):
    id: int
    pgn_content: str
    result_text: str
    user_id: int
    class Config:
        from_attributes = True




@router.post("/register")
def register(user: UserSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(400, "Username already exists")
    
    user = User(
        username=user.username,
        hashed_password=hash_password(user.password)
    ) 

    db.add(user)
    db.commit()
    return {"message": "User registered successfully"}


@router.post("/login")
def login(user: UserSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user.username).first()
    if not user: 
        raise HTTPException(401, "Invalid credentials")

    access_token = create_token(user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"} 


@router.post("/upload")
async def analyze_pgn(file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    contents = await file.read()

    pgn_content = contents.decode("utf-8")
    analysis = await get_chess_analysis(pgn_content)
    
    db_analysis = Analysis(
        pgn_content=pgn_content,
        result_text=analysis,
        user_id=current_user.id
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return {"analysis": analysis} 


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .all()
    )
    return history
 

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username
    }
