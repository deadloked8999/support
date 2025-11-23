import re
import uuid
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes,
    JobQueue,
    ApplicationHandlerStop,
)
from database import (
    init_database,
    add_purchase,
    add_activation,
    update_activation_receipt,
    update_activation_kit,
    update_activation_serial_number,
    update_activation_serial_photo,
    update_activation_box_serial_number,
    update_activation_box_serial_photo,
    get_all_purchases,
    get_all_activations,
    get_statistics,
    mark_service_provided,
    get_activations_for_subscription_reminders,
    update_last_reminder_day,
)
from config import BOT_TOKEN, ACTIVATION_PRICE, ACTIVATION_PRICE_TON, PAYMENT_PHONE, PROVIDER_TOKEN, ADMIN_IDS, ADMIN_PASSWORD, SERIAL_NUMBER_EXAMPLE


WAITING_PHONE_PURCHASE, WAITING_NAME_PURCHASE = range(2)
WAITING_PHONE_ACTIVATE, WAITING_NAME_ACTIVATE, WAITING_SERIAL, WAITING_SERIAL_PHOTO, WAITING_BOX_SERIAL, WAITING_BOX_SERIAL_PHOTO, WAITING_KIT = range(5, 12)
WAITING_ADMIN_PASSWORD = 15


def normalize_phone(phone):
    phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if phone.startswith('8') and len(phone) == 11:
        phone = '+7' + phone[1:]
    elif not phone.startswith('+7'):
        if phone.startswith('7') and len(phone) == 11:
            phone = '+7' + phone[1:]
        else:
            phone = '+7' + phone
    return phone


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"DEBUG: start command received from user {update.effective_user.id}")
    try:
        # Очищаем все состояния ConversationHandler для этого пользователя
        context.user_data.clear()
        print(f"DEBUG: user_data cleared for user {update.effective_user.id}")
        
        welcome_text = (
            "Добро пожаловать! 👋\n\n"
            "Это техподдержка по активации терминалов Starlink. "
            "Я помогу вам купить терминал или активировать уже имеющееся устройство.\n\n"
            "Выберите нужное действие:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛒 Купить терминал", callback_data="buy")],
            [InlineKeyboardButton("⚙️ Активировать", callback_data="activate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        print(f"DEBUG: start message sent to user {update.effective_user.id}")
        
        # Останавливаем дальнейшую обработку
        raise ApplicationHandlerStop()
    except ApplicationHandlerStop:
        raise
    except Exception as e:
        print(f"Ошибка в start: {e}")
        import traceback
        traceback.print_exc()
        raise ApplicationHandlerStop()


async def button_callback_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Для покупки терминала мне нужна ваша информация.\n\n"
        "Пожалуйста, введите ваш номер телефона (формат: 8XXXXXXXXXX или +7XXXXXXXXXX):"
    )
    return WAITING_PHONE_PURCHASE


async def button_callback_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Для активации терминала мне нужна ваша информация.\n\n"
        "Пожалуйста, введите ваш номер телефона (формат: 8XXXXXXXXXX или +7XXXXXXXXXX):"
    )
    return WAITING_PHONE_ACTIVATE


async def handle_phone_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = normalize_phone(update.message.text)
    context.user_data['phone'] = phone
    await update.message.reply_text("Теперь введите ваше имя:")
    return WAITING_NAME_PURCHASE


async def handle_name_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user_id = update.effective_user.id
    phone = context.user_data['phone']
    
    add_purchase(user_id, phone, name)
    
    await update.message.reply_text(
        "Спасибо! Мы с вами свяжемся. ✅"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def handle_phone_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = normalize_phone(update.message.text)
    context.user_data['phone'] = phone
    await update.message.reply_text("Теперь введите ваше имя:")
    return WAITING_NAME_ACTIVATE


async def handle_name_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user_id = update.effective_user.id
    phone = context.user_data['phone']
    
    activation_id = add_activation(user_id, phone, name)
    context.user_data['activation_id'] = activation_id
    context.user_data['name'] = name
    context.user_data['phone'] = phone
    
    message_text = (
        "Спасибо за доверие! Для активации от Вас нужен серийный номер "
        "(написан на ножке после букв SN) + фото серийного номера "
        "(чтобы исключить риск активации чужого устройства), прилагаем пример:"
    )
    
    photo_path_jpg = os.path.join(os.path.dirname(__file__), "images", "serial_number_example.jpg")
    photo_path_png = os.path.join(os.path.dirname(__file__), "images", "serial_number_example.png")
    
    photo_sent = False
    if os.path.exists(photo_path_jpg):
        try:
            with open(photo_path_jpg, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=message_text
                )
            photo_sent = True
        except Exception as e:
            print(f"Ошибка отправки фото JPG: {e}")
    
    if not photo_sent and os.path.exists(photo_path_png):
        try:
            with open(photo_path_png, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=message_text
                )
            photo_sent = True
        except Exception as e:
            print(f"Ошибка отправки фото PNG: {e}")
    
    if not photo_sent:
        await update.message.reply_text(message_text)
    
    await update.message.reply_text(
        "Пожалуйста, введите серийный номер устройства (SN):"
    )
    return WAITING_SERIAL


async def handle_serial_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    serial_number = update.message.text.strip()
    user_id = update.effective_user.id
    
    update_activation_serial_number(user_id, serial_number)
    
    await update.message.reply_text(
        "Теперь отправьте фото серийного номера:"
    )
    return WAITING_SERIAL_PHOTO


async def handle_serial_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file_id = None
    
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text(
            "Пожалуйста, отправьте фото серийного номера (фото или документ)."
        )
        return WAITING_SERIAL_PHOTO
    
    update_activation_serial_photo(user_id, file_id)
    
    message_text = (
        "А также серийный номер с коробки терминала (написан после букв SN) + его фото, "
        "прилагаем пример:"
    )
    
    photo_path_jpg = os.path.join(os.path.dirname(__file__), "images", "serial_number_box_example.jpg")
    photo_path_png = os.path.join(os.path.dirname(__file__), "images", "serial_number_box_example.png")
    
    photo_sent = False
    if os.path.exists(photo_path_jpg):
        try:
            with open(photo_path_jpg, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=message_text
                )
            photo_sent = True
        except Exception as e:
            print(f"Ошибка отправки фото JPG: {e}")
    
    if not photo_sent and os.path.exists(photo_path_png):
        try:
            with open(photo_path_png, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=message_text
                )
            photo_sent = True
        except Exception as e:
            print(f"Ошибка отправки фото PNG: {e}")
    
    if not photo_sent:
        await update.message.reply_text(message_text)
    
    await update.message.reply_text(
        "Пожалуйста, введите серийный номер с коробки (SN):"
    )
    return WAITING_BOX_SERIAL


async def handle_serial_photo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, отправьте фото серийного номера (фото или документ). "
        "Вы также можете отменить операцию командой /cancel"
    )
    return WAITING_SERIAL_PHOTO


async def handle_box_serial_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    box_serial_number = update.message.text.strip()
    user_id = update.effective_user.id
    
    update_activation_box_serial_number(user_id, box_serial_number)
    
    await update.message.reply_text(
        "Теперь отправьте фото серийного номера с коробки:"
    )
    return WAITING_BOX_SERIAL_PHOTO


async def handle_box_serial_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file_id = None
    
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text(
            "Пожалуйста, отправьте фото серийного номера с коробки (фото или документ)."
        )
        return WAITING_BOX_SERIAL_PHOTO
    
    update_activation_box_serial_photo(user_id, file_id)
    
    # После получения фото коробки, переходим к оплате и запросу KIT
    payment_info = (
        f"Стоимость активации: {ACTIVATION_PRICE}₽\n\n"
        f"Оплатите на номер Сбербанк: {PAYMENT_PHONE}\n\n"
        "Теперь введите KIT номер устройства (буквы и цифры):"
    )
    
    await update.message.reply_text(payment_info)
    return WAITING_KIT


async def handle_box_serial_photo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, отправьте фото серийного номера с коробки (фото или документ). "
        "Вы также можете отменить операцию командой /cancel"
    )
    return WAITING_BOX_SERIAL_PHOTO


async def handle_kit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kit_number = update.message.text.strip()
    user_id = update.effective_user.id
    
    update_activation_kit(user_id, kit_number)
    
    await update.message.reply_text(
        "KIT номер сохранен. Пожалуйста, ожидайте. ⏳"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)
    
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    
    payment_info = (
        f"✅ Платеж успешно получен!\n\n"
        f"Сумма: {payment.total_amount / 1e9} {payment.currency}\n\n"
        "Теперь введите KIT номер устройства (буквы и цифры):"
    )
    
    update_activation_receipt(user_id, payment.telegram_payment_charge_id)
    
    await update.message.reply_text(payment_info)
    return WAITING_KIT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    context.user_data.clear()
    return ConversationHandler.END

async def start_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    welcome_text = (
        "Добро пожаловать! 👋\n\n"
        "Это техподдержка по активации терминалов Starlink. "
        "Я помогу вам купить терминал или активировать уже имеющееся устройство.\n\n"
        "Выберите нужное действие:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Купить терминал", callback_data="buy")],
        [InlineKeyboardButton("⚙️ Активировать", callback_data="activate")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return ConversationHandler.END


def is_admin(user_id):
    return user_id in ADMIN_IDS


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    context.user_data['admin_auth'] = True
    await update.message.reply_text(
        "🔐 Админ-панель\n\nВведите пароль для доступа:"
    )
    return WAITING_ADMIN_PASSWORD


async def admin_password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id) or not context.user_data.get('admin_auth'):
        return ConversationHandler.END
    
    password = update.message.text.strip()
    
    if password != ADMIN_PASSWORD:
        await update.message.reply_text("❌ Неверный пароль. Попробуйте еще раз:")
        return WAITING_ADMIN_PASSWORD
    
    context.user_data.pop('admin_auth', None)
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🛒 Покупки", callback_data="admin_purchases")],
        [InlineKeyboardButton("⚙️ Активации", callback_data="admin_activations")],
        [InlineKeyboardButton("📋 Активации (детально)", callback_data="admin_activations_detail")],
        [InlineKeyboardButton("📄 Экспорт в Excel", callback_data="admin_export_excel")],
        [InlineKeyboardButton("✅ Отметить как обработанную", callback_data="admin_mark_processed")],
        [InlineKeyboardButton("🚪 Выход из админ-панели", callback_data="admin_exit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 Админ-панель\n\nВыберите действие:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await query.message.reply_text("❌ У вас нет доступа.")
        return
    
    if query.data == "admin_stats":
        stats = get_statistics()
        text = (
            f"📊 Статистика\n\n"
            f"🛒 Всего покупок: {stats['total_purchases']}\n"
            f"⚙️ Всего активаций: {stats['total_activations']}\n\n"
            f"⏳ Ожидают оплаты: {stats['pending_activations']}\n"
            f"💳 Оплата подтверждена: {stats['payment_confirmed']}\n"
            f"✅ Завершено: {stats['completed_activations']}"
        )
        await query.message.reply_text(text)
    
    elif query.data == "admin_purchases":
        purchases = get_all_purchases()
        if not purchases:
            await query.message.reply_text("📭 Покупок пока нет.")
            return
        
        text = "🛒 Все покупки:\n\n"
        for purchase in purchases[:20]:
            purchase_id, uid, phone, name, created_at = purchase
            text += (
                f"ID: {purchase_id}\n"
                f"User ID: {uid}\n"
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Дата: {created_at[:19]}\n"
                f"{'─' * 30}\n"
            )
        
        if len(purchases) > 20:
            text += f"\n... и еще {len(purchases) - 20} записей"
        
        await query.message.reply_text(text)
    
    elif query.data == "admin_activations":
        activations = get_all_activations()
        if not activations:
            await query.message.reply_text("📭 Активаций пока нет.")
            return
        
        text = "⚙️ Все активации:\n\n"
        for act in activations[:20]:
            act_id, uid, phone, name, created_at, payment, receipt, serial_num, serial_photo, box_serial, box_photo, kit, status, service_provided, service_provided_at = act[:15]
            status_emoji = {
                'pending': '⏳',
                'payment_confirmed': '💳',
                'completed': '✅'
            }.get(status, '❓')
            
            service_status = "✅ Обработана" if service_provided else "⏳ Не обработана"
            
            text += (
                f"{status_emoji} ID: {act_id} | {status} | {service_status}\n"
                f"User ID: {uid}\n"
                f"Имя: {name} | {phone}\n"
                f"Дата: {created_at[:19]}\n"
            )
            if serial_num:
                text += f"SN устройство: {serial_num}\n"
            if box_serial:
                text += f"SN коробка: {box_serial}\n"
            if kit:
                text += f"KIT: {kit}\n"
            if service_provided_at:
                text += f"Обработана: {service_provided_at[:19]}\n"
            text += f"{'─' * 30}\n"
        
        if len(activations) > 20:
            text += f"\n... и еще {len(activations) - 20} записей"
        
        await query.message.reply_text(text)
    
    elif query.data == "admin_activations_detail":
        activations = get_all_activations()
        if not activations:
            await query.message.reply_text("📭 Активаций пока нет.")
            return
        
        text = "📋 Детальная информация по активациям:\n\n"
        for act in activations[:10]:
            act_id, uid, phone, name, created_at, payment, receipt, serial_num, serial_photo, box_serial, box_photo, kit, status, service_provided, service_provided_at = act[:15]
            text += (
                f"🔹 ID заявки: {act_id}\n"
                f"User ID: {uid}\n"
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Статус: {status}\n"
                f"Оплата получена: {'Да' if payment else 'Нет'}\n"
                f"SN устройство: {serial_num if serial_num else 'не указан'}\n"
                f"SN коробка: {box_serial if box_serial else 'не указан'}\n"
                f"KIT номер: {kit if kit else 'не указан'}\n"
                f"Услуга оказана: {'✅ Да' if service_provided else '❌ Нет'}\n"
                f"Дата создания: {created_at[:19]}\n"
            )
            if service_provided_at:
                start_date = datetime.fromisoformat(service_provided_at)
                end_date = start_date + timedelta(days=30)
                text += f"Дата начала активации: {service_provided_at[:19]}\n"
                text += f"Дата окончания подписки: {end_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            text += f"{'═' * 35}\n"
        
        if len(activations) > 10:
            text += f"\n... и еще {len(activations) - 10} записей"
        
        await query.message.reply_text(text)
    
    elif query.data == "admin_export_excel":
        await query.message.reply_text("📄 Генерирую Excel файл...")
        activations = get_all_activations()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Активации"
        
        headers = ["User ID", "Номер телефона", "Имя", "Дата заявки", "Услуга",
                   "SN устройство", "SN коробка", "KIT номер",
                   "Дата начала активации", "Дата окончания подписки"]
        ws.append(headers)
        
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        for act in activations:
            act_id, uid, phone, name, created_at, payment, receipt, serial_num, serial_photo, box_serial, box_photo, kit, status, service_provided, service_provided_at = act[:15]
            
            start_date_str = ""
            end_date_str = ""
            
            if service_provided_at:
                start_date = datetime.fromisoformat(service_provided_at)
                end_date = start_date + timedelta(days=30)
                start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
                end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            ws.append([
                uid,
                phone,
                name,
                created_at[:19],
                "Активация",
                serial_num if serial_num else "",
                box_serial if box_serial else "",
                kit if kit else "",
                start_date_str,
                end_date_str
            ])
        
        filename = f"activations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(filename)
        
        await query.message.reply_document(
            document=open(filename, 'rb'),
            filename=filename
        )
        
        os.remove(filename)
    
    elif query.data == "admin_mark_processed":
        activations = get_all_activations()
        if not activations:
            await query.message.reply_text("📭 Активаций пока нет.")
            return
        
        buttons = []
        for act in activations[:50]:
            act_id, uid, phone, name, created_at, payment, receipt, serial_num, serial_photo, box_serial, box_photo, kit, status, service_provided, service_provided_at = act[:15]
            if not service_provided:
                buttons.append([InlineKeyboardButton(
                    f"ID {act_id}: {name} ({phone})",
                    callback_data=f"mark_{act_id}"
                )])
        
        if not buttons:
            await query.message.reply_text("✅ Все заявки уже обработаны.")
            return
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.reply_text(
            "Выберите заявку для отметки как обработанную:",
            reply_markup=reply_markup
        )
    
    elif query.data.startswith("mark_"):
        activation_id = int(query.data.split("_")[1])
        if mark_service_provided(activation_id):
            await query.message.reply_text(f"✅ Заявка #{activation_id} отмечена как обработанная.")
        else:
            await query.message.reply_text(f"❌ Ошибка при обработке заявки #{activation_id}.")
    
    elif query.data == "admin_exit":
        welcome_text = (
            "👋 Вы вышли из админ-панели.\n\n"
            "Добро пожаловать! 👋\n\n"
            "Это техподдержка по активации терминалов Starlink. "
            "Я помогу вам купить терминал или активировать уже имеющееся устройство.\n\n"
            "Выберите нужное действие:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🛒 Купить терминал", callback_data="buy")],
            [InlineKeyboardButton("⚙️ Активировать", callback_data="activate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(welcome_text, reply_markup=reply_markup)
        return


def main():
    import sys
    sys.stdout.write("MAIN: Функция main() вызвана\n")
    sys.stdout.flush()
    sys.stderr.write("MAIN: Функция main() вызвана (stderr)\n")
    sys.stderr.flush()
    
    print("Инициализация базы данных...")
    try:
        init_database()
        print("База данных инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print("Создание Application...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        print("Application создан")
    except Exception as e:
        print(f"Ошибка при создании Application: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    purchase_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback_buy, pattern="^buy$")],
        states={
            WAITING_PHONE_PURCHASE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_purchase)
            ],
            WAITING_NAME_PURCHASE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_purchase)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start_fallback)
        ],
    )
    
    activation_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_callback_activate, pattern="^activate$"),
            MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
        ],
        states={
            WAITING_PHONE_ACTIVATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_activate)
            ],
            WAITING_NAME_ACTIVATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_activate)
            ],
            WAITING_SERIAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_serial_number)
            ],
            WAITING_SERIAL_PHOTO: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_serial_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_serial_photo_text)
            ],
            WAITING_BOX_SERIAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_box_serial_number)
            ],
            WAITING_BOX_SERIAL_PHOTO: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, handle_box_serial_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_box_serial_photo_text)
            ],
            WAITING_KIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_kit),
                MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start_fallback)
        ],
    )
    
    admin_password_handler_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_command)],
        states={
            WAITING_ADMIN_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_password_handler)
            ],
        },
        fallbacks=[],
    )
    
    async def check_subscriptions(context: ContextTypes.DEFAULT_TYPE):
        activations = get_activations_for_subscription_reminders()
        now = datetime.now()
        
        for act in activations:
            act_id, user_id, phone, name, service_provided_at, last_reminder_day = act
            
            if not service_provided_at:
                continue
            
            try:
                start_date = datetime.fromisoformat(service_provided_at)
                end_date = start_date + timedelta(days=30)
                days_left = (end_date - now).days
                
                if 1 <= days_left <= 5:
                    if last_reminder_day != days_left:
                        reminder_text = (
                            f"⏰ Напоминание о подписке\n\n"
                            f"Ваша подписка Starlink заканчивается через {days_left} день(дня/дней).\n"
                            f"Дата окончания: {end_date.strftime('%d.%m.%Y')}\n\n"
                            f"Пожалуйста, продлите подписку."
                        )
                        try:
                            await context.bot.send_message(chat_id=user_id, text=reminder_text)
                            update_last_reminder_day(act_id, days_left)
                        except Exception as e:
                            print(f"Ошибка отправки напоминания пользователю {user_id}: {e}")
            except Exception as e:
                print(f"Ошибка обработки активации {act_id}: {e}")
    
    try:
        print("Настройка job_queue...")
        job_queue = application.job_queue
        if job_queue:
            job_queue.run_repeating(check_subscriptions, interval=3600, first=10)
        print("job_queue настроен")
        
        print("Регистрация обработчиков...")
        # Группа -1 для команд (высший приоритет)
        application.add_handler(CommandHandler("start", start), group=-1)
        print("Обработчик /start зарегистрирован")
        
        # Группа 0 для остальных обработчиков
        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        application.add_handler(CallbackQueryHandler(admin_callback, pattern="^(admin_|mark_)"))
        application.add_handler(admin_password_handler_conv)
        application.add_handler(purchase_handler)
        application.add_handler(activation_handler)
        print("Все обработчики зарегистрированы")
        
        print("Бот запущен...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Ошибка при настройке обработчиков: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    import sys
    sys.stdout.write("START: Скрипт запущен\n")
    sys.stdout.flush()
    sys.stderr.write("START: Скрипт запущен (stderr)\n")
    sys.stderr.flush()
    
    print("START: __name__ == '__main__'")
    
    try:
        main()
    except Exception as e:
        error_msg = f"КРИТИЧЕСКАЯ ОШИБКА при запуске бота: {e}"
        print(error_msg)
        sys.stderr.write(error_msg + "\n")
        sys.stderr.flush()
        import traceback
        traceback.print_exc()
        traceback.print_exc(file=sys.stderr)
        raise

