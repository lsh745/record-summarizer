from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData, Table

Base = declarative_base()

class Database:
    def __init__(self, database_url: str, create: bool = False):
        self.engine = create_engine(database_url, echo=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        if create:
            Base.metadata.create_all(self.engine)
        else:
            Base.metadata.bind = self.engine


    def connect_table(self, table_name: str):
        return Table(table_name, MetaData(), autoload_with=self.engine)