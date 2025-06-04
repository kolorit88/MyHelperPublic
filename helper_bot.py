import asyncio
import os
import random
import shutil
import string

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, InputMediaPhoto, KeyboardButton, ParseMode
from aiogram.types import (ReplyKeyboardMarkup, CallbackQuery,
                           InlineKeyboardButton as Ikb, InlineKeyboardMarkup as Ikm)
from aiogram.utils import executor
from PIL import ImageGrab

from extension_emojis import EXTENSION_EMOJIS
from open_router_api import OpenRouterAPI
from selenium_parser import SeleniumParserKemGU
from utils import collect_all_paths, log_message
from random import choice


class ChatFilterMiddleware(BaseMiddleware):
    def __init__(self, admin_list: list):
        self.admin_list = admin_list
        print(admin_list)
        super().__init__()

    async def on_pre_process_message(self, message: Message, data: dict):
        if str(message.chat.id) not in self.admin_list:
            await message.answer("Ты не админ!")
            raise CancelHandler()
        log_message(message.from_user.id, message.from_user.username, message.text)


class HelperBot:
    def __init__(self, bot_key, admin_list, important_paths, open_router_key=None):
        self.admin_list = admin_list
        self.important_paths = important_paths
        self.api = OpenRouterAPI(open_router_key)

        self.bot_key = bot_key
        self.bot = Bot(token=bot_key)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(self.bot, storage=self.storage)

        self.dp.middleware.setup(ChatFilterMiddleware(self.admin_list))

        self.message_to_del = None

        if open_router_key is not None:
            self.ai_bot = OpenRouterAPI(open_router_key)

        with open("current_path.txt", "r", encoding="utf-8") as f:
            self.current_path = f.read()

        try:
            with open("phrases.txt", "r", encoding="utf-8") as f:
                self.phrases = f.read().split(";")
        except:
            self.phrases = []

        if self.current_path == "":
            self.current_path = f"C:\\Users\\{os.getlogin()}\\Desktop"

        self.stream_is_active = False
        self.stream_message = None

        @self.dp.message_handler(text=["/ping"])
        async def ping(message: Message):
            await message.answer("Бот работает")

        @self.dp.message_handler(text=["/start", "/menu", "/m"])
        async def start(message: Message):
            available_drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            paths = self.important_paths + available_drives
            print(paths)
            for path in paths:
                kb.add(KeyboardButton(f"/cd {path}\\"))

            await message.answer(f"Текущий путь: {self.current_path}", reply_markup=kb)

        @self.dp.message_handler(Text(startswith="/cd "))
        async def cd(message: Message):
            path = message.text.replace("/cd ", "", 1)
            print(path)

            if path == "..":
                full_path = "\\".join(self.current_path.split("\\")[:-1])
                if "\\" not in full_path:
                    full_path += "\\"
            elif ":" in path:
                full_path = path
            else:
                full_path = os.path.join(self.current_path, path)
            print(full_path)

            if os.path.isdir(full_path):
                self.current_path = full_path

            with open("current_path.txt", "w", encoding="utf-8") as f:
                f.write(self.current_path)

            await list_dir(message)

            #     await message.answer(f"{self.current_path}>")
            # else:
            #     await message.answer(f"Папки не существует: {path}")

        @self.dp.message_handler(Text(startswith="/ls"))
        async def list_dir(message: Message):
            try:
                if os.path.exists(self.current_path):
                    text, kb = self._list_directory_contents(self.current_path)
                    inl_kb = Ikm().add(Ikb(text="⬇️ Скачать папку", callback_data=f"download"))

                    await message.answer(f"<code>{self.current_path}</code>", parse_mode="html", reply_markup=kb)
                    await message.answer(f"{self.current_path}>\n" + text, parse_mode="html", reply_markup=inl_kb)

                else:
                    await message.answer(f"Путь не существует: {self.current_path}")

            except Exception as e:
                return await message.answer(f"Произошла ошибка: {e}")

        @self.dp.message_handler(Text(startswith="/get "))
        async def get_file(message: Message, download_this_folder=False):
            delete_file = False

            if not download_this_folder:
                path = message.text.replace("/get ", "", 1)

                if ":" not in path:
                    full_path_to_file = f"{self.current_path}\\{path}"
                else:
                    full_path_to_file = path
            else:
                full_path_to_file = self.current_path

            try:
                # Проверяем, существует ли путь
                if not os.path.exists(full_path_to_file):
                    await message.answer(f"Файл или папка'{full_path_to_file}' не существует.")
                    return

                # Проверяем, является ли путь файлом
                if os.path.isfile(full_path_to_file):
                    await message.answer(f"'{full_path_to_file}' отправка файла...")
                else:
                    await message.answer(f"'{full_path_to_file}' отправка архива...")

                if os.path.isdir(full_path_to_file):
                    delete_file = True
                    full_path_to_file = self._create_zip_from_folder(full_path_to_file)

                with open(full_path_to_file, 'rb') as file:
                    await self.bot.send_document(message.chat.id, file)

            except Exception as e:
                await message.answer(f"Произошла ошибка: {e}")

            try:
                if delete_file:
                    os.remove(full_path_to_file)
            except:
                pass

        @self.dp.message_handler(text=["/screen", "/sc"])
        async def send_screen_photo(message: Message):
            try:
                screenshot_path = self._take_screenshot()

                with open(screenshot_path, 'rb') as photo:
                    sent_message = await message.answer_photo(photo)

                os.remove(screenshot_path)

            except Exception as e:
                await message.answer(f"Произошла ошибка: {e}")

        @self.dp.message_handler(text=["/stream", "/st"])
        async def stream(message: Message):
            try:
                screenshot_path = self._take_screenshot()

                with open(screenshot_path, 'rb') as photo:
                    sent_message = await message.answer_photo(photo)

                os.remove(screenshot_path)

                self.stream_message = sent_message

                if not self.stream_is_active:
                    self.stream_is_active = True

                    await asyncio.create_task(
                        self._update_screenshot())

            except Exception as e:
                await message.answer(f"Произошла ошибка: {e}")

        @self.dp.message_handler(text=["/stop"])
        async def off_stream(message: Message):
            self.stream_is_active = False

        @self.dp.message_handler(text=["/login", "/winlog", "/wl", "/lw"])
        async def login_windows(message: Message):
            pass

        @self.dp.message_handler(Text(startswith=["/gpt ", "/ai", "/h"]))
        async def ask_ai(message: Message):
            if self.phrases:
                phrase = choice(self.phrases)
            else:
                phrase = "Обработка..."

            await message.answer(phrase)

            prompt = " ".join(message.text.split(" ")[1:])
            structure = str(collect_all_paths(self.important_paths, max_depth=2)).replace("\\\\", "\\")
            downloaded_file = None

            if message.photo:
                photo = message.photo[-1]
                file = await self.bot.get_file(photo.file_id)
                downloaded_file = await self.bot.download_file(file.file_path)

            with open("context.txt", "r", encoding="utf-8") as file:
                content = file.read()

            if len(content) > 5000:
                content = content[-5000:]

            result = self.api.message(
                f"""Ты помощник на моем личном пк. У меня есть список путей на моем компьютере, предоставленные тебе. Вот они: {structure}.
            Я могу как просто задавать любые вопросы, так и попросить найти что-то. Ты отправляешь пути только если тебя попросили найти что-то, перед путями которые ты мне отправишь, нужно ставить /get.
            Пример : /get C:\\path. Не добавляй кавычки или что-то подобное
            
            Вот контекст предыдущих сообщений:{content}
            Сейчас я написал тебе в чате: {prompt}""", photo=downloaded_file)

            if "/get " in result:
                result_for_send = "\n".join(
                    list(map(lambda x: (f"<code>{x}</code>" if "/get" in x else x), result.split("\n"))))
            else:
                result_for_send = result

            print(result)
            print(result_for_send)

            with open("context.txt", "w", encoding="utf-8") as file:
                file.write(content + f"\nЯ:{prompt}\nТы:{result}")

            await message.answer(result_for_send, parse_mode="HTML")

        @self.dp.message_handler(text=["/off", "/shutdown", "/sd"])
        async def shutdown_handler(message: Message):
            await message.answer("Выключить компьютер?",
                                 reply_markup=Ikm().add(Ikb(text="✅", callback_data="shutdown_confirm"),
                                                        Ikb(text="❌", callback_data="shutdown_cancel")))

        @self.dp.callback_query_handler(Text(startswith="shutdown_"))
        async def shutdown(callback: CallbackQuery):
            option = callback.data.replace("shutdown_", "", 1)
            try:
                self.message_to_del.delete()
            except:
                pass
            if option == "confirm":
                await callback.message.answer("Выключение...")
                try:
                    os.system('shutdown -s')
                except Exception as e:
                    await callback.message.answer(f"Ошибка при выключении: {e}")

        @self.dp.callback_query_handler(Text(startswith="download"))
        async def download_current_folder_handler(callback: CallbackQuery):
            await get_file(callback.message, download_this_folder=True)
            await callback.answer()

        @self.dp.message_handler(text=['/debts', '/dolgi', '/kemgu'])
        async def parse_debts(message: Message):
            parser = None
            try:
                await message.answer("Начинаю парсинг")

                parser = SeleniumParserKemGU(os.getenv('LOGIN'),
                                             os.getenv('PASSWORD'),
                                             quantity=int(os.getenv("DISCIPLINES_QUANTITY")),
                                             invisible=os.getenv("INVISIBLE") == 'True', ui=self)
                data = await parser.start()
                data = parser.format_data(data)
                await message.answer(data)

            except Exception as e:
                if parser is not None:
                    parser.exit()
                await message.answer(str(e))

    def start(self):
        executor.start_polling(self.dp, skip_updates=True)

    async def send_message(self, text):
        await self.bot.send_message(self.admin_list[0], text)

    def _take_screenshot(self):
        screenshot = ImageGrab.grab()
        screenshot_path = f"{random.randint(1, 1000000)}.png"
        screenshot.save(screenshot_path)
        return screenshot_path

    async def _update_screenshot(self):
        while self.stream_is_active:
            chat_id, message_id = self.stream_message.chat.id, self.stream_message.message_id
            print(chat_id, message_id)
            try:
                screenshot_path = self._take_screenshot()

                with open(screenshot_path, 'rb') as photo:
                    media = InputMediaPhoto(media=photo)

                    await self.bot.edit_message_media(media, chat_id, message_id)

                # Удаляем временный файл
                os.remove(screenshot_path)
            except Exception as e:
                print(f"Ошибка при обновлении скриншота: {e}")

            await asyncio.sleep(1)

        await self.stream_message.answer("Стрим прекращен!")

    def _list_directory_contents(self, path):
        try:
            items = os.listdir(path)
            kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

            result = []
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    result.append(f"🗂 <code>{item}</code>")  # Папка
                    kb.add(KeyboardButton(f"/cd {item}"))
                else:
                    _, extension = os.path.splitext(item)
                    extension = extension.lower()[1:]

                    # Выбираем смайлик из словаря или используем смайлик по умолчанию
                    emoji = EXTENSION_EMOJIS.get(extension, "📄")
                    result.append(f"{emoji} <code>{item}</code>")
                    result.sort(reverse=True, key=lambda x: (x[0], x[1]))

            kb.add(KeyboardButton("/cd .."))
            return "\n".join(result), kb

        except Exception as e:
            return f"Произошла ошибка: {e}"

    def _create_zip_from_folder(self, folder_path: str) -> str:
        try:
            # Создаем имя для архива
            archive_name = f"{os.path.basename(folder_path)}.zip"
            # Создаем ZIP-архив
            shutil.make_archive(os.path.splitext(archive_name)[0], 'zip', folder_path)
            return archive_name
        except Exception as e:
            raise Exception(f"Ошибка при создании архива: {e}")
