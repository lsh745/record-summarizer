from speech.speech import Speech
from utils.utils import multi_ext_glob, ext_conversion, archive_dir
from utils.slack_utils import SlackSDK
import io
import os
import time
import uvicorn
from fastapi import FastAPI, Request, Header, Response, status, BackgroundTasks, APIRouter
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from openai import OpenAI


class InferenceRequest:
    def __init__(self):
        print("INITIALIZING API SERVER")
        self.router = APIRouter()
        self.router.add_api_route("/api/stt", self.stt, methods=["POST"])
        self.slack_sdk = SlackSDK()
        self.gpt_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),)


    def stt(
        self, 
        request_body: dict
        ):
        print("GPT_MODEL:", request_body["gpt_model"])
        print("MESSAGES:", request_body["messages"])
        print("LANGUAGE:", request_body["language"])
        print("AUDIO:", request_body["upload_data_path"])

        language_dict = {
            "한국어": "ko",
            "영어": "en",
            "자동": None
        }

        speech_tool = Speech(
            save_dir=request_body["upload_data_path"],
            language=language_dict[request_body["language"]]
            )

        speech_tool.video_list = multi_ext_glob(request_body["upload_data_path"], request_body["video_ext_list"], recursive=True)
        speech_tool.audio_list = multi_ext_glob(request_body["upload_data_path"], request_body["audio_ext_list"], recursive=True)
        for audio in speech_tool.audio_list:
            speech_tool.convert_to_wav(audio)
        speech_tool.wav_list = multi_ext_glob(request_body["upload_data_path"], ["wav"], recursive=True)
        print(f"[*]\tVIDEO EXTENSIONS: {request_body['video_ext_list']}\n\tLENGTH OF VIDEOS: {len(speech_tool.video_list)}")
        print(f"[*]\tAUDIO EXTENSIONS: {request_body['audio_ext_list']}\n\tLENGTH OF AUDIOS: {len(speech_tool.audio_list)}")
        print(f"[*]\TARGET EXTENSIONS: ['wav']\n\tLENGTH OF WAVS: {len(speech_tool.wav_list)}")
    
        whisper_result = speech_tool.run()
        request_body["messages"].append({"role": "user", "content": whisper_result[0]["text"]})

        response = self.gpt_client.chat.completions.create(
            model=request_body["gpt_model"],
            messages=request_body["messages"]
        )
        print("[*] CHATGPT RESPONSE:", response)

        print("[*] DONE ARCHIVING", request_body["upload_data_path"])
        
        print("response.choices[0].message.content", response.choices[0].message.content)
        print("FILE EXISTS:", os.listdir(request_body["upload_data_path"]))
        # print(f"PAYLOAD:\n\tmessage={response.choices[0].message.content}\n\tfile_path={os.path.join(request_body['upload_data_path'], 'archive.zip')}\n\tchannel={request_body['slack_id']}")
        # os.system(f"cp {os.path.join(request_body['upload_data_path'], 'archive.zip')} .")
        self.slack_sdk.send_message_multiple_files(
            message=response.choices[0].message.content,
            file_path_list=[os.path.join(request_body["upload_data_path"], filename) for filename in os.listdir(request_body["upload_data_path"])],
            channel=request_body["slack_id"]
        )

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
    # xtts = XTTS()
#     minio = minio_api.MinIO()
    # inference_api = InferenceRequest(xtts, minio)
    inference_api = InferenceRequest()
    inference_api.runserver()
