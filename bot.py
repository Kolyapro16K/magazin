import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# Файл для хранения данных
DATA_FILE = 'bank_data.json'

# Инициализация данных
def init_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        data = {
            'common_bank': 0,
            'vova': 2000000,
            'kolya': 2000000
        }
        save_data(data)
        return data

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Загрузка данных
data = init_data()

# Обновление балансов
def update_personal_balances():
    global data
    if data['common_bank'] < 0:
        half_debt = abs(data['common_bank']) // 2
        data['vova'] = 2000000 - half_debt
        data['kolya'] = 2000000 - half_debt
        if data['vova'] < 0:
            data['vova'] = 0
        if data['kolya'] < 0:
            data['kolya'] = 0
    else:
        data['vova'] = 2000000
        data['kolya'] = 2000000
    save_data(data)

# Команда /start
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("💰 Общий банк", callback_data='common_bank')],
        [InlineKeyboardButton("👤 Вова", callback_data='vova')],
        [InlineKeyboardButton("👤 Коля", callback_data='kolya')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "🏦 Добро пожаловать в банковскую систему!\nВыберите раздел:",
        reply_markup=reply_markup
    )

# Обработка нажатий
def button_callback(update, context):
    query = update.callback_query
    query.answer()
    
    context.user_data['last_action'] = query.data
    
    if query.data == 'common_bank':
        keyboard = [
            [InlineKeyboardButton("➕ Добавить", callback_data='add_money')],
            [InlineKeyboardButton("➖ Вычесть", callback_data='subtract_money')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            f"💰 Общий банк\nБаланс: {data['common_bank']} руб.\n\n"
            f"Выберите действие:",
            reply_markup=reply_markup
        )
    
    elif query.data == 'add_money':
        context.user_data['transaction_type'] = 'add'
        query.edit_message_text(
            f"💰 Общий банк\nБаланс: {data['common_bank']} руб.\n\n"
            f"✏️ Введите сумму, которую хотите добавить:\n"
            f"(например: 1000)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к банку", callback_data='common_bank')]
            ])
        )
    
    elif query.data == 'subtract_money':
        context.user_data['transaction_type'] = 'subtract'
        query.edit_message_text(
            f"💰 Общий банк\nБаланс: {data['common_bank']} руб.\n\n"
            f"✏️ Введите сумму, которую хотите вычесть:\n"
            f"(например: 500)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к банку", callback_data='common_bank')]
            ])
        )
    
    elif query.data == 'vova':
        query.edit_message_text(
            f"👤 Вова\nБаланс: {data['vova']} руб.\n\n"
            f"Баланс корректируется автоматически.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ])
        )
    
    elif query.data == 'kolya':
        query.edit_message_text(
            f"👤 Коля\nБаланс: {data['kolya']} руб.\n\n"
            f"Баланс корректируется автоматически.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ])
        )
    
    elif query.data == 'back_to_menu':
        keyboard = [
            [InlineKeyboardButton("💰 Общий банк", callback_data='common_bank')],
            [InlineKeyboardButton("👤 Вова", callback_data='vova')],
            [InlineKeyboardButton("👤 Коля", callback_data='kolya')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            "🏦 Банковская система\nВыберите раздел:",
            reply_markup=reply_markup
        )

# Обработчик текстовых сообщений
def handle_amount_input(update, context):
    global data
    text = update.message.text.strip()
    
    transaction_type = context.user_data.get('transaction_type')
    if not transaction_type:
        update.message.reply_text(
            "❌ Сначала выберите действие в разделе 'Общий банк'."
        )
        return
    
    try:
        amount = int(text)
        if amount <= 0:
            update.message.reply_text("❌ Сумма должна быть положительным числом!")
            return
        
        if transaction_type == 'add':
            data['common_bank'] += amount
            action = "добавлено"
        elif transaction_type == 'subtract':
            data['common_bank'] -= amount
            action = "вычтено"
        
        update_personal_balances()
        context.user_data['transaction_type'] = None
        
        keyboard = [
            [InlineKeyboardButton("💰 Вернуться к банку", callback_data='common_bank')],
            [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        warning = ""
        if data['common_bank'] < 0:
            warning = f"\n⚠️ ВНИМАНИЕ: Общий банк в минусе на {abs(data['common_bank'])} руб."
        
        update.message.reply_text(
            f"✅ {action} {amount} руб.\n\n"
            f"📊 Текущие балансы:\n"
            f"💰 Общий банк: {data['common_bank']} руб.\n"
            f"👤 Вова: {data['vova']} руб.\n"
            f"👤 Коля: {data['kolya']} руб."
            f"{warning}",
            reply_markup=reply_markup
        )
        
    except ValueError:
        update.message.reply_text(
            "❌ Введите корректное число!\nПример: 1000"
        )

# Обработчик неизвестных команд
def handle_unknown(update, context):
    update.message.reply_text(
        "❌ Неизвестная команда.\nИспользуйте /start"
    )

def main():
    token = "8814586295:AAGND5Un2doDdOFvISKgg2M_3A744dKHbhc"
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_amount_input))
    dp.add_handler(MessageHandler(Filters.command, handle_unknown))
    
    print("Бот запущен...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
