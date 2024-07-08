import os
from glob import glob
from pydub import AudioSegment
import zipfile


def multi_ext_glob(
    dir: str,
    ext_list: list,
    recursive: bool = False
    ):
    data = []
    # [data.extend(glob(path.join(dir, f'*.{ext}'), recursive=recursive)) for ext in ext_list]
    for ext in ext_list:
        temp_path = os.path.join(dir, f'*.{ext}')
        print("EXT:", ext, "TEMP_PATH:", temp_path)  
        data.extend(glob(temp_path, recursive=recursive))
    return data


def ext_conversion(
    input_file: str, 
    output_file: str,
    output_ext: str = "wav",
    verbose: bool = True
    ):
    if verbose: print(f"[*] CONVERTING {input_file} TO {output_file}")
    _, input_ext = os.path.splitext(input_file)
    sound = AudioSegment.from_file(input_file, format=input_ext[1:])
    file_handle = sound.export(output_file, format=output_ext)
    return file_handle


def archive_dir(
    directory: str="result",
    archive_name: str="output.zip"
    ):
    zip_path = os.path.join(directory, archive_name)

    print("AAAAAAAA", zip_path)
    zip_file = zipfile.ZipFile(zip_path, "w")
    for file in os.listdir(directory):
        print(file)
        if file == archive_name: break
        zip_file.write(os.path.join(directory, file), compress_type=zipfile.ZIP_DEFLATED)
    zip_file.close()
    print("압축 파일:", zip_path)


if __name__ == "__main__":
    input_dir = "/app/data/0605_chairman"
    audio_ext_list = ["mp4", "wav", "m4a"]
    result = multi_ext_glob(input_dir, audio_ext_list, recursive=True)
    print(result)