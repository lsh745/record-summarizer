import streamlit as st
import pandas as pd
import os
import tempfile
import requests
from sqlalchemy import select
from utils.slack_utils import SlackSDK
from utils.database_utils import Database
from database.models import User, Job


def toggle_availability_state():
    st.session_state.unavailable = not st.session_state.unavailable

## INITIALIZE
if "unavailable" not in st.session_state:
    st.session_state.unavailable = True

if "slack_user_dict" not in st.session_state:
    st.session_state.slack_user_dict = {}

# SQLALCHEMY_DATABASE_URL = f"{os.getenv('DB_TYPE')}://{os.getenv('POSTGRES_DB')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('DOCKER_HOST_IP')}:{os.getenv('POSTGRESQL_PORT')}/database"
SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_DB')}:{os.getenv('POSTGRES_PASSWORD')}@database" # TODO: 환경변수화
database = Database(SQLALCHEMY_DATABASE_URL)

if not st.session_state.slack_user_dict:
    stmt = select(User)
    user_data = database.session.scalars(stmt).all()
    for data in user_data:
        st.session_state.slack_user_dict[data.display_name] = data.id
        
st.title("음성인식/요약")

default_options =  pd.DataFrame([
    {"option": "gpt_model", "value": "gpt-3.5-turbo"},
    # {"option": "save_dir", "value": ""},
    # {"option": "video_ext_list", "value": "mp4"},
    # {"option": "audio_ext_list", "value": "m4a, wav"},
    # {"option": "axis", "value": "-1"},
    # {"option": "n_mels", "value": "128"},
    # {"option": "length", "value": "480000"},
    # {"option": "model", "value": "large"},
    # {"option": "pipeline_model", "value": "pyannote/speaker-diarization-3.1"},
    # {"option": "use_auth_token", "value": },
    # {"option": "gpt_token", "value": ""},
])

with st.expander("설정"):
    options = st.data_editor(
        default_options,
        disabled=["option"],
        hide_index=True,
        use_container_width=True
    )

col0, col1, col2 = st.columns([5,5,1])
with col0:
    language_selectbox = col0.selectbox("언어", ["한국어", "영어", "자동"], index=0)

with col1:
    slack_user_name = col1.selectbox("유저", st.session_state.slack_user_dict.keys(), index=0)

# with col2:
#     slack_user_list_refresh = col2.button("새로고침")

upload_data_list = st.file_uploader(
    "음성 파일 업로드", 
    type=["m4a", "wav", "mp4"],
    accept_multiple_files=True,
    on_change=toggle_availability_state
    )
prompt_data = st.text_area("요약용 프롬프트", placeholder="ex) ~~에 관한 내용이다. ") # Placeholder 적기
start_button = st.button("작업 시작", disabled=st.session_state.unavailable, on_click=toggle_availability_state)

if start_button:
    st.success("요청 전송 완료. 결과물은 Slack 메시지로 전송됩니다.")
    
    temp_dir = tempfile.mkdtemp()
    save_dir = os.path.join(temp_dir, "result")
    for upload_data in upload_data_list:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, upload_data.name)
        print("SAVING AS:", path)
        with open(path, "wb") as f:
            f.write(upload_data.getvalue())

    print("ASDJIOAJSIODJAIOSDJI", str(options[options["option"] == "gpt_model"]["value"]).split()[1])
    payload = {
        "slack_id": st.session_state.slack_user_dict[slack_user_name],
        # "gpt_model": "gpt-4o", 
        "gpt_model": str(options[options["option"] == "gpt_model"]["value"]).split()[1],
        "language": language_selectbox,
        "upload_data_path": save_dir,
        "video_ext_list": ["mp4"],
        "audio_ext_list": ["m4a", "wav"],
        # "video_ext_list": options[options["option"] == "video_ext_list"]["value"].split(),
        # "audio_ext_list": options[options["option"] == "audio_ext_list"]["value"].split(),
        "messages": [ 
            {"role": "system", "content": "너는 사용자가 제공하는 회의 내용을 보고 요약해야 돼. 회사에서 진행 한 회의 내용이고 회의록처럼 요약하고 정리해서 사용자한테 돌려줘. 바로 아래에 나올 내용은 사용자의 요구사항이고 비어있을 땐 무시하면 돼."},
            {"role": "user", "content": prompt_data}, 
            {"role": "system", "content": "이제 아래에 회의 내용이 제공될거야."}
        ]
    }

    job = Job(
        user_id=payload["slack_id"],
        gpt_model=payload["gpt_model"],
        language=payload["language"],
        prompt=prompt_data,
        upload_path=payload["upload_data_path"]
        )
    database.session.add(job)
    database.session.commit()

    response = requests.request(
        method="POST",
        url=f"http://{os.getenv('DOCKER_HOST_IP')}:{os.getenv('WEBSERVER_PORT')}/api/stt",
        json=payload
    )
    print(response.json())
