from sqlalchemy import Column, Integer, String, Float

from app.database.database import Base


class PruebasCETEVI(Base):
    __tablename__ = "PruebasCETEVI"

    Id = Column(String(300), primary_key=True)

    Muestras = Column(Integer)

    Tiempo = Column(Float)

    Orientacion = Column(String(300))

    FMax = Column(Float)

    IMax = Column(Float)

    Grosor = Column(Float)

    Material = Column(String(300))

    Diametro = Column(Float)

