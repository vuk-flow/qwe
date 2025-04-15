from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Backend.app.database import SessionLocal
from Backend.app.schemas.workers_schema import Worker as WorkerSchema
from Backend.app.models.workers_model import Worker
from Backend.app.schemas.workers_schema import WorkerCreate, WorkerUpdate
from Backend.app.file_reader import df_list


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/workers/", response_model=list[WorkerSchema])
def get_all_workers(db: Session = Depends(get_db)):
    workers = db.query(Worker).all()
    if not workers:
        return []
    return workers


@router.get("/workers/{id}", response_model=WorkerSchema)
def get_worker_by_id(id: int, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == id).first()
    if worker is None:
        raise HTTPException(status_code=404, detail=f"Worker with {id=} not found")

    return worker


@router.post("/workers/", response_model=WorkerSchema)
def create_worker(worker: WorkerCreate, db: Session = Depends(get_db)):
    db_worker = Worker(**worker.model_dump())

    exist_already = db.query(Worker).filter(Worker.email == worker.email).first()

    if exist_already:
        raise HTTPException(status_code=400, detail="Email already exist")

    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)

    return db_worker


@router.post("/workers/csv/", response_model=list[WorkerSchema])
def post_from_csv(db: Session = Depends(get_db)):
    
    inserted_workers = []

    if not df_list:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    
    for worker_data in df_list:
        if db.query(Worker).filter(Worker.email == worker_data["email"]).first():
            continue

        new_worker = Worker(**worker_data)
        db.add(new_worker)
        inserted_workers.append(new_worker)
    db.commit()
    for worker in inserted_workers:
        db.refresh(worker)

        

    return inserted_workers


@router.patch("/workers/edit/{id}", response_model=WorkerSchema)
def update_worker(id: int, worker_update: WorkerUpdate, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == id).first()

    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker with {id=} not found")

    if worker_update.email and worker_update.email != worker.email:
        existing_email = (
            db.query(Worker).filter(Worker.email == worker_update.email).first()
        )
        if existing_email:
            raise HTTPException(status_code=400, detail=f"Email already exists")

    for key, value in worker_update.model_dump(exclude_unset=True).items():
        setattr(worker, key, value)

    db.commit()
    db.refresh(worker)

    return worker


@router.delete("/workers/delete/{id}", response_model=WorkerSchema)
def delete_worker_by_id(id: int, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == id).first()
    if worker is None:
        raise HTTPException(status_code=404, detail=f"Worker with {id=} not found")
    db.delete(worker)
    db.commit()

    return worker
