# This Python file uses the following encoding: utf-8
from model import Base, engine

if __name__ == "__main__":
    engine.echo = True
    Base.metadata.create_all(bind=engine)
