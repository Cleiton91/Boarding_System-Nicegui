from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from urllib.parse import quote_plus
from dotenv import load_dotenv
import uvicorn
import os



# Carregamento de Credenciais no.env
load_dotenv()

# Classe para conexão com Banco de dados
class BoardingSystemApp:
    def __init__(self):        
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")

        if not db_password:
            raise RuntimeError("DB_PASSWORD não definido. Configure no arquivo .env.")

        senha = quote_plus(db_password)
        self.DATABASE_URL = f"mysql+pymysql://{db_user}:{senha}@{db_host}/{db_name}"

        # Configura banco
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

        # Cria ORM
        self.define_models()

        # Cria a tabela
        self.Base.metadata.create_all(bind=self.engine)

        # Cria modelo Pydantic
        self.define_pydantic_models()

        # Cria app FastAPI
        self.app = FastAPI()

        # Adiciona rotas
        self.add_routes()

    # Mapeamento do objeto (ORM) 
    def define_models(self):
        class PassengerDB(self.Base):
            __tablename__ = "passengers"
            id = Column(Integer, primary_key=True, index=True)
            NAME = Column(String(100), index=True)
            FLIGHT = Column(String(100), index=True)
            ORIGIN = Column(String(100))
            DESTINATION = Column(String(100))
            SEAT = Column(String(10))
            CHECKIN_STATUS = Column(Integer)  # 0 = Não feito, 1 = Feito

        self.PassengerDB = PassengerDB

    # Pydantic 
    def define_pydantic_models(self):
        class Passenger(BaseModel):
            NAME: str
            FLIGHT: str
            ORIGIN: str
            DESTINATION: str
            SEAT: str

        class PassengerResponse(Passenger):
            id: int
            CHECKIN_STATUS: int

            class Config:
                orm_mode = True

        self.Passenger = Passenger
        self.PassengerResponse = PassengerResponse

    # Gerenciador DB Session 
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Rotas da API 
    def add_routes(self):
        @self.app.post("/passengers", response_model=self.PassengerResponse)
        def create_passenger(passenger: self.Passenger, db: Session = Depends(self.get_db)):
            db_passenger = self.PassengerDB(**passenger.dict(), CHECKIN_STATUS=0)
            db.add(db_passenger)
            try:
                db.commit()
                db.refresh(db_passenger)
                return db_passenger
            except:
                db.rollback()
                raise HTTPException(status_code=400, detail="Erro ao cadastrar passageiro.")

        @self.app.get("/passengers", response_model=List[self.PassengerResponse])
        def list_passengers(db: Session = Depends(self.get_db)):
            return db.query(self.PassengerDB).all()

        @self.app.get("/passengers/{passenger_id}", response_model=self.PassengerResponse)
        def get_passenger(passenger_id: int, db: Session = Depends(self.get_db)):
            passenger = db.query(self.PassengerDB).filter(self.PassengerDB.id == passenger_id).first()
            if not passenger:
                raise HTTPException(status_code=404, detail="Passageiro não encontrado.")
            return passenger
        
        @self.app.post("/passengers/{passenger_id}/checkin", response_model=self.PassengerResponse)
        def checkin_passenger(passenger_id: int, db: Session = Depends(self.get_db)):
            
            passenger = db.query(self.PassengerDB).filter(self.PassengerDB.id == passenger_id).first()

            
            if not passenger:
                raise HTTPException(status_code=404, detail="Passageiro não encontrado.")

            # Atualiza o status do check-in
            passenger.CHECKIN_STATUS = 1
            
            # Salva (commita) a alteração no banco
            try:
                db.commit()
                db.refresh(passenger) 
                return passenger
            except:
                db.rollback()
                raise HTTPException(status_code=500, detail="Erro interno ao salvar o check-in.")

# Comando de start via IDE
boarding_system = BoardingSystemApp()
app = boarding_system.app

if __name__ == "__main__":    
    uvicorn.run("Back_end:app", host="127.0.0.1", port=8000, reload=True)




