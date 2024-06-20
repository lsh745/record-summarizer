import os
import time
from utils import multi_ext_glob, ext_conversion
from whisper_stt import WhisperSTT
from annote import Annotation


class Speech:
    def __init__(
        self,
        save_dir: str = "/app/data", # MOVE
        axis: int = -1,
        n_mels: int = 128,
        length: int = 480000,
        model: str = "large",
        language: str = None,

        pipeline_model: str = "pyannote/speaker-diarization-3.1",
        use_auth_token: str = "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"        
        ):
        print("[+] INITIALIZING MAIN")
        start = time.time()

        self.save_dir = save_dir
        self.audio_list = []

        self.axis = axis
        self.n_mels = n_mels
        self.length = length
        self.model = model
        self.language = language
        
        self.pipeline_model = pipeline_model
        self.use_auth_token = use_auth_token

        print("[-] INITIALIZATION COMPLETE.\n\tTIME TAKEN:", time.time() - start)


    def convert_to_wav(self, target_file: str):
        print("[+] CONVERTING TO WAV")
        start = time.time()

        target_file_name, target_file_ext = os.path.splitext(target_file)
        if target_file_ext == "wav": return

        converted_file = target_file.replace(target_file_ext, "wav")
        ext_conversion(
            target_file, 
            os.path.join(self.save_dir, f"{target_file_name}.wav")
            )
        print("[-] CONVERSION COMPLETE.\n\tTIME TAKEN:", time.time() - start)

    
    def start_apps(self):
        self.whisper_stt = WhisperSTT(
            audio_list = self.wav_list,
            save_dir = self.save_dir,
            axis = self.axis,
            n_mels = self.n_mels,
            length = self.length,
            model = self.model,
            language = self.language
        )

        # self.annotation = Annotation(
        #     audio_list = self.wav_list,
        #     save_dir = self.save_dir,

        #     pipeline_model = self.pipeline_model,
        #     use_auth_token = self.use_auth_token
        # )


    def run(self):
        self.start_apps()

        whisper_result = self.whisper_stt.run()

        for result in whisper_result:
            for data in result:
                print(f"{data}: {result[data]}")

        # annotation_result = self.annotation.run()

        # for result in annotation_result:
        #     print(result)


        return whisper_result

if __name__ == "__main__":
    input_dir = "/app/data/240611"
    save_dir  = "/app/data/240611/result"


    test = MainProcess(
        language="ko"
        )

