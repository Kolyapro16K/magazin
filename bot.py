import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Общий банк", callback_data='common_bank')],
        [InlineKeyboardButton("👤 Вова", callback_data='vova')],
        [InlineKeyboardButton("👤 Коля", callback_data='kolya')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🏦 Добро пожаловать в банковскую систему!\nВыберите раздел:",
        reply_markup=reply_markup
    )

# Обработка нажатий
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['last_action'] = query.data
    
    if query.data == 'common_bank':
        keyboard = [
            [InlineKeyboardButton("➕ Добавить", callback_data='add_money')],
            [InlineKeyboardButton("➖ Вычесть", callback_data='subtract_money')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"💰 Общий банк\nБаланс: {data['common_bank']} руб.\n\n"
            f"Выберите действие:",
            reply_markup=reply_markup
        )
    
    elif query.data == 'add_money':
        context.user_data['transaction_type'] = 'add'
        await query.edit_message_text(
            f"💰 Общий банк\nБаланс: {data['common_bank']} руб.\n\n"
            f"✏️ Введите сумму, которую хотите добавить:\n"
            f"(например: 1000)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к банку", callback_data='common_bank')]
            ])
        )
    
    elif query.data == 'subtract_money':
        context.user_data['transaction_type'] = 'subtract'
        await query.edit_message_text(
            f"💰 Общий банк\nБаланс: {data['common_bank']} руб.\n\n"
            f"✏️ Введите сумму, которую хотите вычесть:\n"
            f"(например: 500)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к банку", callback_data='common_bank')]
            ])
        )
    
    elif query.data == 'vova':
        await query.edit_message_text(
            f"👤 Вова\nБаланс: {data['vova']} руб.\n\n"
            f"Баланс корректируется автоматически.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
            ])
        )
    
    elif query.data == 'kolya':
        await query.edit_message_text(
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
        await query.edit_message_text(
            "🏦 Банковская система\nВыберите раздел:",
            reply_markup=reply_markup
        )

# Обработчик текстовых сообщений
async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data
    text = update.message.text.strip()
    
    transaction_type = context.user_data.get('transaction_type')
    if not transaction_type:
        await update.message.reply_text(
            "❌ Сначала выберите действие в разделе 'Общий банк'."
        )
        return
    
    try:
        amount = int(text)
        if amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть положительным числом!")
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
        
        await update.message.reply_text(
            f"✅ {action} {amount} руб.\n\n"
            f"📊 Текущие балансы:\n"
            f"💰 Общий банк: {data['common_bank']} руб.\n"
            f"👤 Вова: {data['vova']} руб.\n"
            f"👤 Коля: {data['kolya']} руб."
            f"{warning}",
            reply_markup=reply_markup
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректное число!\nПример: 1000"
        )

# Обработчик неизвестных команд
async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Неизвестная команда.\nИспользуйте /start"
    )

async def main():
    token = "8814586295:AAGND5Un2doDdOFvISKgg2M_3A744dKHbhc"
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input))
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
    
    print("Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
