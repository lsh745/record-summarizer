from speech.speech import Speech
from utils.utils import multi_ext_glob, ext_conversion, archive_dir
from utils.slack_utils import SlackSDK
from utils.database_utils import Database
from utils.minio_utils import MinIO
from database.models import User, Job
from database.enums import GPTModelEnum, LanguageEnum, StatusEnum

import io
import os
import datetime
import copy
import uvicorn
import hashlib

from fastapi import FastAPI, Request, Header, Response, status, BackgroundTasks, APIRouter
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import select, update
from openai import OpenAI


class InferenceRequest:
    def __init__(self):
        print("INITIALIZING API SERVER")
        
        self.router = APIRouter()
        self.router.add_api_route("/api/stt", self.loop_stt, methods=["POST"])
        self.router.add_api_route("/api/get_users", self.get_users, methods=["POST"])
        self.router.add_api_route("/api/", self.storage_lambda, methods=["POST"])

        self.slack_sdk = SlackSDK()
        self.gpt_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),)
        self.database_url = f"postgresql://{os.getenv('POSTGRES_DB')}:{os.getenv('POSTGRES_PASSWORD')}@database"
        self.table_name = "job"
        self.database = Database(self.database_url, True)
        self.storage = MinIO()

        self.download_dir = "/downloads"
        self.running = False

        self.video_ext_list = ["mp4", "MXF"]
        self.audio_ext_list = ["m4a", "wav"]
        self.default_message = [ 
            {"role": "system", "content": "너는 사용자가 제공하는 회의 내용을 보고 요약해야 돼. 회의록처럼 요약하고 정리해서 사용자한테 돌려줘. 바로 아래에 나올 내용은 사용자의 요구사항이고 비어있을 땐 무시하면 돼."},
            {}, 
            {"role": "system", "content": "이제 아래에 회의 내용이 제공될거야."}
        ]


    def get_users(self):
        slack_user_dict = SlackSDK().get_user_dict()["members"]
        for data in slack_user_dict:
            if data["deleted"] or not data["profile"]["display_name"]: continue
            user = User(
                slack_id=data["id"],
                display_name=data["profile"]["display_name"]
            )
            self.database.session.add(user)
        self.database.session.commit()


    def send_slack_message(self, user_id: str, message: str, uploaded_list: list = []):
        row = self.database.session.query(User).filter(
                User.id == user_id
            ).first() 

        self.slack_sdk.send_message_multiple_files(
            message=message,
            file_path_list=uploaded_list,
            channel=row.slack_id
        )
    

    def update_job_by_id(self, job_id: int, **kwargs):
        self.database.session.query(
            Job
            ).filter(
                Job.id == job_id
            ).update(
                kwargs
            )
        self.database.session.commit()
        self.database.session.flush()


    def loop_stt(
        self, 
        request_body: dict = {}
        ):
        if self.running: return 
        else: self.running = True

        while 1:
            latest_job = self.database.session.query(
                    Job
                ).filter(
                    Job.status == StatusEnum.PENDING
                ).order_by(
                    Job.created_at.desc()
                ).first() 

            if not latest_job: 
                self.running = False
                break

            try:
                self.stt(latest_job)
            except Exception as e:
                print(e)
                self.send_slack_message(latest_job.user_id, f"========== 에러 발생 ==========\n{e}")
                self.update_job_by_id(latest_job.id, status=StatusEnum.FAILED, error_message=str(e))
                
                
    def stt(
        self, 
        latest_job: Job
        ):
        def _debug_print(latest_job: Job):
            print("[*] SLACK ID:", latest_job.user_id)
            print("[*] BUCKET:", latest_job.bucket)
            print("[*] HASH ID:", latest_job.hash_id)
            print("[*] STATUS:", latest_job.status)
            print("[*] GPT_MODEL:", latest_job.gpt_model)
            print("[*] LANGUAGE:", latest_job.language)
            print("[*] GPT RESULT:", latest_job.gpt_result)
            # print("[*] VIDEO EXT:", latest_job["video_ext_list"])
            # print("[*] AUDIO EXT:", latest_job["audio_ext_list"])
            print("[*] MESSAGE:", latest_job.message)
            print("[*] CREATED_AT:", latest_job.created_at)
            # print("[*] UPDATED_AT:", latest_job.updated_at)
            # print("[*] FINISHED_AT:", latest_job.finished_at)

        def _make_directories():
            if not os.path.isdir(self.download_dir):
                print("[*] MAKING DOWNLOADS DIRECTORY.", self.download_dir)
                os.makedirs(self.download_dir)

            if not os.path.isdir(save_dir):
                print("[*] MAKING DOWNLOADS DIRECTORY.")
                os.makedirs(save_dir)

        def _minio_download(latest_job: Job):
            print(f"[*] PREFIX: {latest_job.bucket}/{latest_job.hash_id}")
            object_list = self.storage.list_object(
                prefix = f"{latest_job.hash_id}/source/"
            )
            for object in object_list:
                _, extension = os.path.splitext(object.object_name)
                basename = os.path.basename(object.object_name)

                if "." in extension:
                    extension = extension.replace(".", "")

                if extension in self.video_ext_list:
                    print("[*] VIDEO")
                    ext_path = "video"
                elif extension in self.audio_ext_list:
                    print("[*] AUDIO")
                    ext_path = "audio"
                
                print("[+] DOWNLOADING", extension, ext_path, object.object_name, f"{self.download_dir}/{latest_job.hash_id}/source/{ext_path}/{basename}")
                self.storage.download_object(
                    object_name=object.object_name,
                    file_path=f"{self.download_dir}/{latest_job.hash_id}/source/{ext_path}/{basename}" ## TODO: Path unification, variantization
                )

        def _speech_jobs(latest_job: Job, save_dir: str) -> dict:
            speech_tool = Speech(
                save_dir=save_dir,
                language=latest_job.language
                )

            speech_tool.video_list = multi_ext_glob(f"{self.download_dir}/{latest_job.hash_id}/source/video/", self.video_ext_list, recursive=True) ## TODO: Path unification, variantization
            speech_tool.audio_list = multi_ext_glob(f"{self.download_dir}/{latest_job.hash_id}/source/audio/", self.audio_ext_list, recursive=True) ## TODO: Path unification, variantization
            for audio in speech_tool.audio_list:
                speech_tool.convert_to_wav(audio)
            speech_tool.wav_list = multi_ext_glob(f"{self.download_dir}/{latest_job.hash_id}/source/audio/", ["wav"], recursive=True) ## TODO: Path unification, variantization
            print(f"[*]\tVIDEO EXTENSIONS: {self.video_ext_list}\n\tLENGTH OF VIDEOS: {len(speech_tool.video_list)}")
            print(f"[*]\tAUDIO EXTENSIONS: {self.audio_ext_list}\n\tLENGTH OF AUDIOS: {len(speech_tool.audio_list)}")
            print(f"[*]\TARGET EXTENSIONS: ['wav']\n\tLENGTH OF WAVS: {len(speech_tool.wav_list)}")
        
            return speech_tool.run()

        def _minio_upload(save_dir: str) -> list:
            uploaded_list = []
            for filename in os.listdir(save_dir):
                result_path = os.path.join(save_dir, filename)
                print("[*] UPLOADING FILE.", filename, result_path)
                self.storage.upload_object(
                    object_name = f"{latest_job.hash_id}/result/{filename}",
                    file_path=result_path
                )
                uploaded_list.append(result_path)
            return uploaded_list
        
        self.update_job_by_id(latest_job.id, status=StatusEnum.INITIALIZING)
        self.storage.bucket_name = latest_job.bucket
        save_dir = f"{self.download_dir}/{latest_job.hash_id}/result/"
        _debug_print(latest_job)

        _make_directories()
        _minio_download(latest_job)

        self.update_job_by_id(latest_job.id, status=StatusEnum.IN_PROGRESS_WHISPER)
        whisper_result = _speech_jobs(latest_job, save_dir)
        print(whisper_result)
        messages = copy.deepcopy(self.default_message)
        messages[1] = {"role": "user", "content": latest_job.prompt}
        messages.append({"role": "user", "content": whisper_result[0]["text"]})

        self.update_job_by_id(latest_job.id, status=StatusEnum.IN_PROGRESS_CHATGPT)
        response = self.gpt_client.chat.completions.create(
            model=latest_job.gpt_model,
            messages=messages
        )
        print("[*] CHATGPT RESPONSE:", response, type(response))
        print("[*] response.choices[0].message.content", response.choices[0].message.content)

        uploaded_list = _minio_upload(save_dir)
        self.send_slack_message(latest_job.user_id, response.choices[0].message.content, uploaded_list)
        self.update_job_by_id(latest_job.id, status=StatusEnum.COMPLETED, finished_at=datetime.datetime.now())


    def storage_lambda(
        self,
        request_body: dict
        ):
        print(request_body)

        user_row = self.database.session.query(User).filter(
                User.storage_id == request_body["Records"][0]["userIdentity"]["principalId"]
            ).first()

        h = hashlib.new('sha256')
        h.update(bytes(f"{user_row.slack_id}_{datetime.datetime.now()}", 'utf-8'))
        hash_value = h.hexdigest()
        basename = os.path.basename(request_body["Records"][0]["s3"]["object"]["key"])

        self.storage.move_object(
            request_body["Records"][0]["s3"]["bucket"]["name"],
            request_body["Records"][0]["s3"]["object"]["key"],
            request_body["Records"][0]["s3"]["bucket"]["name"],
            f"{hash_value}/source/{basename}"
        )
        
        
        job = Job(
            user_id=user_row.id,
            gpt_model="gpt-3.5-turbo", # TODO: 유저가 바꿀 수 있게 변경
            language="ko", # TODO: 유저가 바꿀 수 있게 변경
            prompt="", # TODO: 유저가 바꿀 수 있게 변경
            bucket="large-size", # TODO: 유저가 바꿀 수 있게 변경
            hash_id=hash_value
            )
        self.database.session.add(job)
        self.database.session.commit()
        self.loop_stt()


    def runserver(self):
        print("RUNSERVER")
        app = FastAPI()

        origins = ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.include_router(self.router)
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT")))


if __name__ == "__main__":
    inference_api = InferenceRequest()
    inference_api.runserver()
