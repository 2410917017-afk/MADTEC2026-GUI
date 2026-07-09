from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.caso import CasoSoldadura

from app.schemas.casos import CasoCreate, CasoResponse

router = APIRouter(
    prefix="/casos",
    tags=["Casos de soldadura"]
)

@router.post("/", response_model=CasoResponse)
def crear_caso(caso: CasoCreate, db: Session = Depends(get_db)):

    nuevo = CasoSoldadura(
        Nombre=caso.Nombre,
        Tiempo=caso.Tiempo,
        Fuerza=caso.Fuerza,
        Compresion=caso.Compresion,
        Pulsos=caso.Pulsos,
        Material=caso.Material,
        Grosor=caso.Grosor,
        Separacion=caso.Separacion,
        Proximidad=caso.Proximidad,

    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo

@router.get("/", response_model=list[CasoResponse])
def obtener_casos(db: Session = Depends(get_db)):
    return db.query(CasoSoldadura).all()


@router.get("/{id}", response_model=CasoResponse)
def obtener_caso(id: int, db: Session = Depends(get_db)):

    caso = db.query(CasoSoldadura).filter(
        CasoSoldadura.id == id
    ).first()

    if caso is None:
        raise HTTPException(
            status_code=404,
            detail="Caso no encontrado"
        )

    return caso
