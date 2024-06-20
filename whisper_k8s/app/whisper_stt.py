import whisper
import time
import os
import json

class WhisperSTT:
    def __init__(
        self,
        audio_list: list,
        save_dir: str = "/app/data",

        axis: int = -1,
        n_mels: int = 128,
        length: int = 480000,
        model: str = "large",
        language: str = None
        ):
        print("[+] INITIALIZING WHISPER STT")
        start = time.time()

        self.audio_list = audio_list
        self.save_dir = save_dir

        self.axis = axis
        self.n_mels = n_mels
        self.length = length
        self.model = model = whisper.load_model(model)
        self.language = language
        # self.options = whisper.DecodingOptions(language=language)

        print("[-] INITIALIZATION COMPLETE.\n\tTIME TAKEN:", time.time() - start)

    def load_audio(self, audio_path: str):
        print("[+] LOADING AUDIO:", audio_path)
        start = time.time()
        self.audio_path = audio_path
        self.audio = whisper.load_audio(audio_path)
        print("[-] LOADING COMPLETE.\n\tTIME TAKEN:", time.time() - start)
        print("[*] AUDIO SHAPE:", self.audio.shape)


    def save_data(self, result):
        print("[+] SAVING DATA")
        start = time.time()
        file_name = os.path.splitext(os.path.basename(self.audio_path))[0]       

        if not os.path.isdir(self.save_dir): 
            os.makedirs(self.save_dir)

        with open(os.path.join(self.save_dir, f"{file_name}_stt.json"), "a", encoding='UTF-8') as f:
            f.write(json.dumps(result))

        with open(os.path.join(self.save_dir, f"{file_name}_stt.txt"), "a") as f:
            f.write("".join([i["text"] for i in result["segments"]]))

        print("[+] DONE SAVING\n\tTIME TAKEN:", time.time() - start)



    def run_stt(self):
        print("[+] START STT")
        start = time.time()

        result = self.model.transcribe(self.audio, language=self.language)
        # print("[*] STT RESULT:", result)

        print("[+] DONE STT RUN\n\tTIME TAKEN:", time.time() - start)

        self.save_data(result)
        
        return result


    def run(self):
        stt_result = []

        for audio_path in self.audio_list:
            self.load_audio(audio_path = audio_path)
            stt_result.append(self.run_stt())

        return stt_result


if __name__ == "__main__":
    whisper_stt = WhisperSTT(["/app/data/0603_chairman/0603-01.m4a"])
    print(whisper_stt.run())