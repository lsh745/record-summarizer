import streamlit as st
import pandas as pd
import os
import tempfile
import requests
from slack_utils import SlackSDK



def toggle_availability_state():
    st.session_state.unavailable = not st.session_state.unavailable


if "unavailable" not in st.session_state:
    st.session_state.unavailable = True

if "slack_user_dict" not in st.session_state:
    st.session_state.slack_user_dict = {}


if not st.session_state.slack_user_dict:
    slack_user_dict = SlackSDK().get_user_dict()["members"] # 따로 DB 구현하지 않을 경우 Slack API 요청 초과 발생 가능
    for data in slack_user_dict:
        if data["deleted"]: continue
        st.session_state.slack_user_dict[data["profile"]["display_name"]] = data["id"] 
        
st.title("음성인식/요약")

options =  pd.DataFrame([
    {"option": "gpt_model", "value": "gpt-4o"},
    {"option": "save_dir", "value": ""},
    {"option": "video_ext_list", "value": "mp4"},
    {"option": "audio_ext_list", "value": "m4a, wav"},
    {"option": "axis", "value": "-1"},
    {"option": "n_mels", "value": "128"},
    {"option": "length", "value": "480000"},
    {"option": "model", "value": "large"},
    # {"option": "pipeline_model", "value": "pyannote/speaker-diarization-3.1"},
    # {"option": "use_auth_token", "value": "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"}
])

with st.expander("설정"):
    st.data_editor(
    options,
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
prompt_data = st.text_area("요약용 프롬프트") # Placeholder 적기
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

    payload = {
        "slack_id": st.session_state.slack_user_dict[slack_user_name],
        # "gpt_model": "gpt-4o", 
        "gpt_model": "gpt-3.5-turbo", 
        "language": language_selectbox,
        "upload_data_path": save_dir,
        "video_ext_list": ["mp4"],
        "audio_ext_list": ["m4a", "wav"],
        "messages": [ 
            {"role": "system", "content": "너는 사용자가 제공하는 회의 내용을 보고 요약해야 돼. 회사에서 진행 한 회의 내용이고 회의록처럼 요약하고 정리해서 사용자한테 돌려줘. 바로 아래에 나올 내용은 사용자의 요구사항이고 비어있을 땐 무시하면 돼."},
            {"role": "user", "content": prompt_data}, 
            {"role": "system", "content": "이제 아레에 회의 내용이 제공될거야."}
        ]
    }

    response = requests.request(
        method="POST",
        url="http://192.168.0.21:8089/api/stt", # TODO: 환경변수로 바꾸기
        json=payload
    )
    # print(response.json())
