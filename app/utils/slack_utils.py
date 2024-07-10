import os
import logging
from slack_sdk import WebClient


class SlackSDK:
    def __init__(self):
        self.client = WebClient(os.environ["SLACK_BOT_TOKEN"])
        auth_test = self.client.auth_test()
        self.bot_user_id = auth_test["user_id"]
        print(f"App's bot user: {self.bot_user_id}")

    def get_user_dict(self) -> dict:
        user_dict = self.client.users_list()
        # print("User dict:", user_dict)
        return user_dict

    def send_message(
        self,
        channel: str,
        message: str
        ):
        new_message = self.client.chat_postMessage(
            channel=channel,
            text=message,
        )

    def send_message_file(
        self, 
        message: str,
        channel: str,
        file_path: str, 
        file_title: str, 
        filename: str 
        ):
        with open(file_path, encoding="latin_1") as f:
            divider = ""
            if file_path and file_title and filename:
                new_file = self.client.files_upload_v2(
                    title=file_title,
                    filename=filename,
                    filetype="zip",
                    content=f.read()
                )
                divider == "\n\n"

            file_url = new_file.get("file").get("permalink")
            self.send_message(
                channel=channel, 
                message=f"{message}{divider}{file_url}"
                )


    def send_message_multiple_files(
        self, 
        message: str,
        file_path_list: list,  
        channel: str
        ):
        message = f"{message}\n\nFile:"
        for file_path in file_path_list:
            filename = os.path.basename(file_path)
            # with open(file_path) as f:
            new_file = self.client.files_upload_v2(
                title=filename,
                filename=filename,
                # content=f.read()
                file=file_path
            )
            message += f" {new_file.get('file').get('permalink')}"
        
        self.send_message(
            channel=channel, 
            message=message
            )


if __name__ == "__main__":
    print(SlackSDK().get_user_dict())