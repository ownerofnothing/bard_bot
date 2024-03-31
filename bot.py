from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
from gpt import GPT
import logging
from database import create_db, create_table, DB_NAME, execute_query

bot = TeleBot("7048776893:AAHa3WUKRKw1-zL77-eQwbjAsQYE7lNFbLk")
MAX_LETTERS = 30
gpt = GPT()
users_history = {}
current_options = {}
create_db(DB_NAME)
create_table('users')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)


def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    global current_options
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}! Я твой персональный помощник по дипломатии и психологии.",
                     reply_markup=create_keyboard(["/solve_task", '/help']))
    logging.info("Отправка приветственного сообщения")
    current_options[message.from_user.id] = {'subject': '', 'level': ''}


@bot.message_handler(commands=['help'])
def support(message):
    bot.send_message(message.from_user.id,
                     text="Чтобы приступить к решению проблемы: нажми /solve_task, а затем напиши свой вопрос",
                     reply_markup=create_keyboard(["/solve_task"]))


@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    bot.send_message(message.chat.id, "Выберите предмет:", reply_markup=create_keyboard(['психология','дипломатия']))
    bot.register_next_step_handler(message, choose_subject)
    logging.debug(f"Полученный текст от пользователя: {message.text}")


def choose_subject(message):
    global current_options
    bot.send_message(message.chat.id, "Выберите уровень сложности объяснения:", reply_markup=create_keyboard(['для новичка', 'для профессионала']))
    current_options[message.from_user.id]['subject'] = message.text
    bot.register_next_step_handler(message, choose_level)


def choose_level(message):
    global current_options
    bot.send_message(message.chat.id, "Сформулируйте свой вопрос:")
    current_options[message.from_user.id]['level'] = message.text
    bot.register_next_step_handler(message, get_promt)



def continue_filter(message):
    button_text = 'Продолжить решение'

    return message.text == button_text


@bot.message_handler(func=continue_filter)
def get_promt(message):
    global current_options
    user_id = message.from_user.id
    logging.debug(f"Полученный текст от пользователя: {message.text}")
    if message.content_type != "text":
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, get_promt)
        return
    user_request = message.text
    if gpt.count_tokens(user_request) > 30:
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, get_promt)
        return
    if (user_id not in users_history or users_history[user_id] == {}) and user_request == "Продолжить решение":
        bot.send_message(user_id, "Чтобы продолжить решение, сначала нужно отправить текст запроса")
        bot.send_message(user_id, "Напиши новый вопрос:")
        bot.register_next_step_handler(message, get_promt)
        return
    if user_id not in users_history or users_history[user_id] == {}:
        if user_id not in current_options or current_options[user_id]['subject'] not in ['психология', 'дипломатия'] or current_options[user_id]['level'] not in ['для новичка', 'для профессионала']:
            bot.send_message(user_id, 'Вы не зарегистрированы или не выбрали уровень сложности объяснения/предмет.')
            start(message)
            return
        if current_options[user_id]['subject'] in ['психология', 'дипломатия']:
            cur_subject = current_options[user_id]['subject'][:-1] + 'и'
        if current_options[user_id]['level'] in ['для новичка', 'для профессионала']:
            cur_level = 'как' + current_options[user_id]['level']
        users_history[user_id] = {
            'system_content': f"Ты - дружелюбный помощник по {cur_subject}. Давай ответ {cur_level}",
            'user_content': user_request,
            'assistant_content': " "
        }
    promt = gpt.make_promt(users_history[user_id])
    resp = gpt.send_request(promt)

    answer = "Позже здесь будет реальное решение, а пока что так :)"
    answer = gpt.process_resp(resp)
    execute_query(DB_NAME,f'INSERT INTO users(user_id, subject, level, task, answer) VALUES ({user_id}, "{cur_subject}", "{cur_level}", "{user_request}", "{answer[1]}")')
    users_history[user_id]['assistant_content'] += answer[1]
    bot.send_message(
        user_id,
        text=users_history[user_id]['assistant_content'],
        reply_markup=create_keyboard(["Продолжить решение", "Завершить решение"])
    )


def end_filter(message):
    return message.text == 'Завершить решение'


@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    logging.debug(f"Полученный текст от пользователя: {message.text}")
    user_request = message.text
    user_id = message.from_user.id
    bot.send_message(user_id, "Текущие решение завершено")
    users_history[user_id] = {}
    solve_task(message)
    if (user_id not in users_history or users_history[user_id] == {}) and user_request == "Продолжить решение":
        bot.send_message(user_id, "Чтобы продолжить решение, сначала нужно отправить текст запроса")
        bot.send_message(user_id, "Напиши новый вопрос:")
        bot.register_next_step_handler(message, get_promt)
        return


@bot.message_handler(commands=['debug'])
def send_logs(message):
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


logging.info("Бот запущен")
bot.polling()
