from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from psycopg2 import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hashlib
import asyncio

from .db import get_db
from .models import User, Analysis, AnalysisStatus
from .auth import hash_password, create_token, get_current_user
from .services import get_chess_analysis, normalize_pgn, process_analysis

router = APIRouter()

class UserSchema(BaseModel):
    username: str
    password: str



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


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username
    }


@router.post("/upload")
async def analyze_pgn(file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user), background_tasks: BackgroundTasks = None):
    contents = await file.read()

    pgn_content = contents.decode("utf-8")

    normalized_pgn = normalize_pgn(pgn_content)
    pgn_hash = hashlib.sha256(normalized_pgn.encode()).hexdigest()


    existing_analysis = db.query(Analysis).filter(
        Analysis.pgn_hash == pgn_hash,   
        Analysis.user_id == current_user.id
    ).first()

    if existing_analysis:
        return {
            "analysis": existing_analysis.result_text,
            "status": AnalysisStatus.exists.value
        }
    
    analysis = await get_chess_analysis(pgn_content)


    db_analysis = Analysis(
        pgn_content=pgn_content,
        normalized_pgn=normalized_pgn,   
        pgn_hash=pgn_hash,
        result_text=analysis,
        user_id=current_user.id,
        status=AnalysisStatus.done
    )


    try:
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        if background_tasks:
            background_tasks.add_task(process_analysis, db_analysis.id)


        return {
            "analysis": analysis,
            "status": AnalysisStatus.queued.value
        }
    except IntegrityError:
        db.rollback()
        
        existing_analysis = db.query(Analysis).filter(
            Analysis.pgn_hash == pgn_hash,
            Analysis.user_id == current_user.id
        ).first()
        
        return {
            "analysis": existing_analysis.result_text if existing_analysis else analysis,
            "status": AnalysisStatus.exists.value  
        }


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.id.desc())   
        .all()
    )
    return [
        {
            "id": record.id,
            "pgn_content": record.pgn_content,
            "result_text": record.result_text,
            "status": record.status.value
            
        }
        for record in history
    ]   
