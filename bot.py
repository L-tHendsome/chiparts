import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)  # ИСПРАВЛЕНО: __name__ вместо name

BOT_TOKEN = os.getenv('BOT_TOKEN', '8218450565:AAFDSOHTUWidvp-gIHHIrx_AB2z8iCMfUTg')
ADMIN_CHAT_IDS = os.getenv('ADMIN_CHAT_IDS', '-5264176031').split(',')

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_car_brand = State()
    waiting_for_car_model = State()
    waiting_for_part_name = State()
    waiting_for_comment = State()

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить заявку")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_brand_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Chery"), KeyboardButton(text="Geely")],
            [KeyboardButton(text="Great Wall"), KeyboardButton(text="Haval")],
            [KeyboardButton(text="Другой бренд"), KeyboardButton(text="❌ Отменить заявку")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🆕 Оформить заявку")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = """
🚗 <b>ChiParts Bot</b> 🇨🇳

Здравствуйте! Я помогу вам оформить заявку на запчасти из Китая.

<b>Что я могу:</b>
✅ Оформить заявку на любые детали
✅ Подобрать запчасти для Chery, Geely, Great Wall, Haval
✅ Отправить заявку менеджеру магазина
✅ Уведомить о статусе обработки

Нажмите кнопку ниже, чтобы начать 👇
"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@dp.message(lambda message: message.text == "🆕 Оформить заявку")
async def start_order(message: types.Message, state: FSMContext):
    await message.answer("👤 Введите ваше имя и фамилию:", reply_markup=get_cancel_keyboard())
    await state.set_state(OrderStates.waiting_for_name)

@dp.message(lambda message: message.text == "❌ Отменить заявку")
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Заявка отменена.\nНажмите /start чтобы начать заново.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(OrderStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заявку":
        await cancel_order(message, state)
        return
    await state.update_data(name=message.text)
    await message.answer("📱 Введите ваш номер телефона:", reply_markup=get_cancel_keyboard())
    await state.set_state(OrderStates.waiting_for_phone)

@dp.message(OrderStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заявку":
        await cancel_order(message, state)
        return
    
    # Корректная очистка телефона от лишних символов (ИСПРАВЛЕНО)
    phone = message.text.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Валидация номера
    if len(phone) < 11 or not phone[1:].isdigit():
        await message.answer("⚠️ Неверный формат телефона. Пример: +79991234567", reply_markup=get_cancel_keyboard())
        return
    
    await state.update_data(phone=phone)
    await message.answer("🚗 Выберите марку авто:", reply_markup=get_brand_keyboard())
    await state.set_state(OrderStates.waiting_for_car_brand)

@dp.message(OrderStates.waiting_for_car_brand)
async def process_brand(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заявку":
        await cancel_order(message, state)
        return
    await state.update_data(car_brand=message.text)
    await message.answer("🚘 Модель и год выпуска (напр.: Tiggo 7 2022):", reply_markup=get_cancel_keyboard())
    await state.set_state(OrderStates.waiting_for_car_model)

@dp.message(OrderStates.waiting_for_car_model)
async def process_model(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заявку":
        await cancel_order(message, state)
        return
    await state.update_data(car_model=message.text)
    await message.answer("🔧 Название детали:", reply_markup=get_cancel_keyboard())
    await state.set_state(OrderStates.waiting_for_part_name)

@dp.message(OrderStates.waiting_for_part_name)
async def process_part(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заявку":
        await cancel_order(message, state)
        return
    await state.update_data(part_name=message.text)
    await message.answer(
        "💬 Дополнительно (VIN, фото, пожелания) или «Пропустить»:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Пропустить"), KeyboardButton(text="❌ Отменить заявку")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(OrderStates.waiting_for_comment)

@dp.message(OrderStates.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заявку":
        await cancel_order(message, state)
        return
    
    comment = "Без комментария" if message.text == "Пропустить" else message.text
    data = await state.get_data()
    data.update({
        'comment': comment,
        'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M"),
        'user_id': message.from_user.id,
        'username': message.from_user.username or "не указан",
        'first_name': message.from_user.first_name or "",
        'last_name': message.from_user.last_name or ""
    })
    
    # Формирование сообщения для админа (ИСПРАВЛЕНО: правильный синтаксис)
    admin_message = f"""🆕 <b>НОВАЯ ЗАЯВКА 📱 Telegram-бот</b> 🆕

⏰ {data['timestamp']}
🆔 @{data['username']} (ID: {data['user_id']})

👤 {data['name']}
📱 {data['phone']}
🚗 {data['car_brand']}
🚘 {data['car_model']}
🔧 {data['part_name']}
💬 {data['comment']}

━━━━━━━━━━━━━━━━━━━━
📞 Связаться: @{data['username']} или {data['phone']}"""
    
    sent_count = 0
    for admin_id in ADMIN_CHAT_IDS:
        admin_id = admin_id.strip()
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode="HTML"  # ИСПРАВЛЕНО: без лишнего пробела
            )
            sent_count += 1
            logger.info(f"✅ Заявка отправлена в группу {admin_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в группу {admin_id}: {e}")
    
    if sent_count == 0:
        await message.answer(
            "⚠️ Ошибка отправки заявки. Пожалуйста, попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Подтверждение пользователю
    await message.answer(
        f"✅ <b>Заявка принята!</b> ✅\n\n"
        f"Менеджер свяжется с вами в течение 15 минут по номеру {data['phone']}.\n\n"
        f"Быстрая связь: @ChiParts_bot",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    await asyncio.sleep(2)
    await message.answer(
        "Хотите оформить еще одну заявку?",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

async def main():
    logger.info("=" * 60)
    logger.info("🚀 Запуск Telegram-бота @ChiParts_bot")
    logger.info(f"🤖 Token: {BOT_TOKEN[:12]}...")
    logger.info(f"👥 Группа для заявок: {ADMIN_CHAT_IDS}")
    logger.info("=" * 60)
    
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот запущен: @{bot_info.username}")
        logger.info(f"   Ссылка: https://t.me/{bot_info.username}")
        
        # Отправка тестового сообщения в группу
        test_message = f"""✅ <b>Бот @ChiParts_bot запущен на Render!</b>

Статус: ✅ Работает нормально
Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Версия: 1.0.0"""
        
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id.strip(),
                    text=test_message,
                    parse_mode="HTML"
                )
                logger.info(f"✅ Тестовое сообщение отправлено в группу {admin_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки тестового сообщения в {admin_id}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о боте: {e}")
        logger.info("⚠️ Бот запущен, но не удалось получить информацию о username")
    
    await dp.start_polling(bot)

if __name__ == "__main__":  # ИСПРАВЛЕНО: правильная проверка
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")