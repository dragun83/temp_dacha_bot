#!/bin/python
# TODO: +Реализовать возможность конфтигурирования через аргументы командной строки
# TODO: +Реализовать хранение конфигов в JSON
# TODO: +Реализовать сохранение конфигов при выходе (штатном и не штатном) из программы
# TODO: +Реализовать API (flask\FastAPI)
# TODO: +Добавить механизм добавления датчика через API
# TODO: +Реализовать функцию сбора данных с датчика.
# TODO: +Реализовать функционал получения оперативных данных через API
# TODO: Реализовать функционал сохранения оперативных данных в СУБД, а так же очистку словаря оперативных данных после сохранения в СУБД
# TODO: Реализовать функционал получения исторических данных из СУБД через API
# TODO: (Не нужно.)Реализовать механизм отключения датчика в случае ошибки чтения информации(с ручной активацией)
# TODO: (После MVP)Продумать привязку к переменным окружения для запуска в контейнере

import asyncio
import argparse
from datetime import datetime
import json
import os
import signal
import time
from pydantic import BaseModel
from pymodbus.client import AsyncModbusTcpClient
from pymodbus import exceptions as py_exceptions
from fastapi import FastAPI
import uvicorn

#Объявим глобальные переменные и другие глобальные сущности.
# TODO: AI говорит что тут можно применить Depends... Почитать и проверить это (после MVP) 

CONFIG_DICT = {} #Словарь с конфигурацией
CONFIG_FILE_PATH = '' #Путь к конфигурационному файлу
DATA_DICT = {} #Словарь с оперативными данными


api = FastAPI()

def shutdown_handler(*args):
    write_config_json(CONFIG_DICT, CONFIG_FILE_PATH)
    raise SystemExit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

def write_config_json(config: dict, config_file_path: str) -> bool:
    """
    Записвыаем конфиг в json если все ок - возвращаем true, если нет - false
    Args:
        config(dict): словарь с конфигурацией.
        config_file_path(str): путь к конфигурационному файлу
    """
    try:
        with open(config_file_path, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        return True
    except:
        return False

def read_config_json(config_file_path: str) -> dict:
    """
    Читаем конфиг и возвращаем словарь с настройками.
    Args:
        config_file_path(str): Путь к конфигрурационному файлу
    """
    with open(config_file_path, 'r') as config_file:
        config_dict = json.load(config_file)
    return config_dict

def validate_config(config_file_path: str) -> bool:
    """
    Функция проверяет наличие и валидность конфигурационного файла (пока просто по тому что в нем содержится JSON)
    Args:
        config_file_path(str): Путь к конфигрурационному файлу
    """
    if os.path.exists(config_file_path) and os.path.getsize(config_file_path) > 0:
        try:
            with open(config_file_path, 'r') as config_file:
                json.load(config_file)
                return True
        except(json.JSONDecodeError, UnicodeDecodeError):
            return False
    else:
        return False

        

async def mesure_temperature() -> dict:
    """
    Функция опрашивает датчики по MODBUS и возвращает словарь с показаниями
    """
    while True:
        # TODO: Написать алгоритм опроса датчиков по MODBUS с выгрузкой результатов в глобальный словарь.
        if CONFIG_DICT.get("modbus_sensors") is not None:
            for sensor_ip in CONFIG_DICT.get("modbus_sensors").keys():
                if CONFIG_DICT.get("modbus_sensors").get(sensor_ip).get("active") is True:
                    tcp_port = CONFIG_DICT.get("modbus_sensors").get(sensor_ip).get("tcp_port")
                    for modbus_offset in CONFIG_DICT.get("modbus_sensors").get(sensor_ip).get("modbus_offsets"):
                      try:
                        async with AsyncModbusTcpClient(host=sensor_ip, port=tcp_port, timeout=CONFIG_DICT.get("modbus_parameters").get("read_timeout")) as connection:
                            response = await connection.read_holding_registers(address=modbus_offset, count=2, slave=1)
                            temperature = connection.convert_from_registers(
                                response.registers,
                                data_type=connection.DATATYPE.FLOAT32,
                                word_order='little'
                            )
                            time_stamp = time.time()
                            DATA_DICT.setdefault(sensor_ip, {}).setdefault(modbus_offset, {}).update({time_stamp:temperature})
                            print(f"Показания датчика IP : {sensor_ip} MODBUS OFFSET: {modbus_offset} - {temperature}")
                      except( py_exceptions.ConnectionException, py_exceptions.ModbusIOException):
                          print(f"Ошибка подключения к датчику {sensor_ip}")
                          continue
                                
                else:
                    print(f"Датчик {sensor_ip} не активен")
        else:
            print("Не указано ни одного датчика")
        await asyncio.sleep(CONFIG_DICT.get('modbus_parameters').get('query_freq'))
    
@api.on_event("startup")
# TODO: Отрефактрить и перепесать с учетом того что декоратор depricated (после MVP!)
async def startup_sequence():
    #pass
    asyncio.create_task(mesure_temperature())


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
    return DATA_DICT

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
    print(f"Мы получили данные : {sensor}")
    CONFIG_DICT.setdefault("modbus_sensors",{})[sensor.ip_address] = { 
                                                                                "active":sensor.active,
                                                                                "tcp_port":sensor.tcp_port,
                                                                                "modbus_offsets":sensor.modbus_offsets
                                                                                }
    print(f"Словарь конфига теперь выглядит так : \n {CONFIG_DICT}")
    return {"message": "Sensor added" }

@api.delete("/sensor/{ip_address}")
async def remove_sensor(ip_address):
    """
    Удаление датчика с указаным IP
    """
    deleted_sensor = CONFIG_DICT["modbus_sensors"].pop(ip_address)
    return {"message": f"Датчик {deleted_sensor} быдл удален"}

@api.get("/config/")
async def get_sensors_list():
    """
    Возвращает конфигурацию. Функция для дебага!
    """
    return CONFIG_DICT

def main():
    global CONFIG_DICT, CONFIG_FILE_PATH
    argparser=argparse.ArgumentParser(description="Backend service for home automation")
    argparser.add_argument('-c', '--config-file', type=str, required=False, default='Conf/backend.cfg', help="Путь к конфигурационному файлу.")
    argparser.add_argument('-i', '--init', type=bool, default=False, help="Очистить и пересоздать конфигурационный файл. Данные о датчиках будут удалены!")
    argparser.add_argument("--api-host", type=str, required=False,default="0.0.0.0", help="Адрес сервера API. По умолчанию \"0.0.0.0\"")
    argparser.add_argument("--api-port", type=int, required=False,default=5000, help="Порт сервера API. По умолчанию \"5000\"")
    argparser.add_argument("--modbus-query-freq", type=int, required=False,default=5, help="Частота опроса MODBUS в секундах. По умолчанию \"5\" сек.")
    argparser.add_argument("--modbus-conn-timeout", type=int, required=False,default=5, help="Таймаут подключения MODBUS в секундах. По умолчанию \"5\" сек.")

    args = argparser.parse_args()
    CONFIG_FILE_PATH = args.config_file
    if validate_config(CONFIG_FILE_PATH):
        CONFIG_DICT = read_config_json(CONFIG_FILE_PATH)
        print("Запускаем API сервер")
        try:
            uvicorn.run(api, host = CONFIG_DICT.get('api_server').get('server_address'),port=int(CONFIG_DICT.get('api_server').get('server_port')))
        finally:
            write_config_json(CONFIG_DICT, CONFIG_FILE_PATH)
    elif args.init:
        CONFIG_DICT = {
            'api_server':{
                'server_address': args.api_host,
                'server_port': args.api_port
            },
            'modbus_parameters':{
                "query_freq":args.modbus_query_freq
                }
        }
        print("Запускаем API сервер")
        try:
            uvicorn.run(api, host = CONFIG_DICT.get('api_server').get('server_address'),port=int(CONFIG_DICT.get('api_server').get('server_port')))
        finally:
            write_config_json(CONFIG_DICT, CONFIG_FILE_PATH)


    else:
        raise FileExistsError(f"Файл {CONFIG_FILE_PATH} не существует или поврежден. Выполните запуск с ключем -i True")
    

if __name__ == "__main__":
    main()