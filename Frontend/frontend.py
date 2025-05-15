#!/bin/python
# Frontend application
# TODO: +Реализовать базовый функционал бота
# TODO: +Реализовать функционал обращения к API backend
# TODO: +Реализовать получение текущей температуры со всех датчиков
# TODO: +Реализовать получение информации о конфигурации датчиков
# TODO: +Реализовать добавление и изменение датчиков
# TODO: +Реализовать получение текущей температуры с одного датчика
# TODO: Реализовать получение исторических данных с конкретного датчика 
#       за фиксированные промежутки (последний час, последнийе сутки, последняя неделя, последний месяц)
# TODO: +Реализовать удалени датчиков по IP
# TODO: Реализовать хранение данных о конматах и привязку датчиков к комнатах.

import httpx
import json
from io import BytesIO

import logging
import plotly.graph_objects as go
import plotly.io as pio
pio.kaleido.scope.mathjax = None
pio.renderers.default = 'png'

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

(
    MAIN_MENU,
    CURRENT_TEMP_ALL,
    CURRENT_TEMP_ONE,
    HISTORY_PERIOD,
    CONFIG,
    ADD_SENSOR_IP,
    ADD_SENSOR_PORT,
    ADD_SENSOR_OFFSET,
    ADD_SENSOR_ACTIVITY,
    ADD_SENSOR_CONFIRM,
    DEL_SENSOR_IP,
    DEL_SENSOR_CONFIRM
) = range(12)

BACKEND_BASE_URL = "http://localhost:22222"
TELEGRAM_TOKEN = "7582204566:AAHJZKOUcEzPiE03rH6rM9THWV7jrMEftwU"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO) #Надо понизить уровень логирования.
logger = logging.getLogger(__name__)

#Клавиатуры
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["1. Текущая температура", "2. История измерений"],
            ["3. Управление датчиками", "4. Помощь"],
        ],
        resize_keyboard=True,
    )

def current_temp_keyboard():
    return ReplyKeyboardMarkup(
        [["1.1 Со всех датчиков", "1.2 С конкретного датчика"], ["Назад"]],
        resize_keyboard=True,
    )

def sensors_control_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["3.1 Список датчиков", "3.2 Добавить датчик"],
            ["3.3 Удалить датчик", "Назад"]
        ],
        resize_keyboard=True
    )

def confirm_keyboard():
    return ReplyKeyboardMarkup(
        [["✅ Да","❌ Нет"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def period_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["За последний час", "За последний день\n(с 0 часов)"],
            ["За последние 24 часа","За последнюю неделю"],
            ["За последний месяц","Назад"]
         ],
         resize_keyboard=True,
         one_time_keyboard=True
    )

#Обработчики
async def start(update: Update, context):
    await update.message.reply_text(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU

async def current_temp_menu(update: Update, context):
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=current_temp_keyboard()
    )
    return CURRENT_TEMP_ALL 

async def handle_current_temp_all(update: Update, context):
    async with httpx.AsyncClient() as api_client:
        response = await api_client.get(BACKEND_BASE_URL + "/current_temp/")

    if response.status_code == 200:
        
        data = response.json()
        answer = ""
        for ip_address in data.keys():
            answer += f"IP адрес : {ip_address}:\n"
            for modbus_offset in data[ip_address].keys():
                temp = data[ip_address][modbus_offset].get("last_temperature_value", "N/A")
                answer += f" 🌡 {modbus_offset} : {temp} ℃\n\n"
        
        await update.message.reply_text(
            text=f"Показания всех датчиков:\n\n {"=" * 25}\n\n{answer}",
            reply_markup=main_menu_keyboard()
            )
    else:
        await update.message.reply_text(
            "❌ Не удалось получить данные!",
            reply_markup=main_menu_keyboard()
        )
    return MAIN_MENU

async def handle_current_temp_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите IP датчика и modbus offset через \":\"")
    return CURRENT_TEMP_ONE

async def handle_current_temp_one_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ip, modbus_offset = update.message.text.strip().split(':')
    except ValueError:
        await update.message.reply_text(
                f"⚠️ Не верно введены IP и modbus offset (пример: 192.168.1.1:100)",
                reply_markup=main_menu_keyboard()
            )
        return MAIN_MENU
    async with httpx.AsyncClient() as client:
        response = await client.get(url=f"{BACKEND_BASE_URL}/current_temp/")
    if response.status_code == 200:
        temp_value = response.json().get(ip, {}).get(modbus_offset, {}).get('last_temperature_value')
        if temp_value is not None:
            await update.message.reply_text(
                f"🌡 Показания датчика {ip}:{modbus_offset} = {temp_value} ℃",
                reply_markup=main_menu_keyboard()
            )
            return MAIN_MENU
        else:
            await update.message.reply_text(
                f"⚠️ Показания датчика {ip}:{modbus_offset} не найдены. ⚠️ ",
                reply_markup=main_menu_keyboard()
            )
            return MAIN_MENU
    else:
        await update.message.reply_text(
            f"❌ Возникла ошибка при получении данных",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Возвращаюсь в главное меню.",
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU

async def config_menu(update: Update, context):
    await update.message.reply_text(
        "Настрйока датчиков: ",
        reply_markup=sensors_control_keyboard()
    )
    return CONFIG

async def get_sensors_list(update: Update, context):
    async with httpx.AsyncClient() as client:
        api_response = await client.get(BACKEND_BASE_URL + "/config/")
    if api_response.status_code == 200:
        config = api_response.json()
        answer = "Список сенсоров в системе: \n\n"
        for sensor_ip in config.get("modbus_sensors").keys():
            answer += f"Сенсор {sensor_ip} :\n"
            answer += f" Активность : {config.get("modbus_sensors").get(sensor_ip).get("active")}\n"
            answer += f" Порт : {config.get("modbus_sensors").get(sensor_ip).get("tcp_port")}\n"
            answer += f" ModBus offsets : {config.get("modbus_sensors").get(sensor_ip).get("modbus_offsets")}\n\n"
        print(answer)
        await update.message.reply_text(
            str(answer),
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "Не удалось получить информацию!",
            reply_markup=main_menu_keyboard
        )
    return MAIN_MENU  

async def add_sensor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите IP адрес сенсора.")
    return ADD_SENSOR_IP

async def add_sensor_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ip = update.message.text.strip()
    if not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip.split('.')):
        await update.message.reply_text("IP адрес указан неверно. Проверьте! (напр. 192.168.1.1)")
        return ADD_SENSOR_IP
    context.user_data['ip'] = ip
    await update.message.reply_text("Введите номер порта (1-65535)")
    return ADD_SENSOR_PORT

async def add_sensor_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    port = update.message.text.strip()
    if not port.isdigit and 1 <= int(port) <= 65535:
        await update.message.reply_text("введен некорректный порт! Проверьте! (1-65635)")
        return ADD_SENSOR_PORT
    context.user_data["port"] = port
    await update.message.reply_text("Введите адрес или список адресов MODBUS (modbus offset). Список разделяйте запятыми \",\"(Напр. 100, 102, 104)")
    return ADD_SENSOR_OFFSET

async def add_sensor_offset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modbus_offsets_raw = update.message.text.strip().split(",")
    context.user_data["modbus_offsets"] = [int(offset.strip()) for offset in modbus_offsets_raw]
    await update.message.reply_text(
        f"Активировать датчик?",
        reply_markup=confirm_keyboard()
    )
    return ADD_SENSOR_ACTIVITY 

async def add_sensor_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    if answer.strip() == "✅ Да":
        context.user_data['sensor_activity'] = 'true'
    else:
        context.user_data['sensor_activity'] = 'false'
    await update.message.reply_text(
        f"""🔎 Подтвердите правильность введенных данных:\n\n IP Адрес: {context.user_data["ip"]}
Порт: {context.user_data["port"]}\n Список оффсетов: {context.user_data["modbus_offsets"]}
Датчик активен: {context.user_data["sensor_activity"]}
""",
        reply_markup=confirm_keyboard()
    )
    return ADD_SENSOR_CONFIRM

async def add_sensor_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        post_data = {
              "active": context.user_data['sensor_activity'],
              "ip_address": context.user_data['ip'],
              "tcp_port": context.user_data['port'],
              "modbus_offsets": context.user_data['modbus_offsets']
        }
        print(json.dumps(post_data, indent=4))
        response = await client.post(BACKEND_BASE_URL + "/sensor/", data=json.dumps(post_data))
    if response.status_code == 200: 
        await update.message.reply_text(
            f"✅ Датчик {context.user_data['ip']} успешно добавлен!",
        reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"❌ При добавлении датчика {context.user_data['ip']} произошла ошибка!",
        reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU

async def del_sensor_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вводим и записываем в user_data IP адрес сенсора для удаления
    """
    ip = update.message.text
    if ip == "3.3 Удалить датчик":
        await update.message.reply_text("Введите IP адрес датчика для удаления.")
        return DEL_SENSOR_IP
    elif not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip.split('.')):
        await update.message.reply_text("IP адрес указан неверно. Проверьте! (напр. 192.168.1.1)")
        return DEL_SENSOR_IP
    else:
        context.user_data['del_ip'] = ip
        await update.message.reply_text(
            f"Вы дествительн хотите удалить датчик {context.user_data['del_ip']}",
            reply_markup=confirm_keyboard()
        )
        return DEL_SENSOR_CONFIRM

async def del_sensor_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Функция вызывается после подтверждения удаления датчика. Выполняет API запрос для удаления датчика и возвращает нас в Главное Меню.
    """
    ip = context.user_data['del_ip']
    async with httpx.AsyncClient() as client:
        response = await client.delete(url=f"{BACKEND_BASE_URL}/sensor/{ip}")
    if response.status_code == 200:
        await update.message.reply_text(
            f"🗑️ Датчик {ip} успешно  удален.",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"❌ При удалении датчика {ip} возникла ошибка.",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU
    
async def build_plot(raw_data, period, ip, modbus) -> BytesIO:
    timestamps = [str(row.get('software_timestamp')) for row in raw_data]
    values = [row.get('temperature_value') for row in raw_data]
    
    #print(f"Timestamps - {timestamps}||| Len = {len(timestamps)}")
    #print(f"Values - {values} ||| Len = {len(values)}")

    plot = go.Figure(data=go.Scatter(
        x=timestamps,
        y=values,
        mode='lines+markers',
        line=dict(color='firebrick', width=2),
        marker=dict(size=8),
        name='Температура (°C)'
        ))
    plot.update_layout(
        title = "График температуры",
        xaxis_title='Время',
        yaxis_title='Температура (°C)',
        template='plotly_white'
        )
    
    file_name = f"plot_{period}_{ip}_{modbus}.html"
    with open(file_name, 'w') as html_file:
        plot.write_html(html_file)
    return file_name
    
async def get_hist_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    if message == "2. История измерений":
        await update.message.reply_text(
            "Введите адрес датчика в формате <IP адрес>:<modbus offset>. Например: 192.168.1.1:100",
        )
        return HISTORY_PERIOD
    elif "." in message and ":" in message:
        ip, modbus_offset = message.split(":")
        context.user_data["history_period_ip"] = ip
        context.user_data["history_period_modbus_offset"] = modbus_offset
        await update.message.reply_text(
            "Выберите период",
            reply_markup=period_keyboard()
        )
        return HISTORY_PERIOD
    elif message == "За последний час":
        context.user_data["history_period"] = "hour"
    elif message == "За последний день\n(с 0 часов)":
        context.user_data["history_period"] = "day"
    elif message == "За последние 24 часа":
        context.user_data["history_period"] = "24_hours"
    elif message == "За последнюю неделю":
        context.user_data["history_period"] = "week"
    elif message == "За последний месяц":
        context.user_data["history_period"] = "month"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACKEND_BASE_URL}/history/{context.user_data['history_period_ip']}/{context.user_data["history_period_modbus_offset"]}/{context.user_data["history_period"]}")
    if response.status_code == 200:
        
        raw_data = response.json()
        
        report_name = await build_plot(raw_data, context.user_data['history_period'], context.user_data['history_period_ip'], context.user_data["history_period_modbus_offset"])

        await update.message.reply_document(document=report_name, 
                                         caption=f"График за {message}", 
                                         reply_markup=main_menu_keyboard())
        
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "❌ Не удалось получить данные!",
            reply_markup=MAIN_MENU
        )
        return MAIN_MENU

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^1. Текущая температура$"), current_temp_menu),
                MessageHandler(filters.Regex("^2. История измерений$"), get_hist_data),
                MessageHandler(filters.Regex("^3. Управление датчиками$"), config_menu),
            ],
            CURRENT_TEMP_ALL: [
                MessageHandler(filters.Regex("^1.1 Со всех датчиков$"), handle_current_temp_all),
                MessageHandler(filters.Regex("^1.2 С конкретного датчика$"), handle_current_temp_one),
                MessageHandler(filters.Regex("^Назад$"), back)
            ],
            CURRENT_TEMP_ONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_current_temp_one_id_input),
                MessageHandler(filters.Regex("^Назад$"), back)
            ],
            CONFIG: [
                MessageHandler(filters.Regex("^3.1 Список датчиков$"), get_sensors_list),
                MessageHandler(filters.Regex("^3.2 Добавить датчик$"), add_sensor),
                MessageHandler(filters.Regex("^3.3 Удалить датчик$"), del_sensor_ip),
                MessageHandler(filters.Regex("^Назад$"), back)
            ],
            ADD_SENSOR_IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_sensor_ip)],
            ADD_SENSOR_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_sensor_port)],
            ADD_SENSOR_OFFSET: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_sensor_offset)],
            ADD_SENSOR_ACTIVITY: [
                MessageHandler(filters.Regex("^✅ Да$"), add_sensor_activity),
                MessageHandler(filters.Regex("^❌ Нет$"), add_sensor_activity)
                ],
            ADD_SENSOR_CONFIRM: [
                MessageHandler(filters.Regex("^✅ Да$"), add_sensor_confirm),
                MessageHandler(filters.Regex("^❌ Нет$"), cancel)
                ],
            DEL_SENSOR_IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_sensor_ip)],
            DEL_SENSOR_CONFIRM: [
                MessageHandler(filters.Regex("^✅ Да$"), del_sensor_confirm),
                MessageHandler(filters.Regex("^❌ Нет$"), cancel)
            ],
            HISTORY_PERIOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hist_data)]

        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()
 
if __name__ == "__main__":
    main()

