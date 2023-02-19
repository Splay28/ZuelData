from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker

engine = create_engine("mysql+mysqlconnector://root:Laobaofa100fen@localhost:3306", pool_recycle=7200)
insp = inspect(engine)

metadata = MetaData(bind=engine)
# reflect 映射dash_base库下的表结构
metadata.reflect(schema='zueldb')

