import os

from helper_bot import HelperBot
from init_config import load_config

if __name__ == "__main__":
    load_config("config.env")
    load_config("parser_config.env")

    KEY = os.getenv("KEY")
    OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY")
    ADMIN_LIST = os.getenv("ADMIN_LIST").split(";")
    IMPORTANT_PATHS = os.getenv("IMPORTANT_PATHS").split(";")

    bot = HelperBot(KEY, ADMIN_LIST, IMPORTANT_PATHS, OPEN_ROUTER_KEY)
    bot.start()
