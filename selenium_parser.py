from selenium.webdriver.common.by import By
from time import sleep

from selenium.webdriver.support.select import Select
from seleniumbase import Driver


# sb_install.py -> DRIVER_DIR
# browser_launcher -> LOCAL_CHROMEDRIVER; LOCAL_UC_DRIVER


class SeleniumParserKemGU:
    def __init__(self, login, password, ui, study_range="2024-2025", quantity=6, invisible=False):
        self.ui = ui
        self.url = 'https://eios.kemsu.ru/a/eios'
        self.wb = Driver(uc=True, page_load_strategy='none', headless2=invisible)

        self.wb.get(self.url)
        self.wb.implicitly_wait(10)

        self.login = login
        self.password = password
        self.study_range = study_range
        self.quantity = quantity

    async def start(self):
        data = []
        await self.ui.send_message("Попытка войти в аккаунт...")
        if self.login_to_account():
            await self.ui.send_message("Успешный вход в аккаунт")
            await self.ui.send_message("Открываем страницу с дисциплинами...")
            if self.open_main_page():
                await self.ui.send_message("Страница открыта")
                await self.ui.send_message("Выбираем промежуток обучения...")
                if self.select_current_study_year():
                    await self.ui.send_message(f"Успешно выбран промежуток {self.study_range}")
                    await self.ui.send_message("Начинаем парсить страницы...")

                    data = await self.parsing_from_end_of_list()
                    if data:
                        await self.ui.send_message("Данные собраны")
                        print(data)
                    else:
                        await self.ui.send_message("Не удалось собрать данные")
        self.exit()
        return data

    def login_to_account(self):
        try:
            while True:
                sleep(0.5)
                try:
                    login_input = self.wb.find_element(By.CSS_SELECTOR, "input[name='username']")
                    password_input = self.wb.find_element(By.CSS_SELECTOR, "input[name='password']")

                    login_input.clear()
                    password_input.clear()

                    login_input.send_keys(self.login)
                    password_input.send_keys(self.password)

                    try:
                        while True:
                            submit_button = self.wb.find_element(By.CSS_SELECTOR, "button[type='submit']")
                            submit_button.click()
                            break
                    except:
                        pass

                    while True:
                        try:
                            if self.wb.current_url == "https://eios.kemsu.ru/a/eios/personal-area":
                                return True
                        except:
                            pass

                except:
                    pass

        except Exception as ex:
            print(ex)
            self.exit()
            return False

    def open_main_page(self):
        try:
            self.wb.get("https://xiais.kemsu.ru/proc/stud?backToNewEios=https://eios.kemsu.ru/a/eios/personal-area")
            while True:
                if (self.wb.current_url in ["https://xiais.kemsu.ru/proc/stud/index.shtm",
                                            "https://xiais.kemsu.ru/proc/stud/?backToNewEios=https://eios.kemsu.ru/a/eios/personal-area"]):
                    return True
        except Exception as ex:
            print(ex)
            self.exit()
            return False

    def select_current_study_year(self):
        while True:
            try:
                sleep(0.5)
                select_element = Select(self.wb.find_element(By.ID, 'studyYearFilter'))
                select_element.select_by_value(self.study_range)
                if select_element.all_selected_options[0].get_attribute("value") == self.study_range:
                    return True
            except:
                pass

    async def parsing_from_end_of_list(self):
        disciplines_list = self._parse_last_disciplines(self.quantity)

        all_disciplines_result = []
        for i in range(len(disciplines_list)):
            if i == self.quantity:
                break
            all_disciplines_result.append(self._get_info_from_discipline_page(disciplines_list[i]))
            await self.ui.send_message(f"{i + 1}/{self.quantity}")
            disciplines_list = self._parse_last_disciplines(self.quantity)

        return all_disciplines_result

    def format_data(self, data: list) -> str:
        """
        Форматирует список данных преподавателей в красивую текстовую таблицу
        """
        result = []

        for item in data:
            # Пропускаем строки с ошибками
            if isinstance(item, str) and item.startswith('error'):
                continue

            if not isinstance(item, dict):
                continue

            # Форматируем основную информацию о предмете
            subject_info = (
                f"📚 {item.get('name', 'Название не указано')}\n"
                f"👨‍🏫 Преподаватель: {item.get('teacher', 'Не указан')}\n"
                f"🏷 Тип: {item.get('type', 'Не указан')}\n"
                f"📅 Год: {item.get('year_range', 'Не указан')}\n"
            )

            # Форматируем задания
            tasks = item.get('teacher_tasks', [])
            if tasks:
                task_lines = []
                for task in tasks:
                    status_icon = "✅" if task.get('status') == 'Просмотрено' else "❌"
                    task_line = (
                        f"  {status_icon} {task.get('task_name', 'Без названия')}\n"
                        f"  💬 Комментарий: {task.get('comment', 'Нет комментария')}\n"
                        f"  ⏰ Срок: {task.get('datetime', 'Не указан').strip() or 'Не указан'}\n"
                    )
                    task_lines.append(task_line)

                tasks_info = "📝 Задания:\n" + "\n".join(task_lines)
            else:
                tasks_info = "📝 Задания отсутствуют\n"

            result.append(subject_info + tasks_info + "\n" + "─" * 40 + "\n")

        return "\n".join(result) if result else "Нет данных о предметах"

    def _get_info_from_discipline_page(self, discipline_tr_elem):
        try:
            sleep(1)
            param_list = list(discipline_tr_elem.find_elements(By.TAG_NAME, 'td'))
            discipline_dict = dict()

            if param_list:
                discipline_dict["teacher_tasks"] = []
                self._add_td_or_default("name", param_list[1], "error", discipline_dict)
                self._add_td_or_default("type", param_list[2], "error", discipline_dict)
                self._add_td_or_default("year_range", param_list[3], "error", discipline_dict)
                self._add_td_or_default("teacher", param_list[6], "error", discipline_dict)

            button = param_list[-1].find_element(By.TAG_NAME, 'input')
            button.click()
        except:
            return "error (parse button)"

        try:
            sleep(0.5)
            rows_list = list((self.wb.find_elements(By.CSS_SELECTOR, "table[class='tbl']")[1]
                              .find_elements(By.TAG_NAME, "tr")))[3:]
        except:
            return "error (parse table)"

        try:
            for row_tr in rows_list:
                teacher_task = dict()
                try:
                    param_td_list = list(row_tr.find_elements(By.TAG_NAME, 'td'))
                except:
                    param_td_list = []

                if param_td_list:
                    param_td_list = param_td_list[::-1][1:]

                    if param_td_list[0].text.lower() in ["просмотрено", "не просмотрено", "редактируется",
                                                         "отправлено на доработку"]:
                        self._add_td_or_default("task_name", param_td_list[-1], "error", teacher_task)
                        self._add_td_or_default("comment", param_td_list[-3], "error", teacher_task)
                        self._add_td_or_default("datetime", param_td_list[-4], "error", teacher_task)
                        self._add_td_or_default("status", param_td_list[0], "error", teacher_task)
                        discipline_dict["teacher_tasks"].append(teacher_task)

            self.wb.get("https://xiais.kemsu.ru/proc/stud/course_st/index.htm")
            if len(self._parse_last_disciplines(self.quantity)) == self.quantity:
                return discipline_dict
        except:
            return "error (parse discipline page)"
        return discipline_dict

    @staticmethod
    def _add_td_or_default(key_to_add, td_elem, default: str, dict_to_add: dict):
        try:
            dict_to_add[key_to_add] = td_elem.text
        except:
            dict_to_add[key_to_add] = default

    def _parse_last_disciplines(self, disciplines_quantity):
        while True:
            sleep(0.5)
            try:
                disciplines_list = list((self.wb.find_elements(By.CSS_SELECTOR, "table[class='tbl']")[1]
                                         .find_elements(By.TAG_NAME, 'tr')))[::-1]
                for elem in disciplines_list:
                    tmp = elem.text
                break
            except:
                pass
        return disciplines_list

    def exit(self):
        self.wb.close()
        self.wb.quit()

# добавить таймауты
