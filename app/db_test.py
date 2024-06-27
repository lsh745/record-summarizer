from utils.database_utils import Database
from database.models import User, Job
import io
import os
import requests


if __name__ == "__main__":
    response = requests.request(
        method="POST",
        url=f"http://0.0.0.0:7527/api/get_users"
    )

    print(response.text)