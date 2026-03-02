from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

router = Router()

MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📋 Очередь", style="primary"),
            KeyboardButton(text="📅 Расписание", style="success"),
        ],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

HELP_TEXT = (
    "<b>Команды бота:</b>\n\n"
    "/caption — Показать/изменить подпись\n"
    "/caption &lt;текст&gt; — Задать новую подпись (HTML)\n"
    "/queue — Очередь постов с управлением\n"
    "/schedule — Настройка расписания\n"
    "/next — Следующий пост и время публикации\n"
    "/publish — Опубликовать следующий пост сейчас\n"
    "/pause — Пауза публикаций\n"
    "/resume — Возобновить публикации\n"
    "/stats — Статистика\n\n"
    "Отправьте фото или видео — бот добавит в очередь."
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я бот для отложенного постинга в канал.\n\n"
        "Пересылайте или отправляйте мне фото/видео — я добавлю их в очередь "
        "и опубликую по расписанию.\n\n" + HELP_TEXT,
        reply_markup=MAIN_KB,
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()
