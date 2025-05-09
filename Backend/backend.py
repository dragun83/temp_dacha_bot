#!/bin/python
# TODO: +Реализовать возможность конфтигурирования через аргументы командной строки
# TODO: +Реализовать хранение конфигов в JSON
# TODO: Продумать привязку к переменным окружения для запуска в контейнере
# TODO: +\-Реализовать API (flask\FastAPI)
# TODO: +Реализовать сохранение конфигов при выходи (штатном и не штатном) из программы
# TODO: +Добавить механизм добавления датчика через API

import asyncio
import argparse
import json
import os
from pydantic import BaseModel
import signal
from fastapi import FastAPI
import uvicorn

#Объявим глобальные переменные и другие глобальные сущьности
CONFIG_DICT = {} #Словарь с конфигурацией
CONFIG_FILE_PATH = ''   #Путь к конфигурационному файлу
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
        print("Датчики опрошены")
        # TODO: Написать алгоритм опроса датчиков по MODBUS с выгрузкой результатов в глобальный словарь.
        await asyncio.sleep(5)
    
@api.on_event("startup")
# TODO: Отрефактрить и перепесать с учетом того что декоратор depricated (после MVP!)
async def startup_sequence():
    pass
    #asyncio.create_task(mesure_temperature())


@api.get("/")
async def api_test():
    """
    Тестовый хук для проверки работы API
    """
    return "It is working!"

class SensorConfig(BaseModel):
    """
    Класс для проверки валидности входных данных json при добавлении датчика
    """
    ip_address: str
    tcp_port: int
    modbus_offsets: list

@api.post("/sensor/")
async def add_sensor(sensor: SensorConfig):
    """
    Функция для добавления датчика MODBUS в конфигурационный файл
    Принимает json:
    {
        "ip_address": <IP адрес устройства[str]>,
        "tcp_port": <TCP порт устройства[int]>,
        "modbus_offsets": <Список офсетов MODBUS адресов [list]>
    }

    """
    print(f"Мы получили данные : {sensor}")
    CONFIG_DICT.setdefault("modbus_sensors",{}).setdefault(sensor.ip_address, {
                                                                                "tcp_port":sensor.tcp_port,
                                                                                "modbus_offsets":sensor.modbus_offsets
                                                                                })
    print(f"Словарь конфига теперь выглядит так : \n {CONFIG_DICT}")
    return {"message": "Sensor added" }

def main():
    global CONFIG_DICT, CONFIG_FILE_PATH
    argparser=argparse.ArgumentParser(description="Backend service for home automation")
    argparser.add_argument('-c', '--config-file', type=str, required=False, default='Conf/backend.cfg', help="Custom config-file path")
    argparser.add_argument('-i', '--init', type=bool, default=False, help="Clear and init configuration file")
    argparser.add_argument("--api-host", type=str, required=False,default="0.0.0.0", help="Адрес сервера API. По умолчанию \"0.0.0.0\"")
    argparser.add_argument("--api-port", type=int, required=False,default=5000, help="Порт сервера API. По умолчанию \"5000\"")

    args = argparser.parse_args()
    CONFIG_FILE_PATH = args.config_file
    if validate_config(CONFIG_FILE_PATH):
        CONFIG_DICT = read_config_json(CONFIG_FILE_PATH)
        print("Запускаем API сервер")
        try:
            uvicorn.run(api, host = CONFIG_DICT.get('api_server').get('server_addres'),port=int(CONFIG_DICT.get('api_server').get('server_port')))
        finally:
            write_config_json(CONFIG_DICT, CONFIG_FILE_PATH)
    elif args.init:
        CONFIG_DICT = {
            'api_server':{
                'server_address': args.api_host,
                'server_port': args.api_port
            }
        }
        print("Запускаем API сервер")
        try:
            uvicorn.run(api, host = CONFIG_DICT.get('api_server').get('server_addres'),port=int(CONFIG_DICT.get('api_server').get('server_port')))
        finally:
            write_config_json(CONFIG_DICT, CONFIG_FILE_PATH)


    else:
        raise FileExistsError(f"Файл {CONFIG_FILE_PATH} не существует или поврежден. Выполните запуск с ключем -i True")
    

if __name__ == "__main__":
    main()