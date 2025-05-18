#!/bin/python
# TODO: +Реализовать возможность конфтигурирования через аргументы командной строки
# TODO: +Реализовать хранение конфигов в JSON
# TODO: +Реализовать сохранение конфигов при выходе (штатном и не штатном) из программы
# TODO: +Реализовать API (flask\FastAPI)
# TODO: +Добавить механизм добавления датчика через API
# TODO: +Реализовать функцию сбора данных с датчика.
# TODO: +Реализовать функционал получения оперативных данных через API
# TODO: +Добавить секцию с настройками доступа к СУБД в конфигурацию и arparse
# TODO: +Реализовать функционал сохранения оперативных данных в СУБД, а так же очистку словаря оперативных данных после сохранения в СУБД
# TODO: +Реализовать функционал получения исторических данных из СУБД через API
# TODO: Реализовать выборку данных за промежуток времени.
# TODO: Реализовать обработку ошибки подключения к БД
# TODO: (Не нужно.)Реализовать механизм отключения датчика в случае ошибки чтения информации(с ручной активацией)
# TODO: (После MVP)Продумать привязку к переменным окружения для запуска в контейнере
# TODO: (После MVP)Продумать валидацию приходящих по MODBUS данных - если датчик со стороны 1Wire не досупны система возвращает пустой лист...

import asyncio
import logging
import signal

from pydantic import BaseModel

from fastapi import FastAPI
import uvicorn
from modbus_iot import AsyncModBus
from pg_db import PGConnector
from backend_config import Configurator

#Объявим глобальные переменные и другие глобальные сущности.


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO) #Надо понизить уровень логирования.
logger = logging.getLogger(__name__)


config = Configurator()

api = FastAPI()

pg_connector = PGConnector(db_host=config.config_dict.get('db_params').get('db_host'),
                           db_name=config.config_dict.get('db_params').get('db_name'),
                           db_username=config.config_dict.get('db_params').get('db_user'),
                           db_password=config.config_dict.get('db_params').get('db_password')
                           )



modbus_connector = AsyncModBus(config.config_dict)

def shutdown_handler(*args):
    # TODO: Доелать обработчик для корректного завершения всех корутин.
    config.save_config()
    raise SystemExit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


async def save_oper_data_to_history():
    """
    Функция сохраняет данные из глобального словаря оперативных данных в БД с историческими данными, очищает оперативный словарь,
     а так-же создает БД в случае если она отсутствует.
    """
    await pg_connector.connect()
    while True:
        if await pg_connector.write_data_to_db(modbus_connector.data_dict):    
            modbus_connector.data_dict_clear()
        else:
            logger.error("Не удалось записать данные в СУБД!")
        await asyncio.sleep(config.config_dict.get("db_params").get("db_write_period"))

async def mesure_temperature():
    """
    Функция опрашивает датчики по MODBUS и записывает в словарь  показания
    """
    while True:
        await modbus_connector.mesure_temperature()


        await asyncio.sleep(config.config_dict.get('modbus_parameters').get('query_freq'))
    
@api.on_event("startup")
# TODO: Отрефактрить и перепесать с учетом того что декоратор depricated (после MVP!)
async def startup_sequence():
    asyncio.create_task(mesure_temperature())
    asyncio.create_task(save_oper_data_to_history())


@api.get("/")
async def api_test():
    """
    Тестовый хук для проверки работы API
    """
    return {"message":"It is working!"}

@api.get("/oper")
async def get_oper_data():
    """
    Возвращаем словарь оперативных данных целиком
    """
    return modbus_connector.data_dict

@api.get("/current_temp/")
async def get_current_temp():
    """
    Возвращаем словарь текущих показаний
    """
    return modbus_connector.last_data_dict

class SensorConfig(BaseModel):
    """
    Класс для проверки валидности входных данных json при добавлении датчика
    """
    active: bool
    ip_address: str
    tcp_port: int
    modbus_offsets: list

@api.post("/sensor/")
async def add_sensor(sensor: SensorConfig):
    """
    Функция для добавления датчика MODBUS в конфигурационный файл
    Принимает json:
    {
        "active" : <bool флаг активности устройства>
        "ip_address": <IP адрес устройства[str]>,
        "tcp_port": <TCP порт устройства[int]>,
        "modbus_offsets": <Список офсетов MODBUS адресов [list]>
    }

    """
    config.config_dict.setdefault("modbus_sensors",{})[sensor.ip_address] = { 
                                                                                "active":sensor.active,
                                                                                "tcp_port":sensor.tcp_port,
                                                                                "modbus_offsets":sensor.modbus_offsets
                                                                                }
    await modbus_connector.update_config(config.config_dict)
    return {"message": "Sensor added" }

@api.delete("/sensor/{ip_address}")
async def remove_sensor(ip_address):
    """
    Удаление датчика с указаным IP
    """
    deleted_sensor = config.config_dict["modbus_sensors"].pop(ip_address)
    await modbus_connector.update_config(config.config_dict)
    return {"message": f"Датчик {deleted_sensor} быдл удален"}

@api.get("/config/")
async def get_config():
    """
    Возвращает конфигурацию. Функция для дебага!
    """
    return config.config_dict

@api.get("/history/{ip}/{modbus_offset}/{period}")
async def get_history_data(ip: str, modbus_offset: int, period: str):
    """
    Функция выбирает из БД исторические данные. По IP и MODBUS OFFSEET. Возвращает выборку (JSON).
    """
    result = await pg_connector.get_history_data(ip,modbus_offset, period)
    return result


def main():
    print(f"Состояние флага конфигурации {config.is_config_valid}")
    if  config.is_config_valid:
        print("Запускаем API сервер")
        try:
            uvicorn.run(api, host = config.config_dict.get('api_server').get('server_address'),port=int(config.config_dict.get('api_server').get('server_port')))
        finally:
            config.save_config()

    else:
        raise FileExistsError(f"Не удалось загрузить конфигурацию. Файл {config.config_file_name} не найден или поврежден. Выполните запуск с ключем -i True")
    

if __name__ == "__main__":
    main()