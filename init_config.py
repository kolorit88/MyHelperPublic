import os
from dotenv import load_dotenv

def load_config(name: str):
    path = os.getcwd() + f"/{name}"
    if os.path.exists(os.getcwd() + f"/{name}"):
        load_dotenv(dotenv_path=path, override=True)
        print("config loaded")
        return True
    print("config not loaded")
    return False
