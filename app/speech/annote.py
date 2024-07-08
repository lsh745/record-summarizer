import os
import time
import torch
import json
from pyannote.audio import Pipeline

class Annotation:
    def __init__(
        self,
        audio_list: list,
        pipeline_model: str = "pyannote/speaker-diarization-3.1",
        use_auth_token: str = "",
        save_dir: str = "/app/data"
        ):
        print("[+] INITIALIZING DIARIZATION")
        start = time.time()

        self.audio_list = audio_list
        self.save_dir = save_dir

        self.pipeline = Pipeline.from_pretrained(
        pipeline_model,
        use_auth_token=use_auth_token
        )

        self.pipeline.to(torch.device("cuda"))
        print("[-] INITIALIZATION COMPLETE.\n\tTIME TAKEN:", time.time() - start)


    def load_audio(self, audio_path: str):
        print("[+] LOADING AUDIO:", audio_path)
        start = time.time()
        self.audio_path = audio_path
        self.diarization = self.pipeline(audio_path)
        print("[-] LOADING COMPLETE.\n\tTIME TAKEN:", time.time() - start)


    def annote(self):
        print("[+] DIARIZATING")

        start = time.time()
        result = []

        for turn, _, speaker in self.diarization.itertracks(yield_label=True):
            # print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
            result.append({"start": turn.start, "stop": turn.end, "speaker": speaker})

        self.save_data(result)
        print("[-] DIARIZATION COMPLETE\n\tTIME TAKEN:", time.time() - start)
        return result


    def run(self):
        annotation_result = []

        for audio_path in self.audio_list:
            self.load_audio(audio_path = audio_path)
            annotation_result.append(self.annote())

        return annotation_result


    def save_data(self, result):
        print("[+] SAVING DATA")
        start = time.time()
        file_name = os.path.splitext(os.path.basename(self.audio_path))[0]       

        if not os.path.isdir(self.save_dir): 
            os.makedirs(self.save_dir)

        with open(os.path.join(self.save_dir, f"{file_name}_annotation.json"), "a", encoding='UTF-8') as f:
            f.write(json.dumps(result))

        with open(os.path.join(self.save_dir, f"{file_name}_annotation.txt"), "a") as f:
            f.write("".join([f"Start: {i['start']}, Stop: {i['stop']}, Speaker: {i['speaker']}" for i in result]))

        print("[+] DONE SAVING\n\tTIME TAKEN:", time.time() - start)



if __name__ == "__main__":
    annotation = Annotation(["/app/data/0603_chairman/0603-01.wav"])
    print(annotation.run())