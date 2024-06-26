from database_utils import Base, engine
from sqlalchemy.orm import sessionmaker
from models import Job
from enums import *

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


# Create all tables
Base.metadata.create_all(engine)

# Adding a new job
hash_value = "CAFEBEBECAFEBEBE"
job1 = Job(
    hash=hash_value, 
    user_id="U04JTRAGYBY",
    gpt_model=GPTModelEnum.GPT35,
    language=LanguageEnum.AUTO,
    prompt="",
    gpt_result=None,
    save_path=f"/app/storage/test/{hash_value}",
    status=StatusEnum.PENDING
    )
# session.add(job1)
# session.commit()

job = session.query(Job).first()
print(
    job.hash, 
    job.user_id,
    job.gpt_model,
    job.language,
    job.prompt,
    job.gpt_result,
    job.save_path,
    job.status, 
    job.created_at, 
    job.updated_at, 
    job.finished_at
    )