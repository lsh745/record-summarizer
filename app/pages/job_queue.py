import os
import requests
import streamlit as st
import pandas as pd
from sqlalchemy import select
from utils.slack_utils import SlackSDK
from utils.database_utils import Database
from database.models import User, Job

st.title("작업 목록")

SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_DB')}:{os.getenv('POSTGRES_PASSWORD')}@database"
database = Database(SQLALCHEMY_DATABASE_URL)


stmt = select(Job)
job_data = database.session.scalars(stmt).all() 
job_dict_total = {}
for job in job_data:
    job_dict = job.__dict__
    job_dict_total[job_dict["id"]] = {}
    for key in job_dict:
        if key == "_sa_instance_state": continue
        job_dict_total[job_dict["id"]][key] = job_dict[key]

default_job_queue = pd.DataFrame(job_dict_total)
print(default_job_queue)
default_job_queue = default_job_queue.transpose()
job_queue = st.data_editor(
    default_job_queue,
    hide_index=True
)
