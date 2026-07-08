from pydantic import BaseModel


class PruebaBase(BaseModel):
    Id: str
    Muestras: int
    Tiempo: float
    Orientacion: str
    FMax: float
    IMax: float
    Grosor: float
    Material: str
    Diametro: float


class PruebaCreate(PruebaBase):
    pass


class PruebaResponse(PruebaBase):
    class Config:
        from_attributes = True
