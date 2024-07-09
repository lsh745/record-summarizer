from speech.speech import Speech
from utils.utils import multi_ext_glob, ext_conversion, archive_dir
from utils.slack_utils import SlackSDK
from utils.database_utils import Database
from utils.minio_utils import MinIO
from database.models import User, Job
import io
import os
import time
import uvicorn
from fastapi import FastAPI, Request, Header, Response, status, BackgroundTasks, APIRouter
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import select
from openai import OpenAI


class InferenceRequest:
    def __init__(self):
        print("INITIALIZING API SERVER")
        
        self.router = APIRouter()
        self.router.add_api_route("/api/stt", self.stt, methods=["POST"])
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

        self.language_dict = {
            "한국어": "ko",
            "영어": "en",
            "자동": None
        }


    # def update_table(self):
    
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
            

    def stt(
        self, 
        request_body: dict
        ): # TODO: 작업 분리
        def debug_print(request_body: dict):
            print("[*] SLACK ID:", request_body["slack_id"])
            print("[*] BUCKET:", request_body["bucket"])
            print("[*] HASH:", request_body["hash"])
            print("[*] GPT_MODEL:", request_body["gpt_model"])
            print("[*] VIDEO EXT:", request_body["video_ext_list"])
            print("[*] AUDIO EXT:", request_body["audio_ext_list"])
            print("[*] MESSAGES:", request_body["messages"])
            print("[*] LANGUAGE:", request_body["language"])

        def make_directories():
            if not os.path.isdir(self.download_dir):
                print("[*] MAKING DOWNLOADS DIRECTORY.", self.download_dir)
                os.makedirs(self.download_dir)

            if not os.path.isdir(save_dir):
                print("[*] MAKING DOWNLOADS DIRECTORY.")
                os.makedirs(save_dir)

        def minio_download(request_body: dict):
            print(f"[*] PREFIX: {request_body['bucket']}/{request_body['hash']}")
            object_list = self.storage.list_object(
                prefix = f"{request_body['hash']}/source/"
            )
            for object in object_list:
                _, extension = os.path.splitext(object.object_name)
                basename = os.path.basename(object.object_name)

                if "." in extension:
                    extension = extension.replace(".", "")

                if extension in request_body["video_ext_list"]:
                    print("[*] VIDEO")
                    ext_path = "video"
                elif extension in request_body["audio_ext_list"]:
                    print("[*] AUDIO")
                    ext_path = "audio"
                
                print("[+] DOWNLOADING", extension, ext_path, object.object_name, f"{self.download_dir}/{request_body['hash']}/source/{ext_path}/{basename}")
                self.storage.download_file(
                    object_name=object.object_name,
                    file_path=f"{self.download_dir}/{request_body['hash']}/source/{ext_path}/{basename}" ## TODO: Path unification, variantization
                )

        def speech_jobs(request_body: dict, save_dir: str) -> dict:
            speech_tool = Speech(
                save_dir=save_dir,
                language=self.language_dict[request_body["language"]]
                )

            speech_tool.video_list = multi_ext_glob(f"{self.download_dir}/{request_body['hash']}/source/video/", request_body["video_ext_list"], recursive=True) ## TODO: Path unification, variantization
            speech_tool.audio_list = multi_ext_glob(f"{self.download_dir}/{request_body['hash']}/source/audio/", request_body["audio_ext_list"], recursive=True) ## TODO: Path unification, variantization
            for audio in speech_tool.audio_list:
                speech_tool.convert_to_wav(audio)
            speech_tool.wav_list = multi_ext_glob(f"{self.download_dir}/{request_body['hash']}/source/audio/", ["wav"], recursive=True) ## TODO: Path unification, variantization
            print(f"[*]\tVIDEO EXTENSIONS: {request_body['video_ext_list']}\n\tLENGTH OF VIDEOS: {len(speech_tool.video_list)}")
            print(f"[*]\tAUDIO EXTENSIONS: {request_body['audio_ext_list']}\n\tLENGTH OF AUDIOS: {len(speech_tool.audio_list)}")
            print(f"[*]\TARGET EXTENSIONS: ['wav']\n\tLENGTH OF WAVS: {len(speech_tool.wav_list)}")
        
            return speech_tool.run()

        def minio_upload(save_dir: str) -> list:
            uploaded_list = []
            for filename in os.listdir(save_dir):
                result_path = os.path.join(save_dir, filename)
                print("[*] UPLOADING FILE.", filename, result_path)
                self.storage.upload_file(
                    object_name = f"{request_body['hash']}/result/{filename}",
                    file_path=result_path
                )
                uploaded_list.append(result_path)
            return uploaded_list

        def update_db(request_body: dict, uploaded_list: list):
            user_table = self.database.connect_table("user")
            stmt = select(user_table).where(user_table.c.id == request_body["slack_id"])
            with self.database.engine.connect() as conn:
                for row in conn.execute(stmt):
                    print(row.slack_id) 
                    self.slack_sdk.send_message_multiple_files(
                        message=response.choices[0].message.content,
                        # message="test",
                        file_path_list=uploaded_list,
                        channel=row.slack_id
                    )

        self.storage.bucket_name = request_body['bucket']
        save_dir = f"{self.download_dir}/{request_body['hash']}/result/"

        if self.running: return 
        else: self.running = True
        debug_print(request_body)

        make_directories()
        minio_download(request_body)

        whisper_result = speech_jobs(request_body, save_dir)
        request_body["messages"].append({"role": "user", "content": whisper_result[0]["text"]})

        response = self.gpt_client.chat.completions.create(
            model=request_body["gpt_model"],
            messages=request_body["messages"]
        )
        print("[*] CHATGPT RESPONSE:", response)
        print("[*] response.choices[0].message.content", response.choices[0].message.content)
        # print(f"PAYLOAD:\n\tmessage={response.choices[0].message.content}\n\tfile_path={os.path.join(request_body['upload_data_path'], 'archive.zip')}\n\tchannel={request_body['slack_id']}")

        uploaded_list = minio_upload(save_dir)
        update_db(request_body, uploaded_list)

        # ## TODO: DB 확인해서 완료되지 않은 job이 있을 시 그 job 진행, 없을 시 self.running = False


    def storage_lambda(
        self,
        request_body: dict
        ):
        print(request_body)


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