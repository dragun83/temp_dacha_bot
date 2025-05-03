#!/bin/python
# TODO: Реализовать возможность конфтигурирования через аргументы командной строки
# TODO: Реализовать хранение конфигов в JSON
# TODO: Продумать привязку к переменным окружения для запуска в контейнере
# TODO: Реализовать API (flask)

import json
import argparse
from flask import Flask


TEST_CONFIG = {
               'api_server':{
                   'server_addres': '0.0.0.0',
                   'server_port': 8080
                    }
               }

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
    """
    pass

def main():
    argparser=argparse.ArgumentParser(description="Backend service for home automation")
    argparser.add_argument('-c', '--config-file', type=str, required=False, default='backend.cfg', help="Custom config-file path")
    argparser.add_argument('-i', '--init', type=bool, default=False, help="Clear and init configuration file")
    print(TEST_CONFIG)
    write_config_json(TEST_CONFIG,'test_config.conf')

if __name__ == "__main__":
    main()