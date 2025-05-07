#!/bin/python
# TODO: Реализовать возможность конфтигурирования через аргументы командной строки
# TODO: Реализовать хранение конфигов в JSON
# TODO: Продумать привязку к переменным окружения для запуска в контейнере
# TODO: Реализовать API (flask\FastAPI)

import asyncio
import argparse
import json
import os
#from flask import Flask
from fastapi import FastAPI
import uvicorn

#api = Flask(__name__)
api = FastAPI()

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

async def sensors_sync() -> dict:
    """
    Функция опрашивает датчики по MODBUS и возвращает словарь с показаниями
    """
    while True:
        print("Датчики опрошены")
        await asyncio.sleep(5)
    
@api.on_event("startup")
async def startup_sequence():
    asyncio.create_task(sensors_sync())

@api.get("/")
async def api_test():
    """
    Тестовый хук для проверки работы API
    """
    return "It is working!"

def main():
    argparser=argparse.ArgumentParser(description="Backend service for home automation")
    argparser.add_argument('-c', '--config-file', type=str, required=False, default='Conf/backend.cfg', help="Custom config-file path")
    argparser.add_argument('-i', '--init', type=bool, default=False, help="Clear and init configuration file")
    
    args = argparser.parse_args()
    if validate_config(args.config_file):
        config_dict = read_config_json(args.config_file)
    else:
        raise FileExistsError(f"Файл {args.config_file} не существует или поврежден. Выполните запуск с ключем -i")
    uvicorn.run(api, host = config_dict.get('api_server').get('server_addres'),port=int(config_dict.get('api_server').get('server_port')))
    #api.run(host = config_dict.get('api_server').get('server_addres'),port=int(config_dict.get('api_server').get('server_port')))
    


if __name__ == "__main__":
    main()