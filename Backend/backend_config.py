#!/bin/python
#Модуль бекенда для работы с конфигурациями
import argparse
import json
import os

class Configurator:
    """
    Класс для работы с конфигурациями в формате JSON
    Args:
        config_dict(dict): Словарь с конфигурацией
        config_file_path(str): Путь к файлу конфигурации
    """
    def __init__(self):
        self.config_dict = {}
        self.__config_is_valid = False
        self.__config_file_path = None
        #Тут будет лютая дичь, а именно - загрузка и валидация данных конфига при инициализации объекта класса.

        argparser=argparse.ArgumentParser(description="Backend service for home automation")
        argparser.add_argument('-c', '--config-file', type=str, required=False, default='Conf/backend.cfg', help="Путь к конфигурационному файлу.")
        argparser.add_argument('-i', '--init', action="store_true", help="Очистить и пересоздать конфигурационный файл. Данные о датчиках будут удалены!")
        argparser.add_argument("--api-host", type=str, required=False,default="0.0.0.0", help="Адрес сервера API. По умолчанию \"0.0.0.0\"")
        argparser.add_argument("--api-port", type=int, required=False,default=5000, help="Порт сервера API. По умолчанию \"5000\"")
        argparser.add_argument("--modbus-query-freq", type=int, required=False,default=5, help="Частота опроса MODBUS в секундах. По умолчанию \"5\" сек.")
        argparser.add_argument("--modbus-conn-timeout", type=int, required=False,default=5, help="Таймаут подключения MODBUS в секундах. По умолчанию \"5\" сек.")
        argparser.add_argument("--db-host", type=str, required=False,default="localhost", help="Адрес сервера СУБД Postgresql  \"localhost\"")
        argparser.add_argument("--db-name", type=str, required=False,default="dachabot_db", help="Имя базы данных. По умолчанию \"dachabot_db\"")
        argparser.add_argument("--db-user", type=str, required=False,default="postgres", help="Имя пользователя БД. По умолчанию \"postgres\" сек.")
        argparser.add_argument("--db-password", type=str, required=False,default="Qwe12345", help="Пароль БД")
        argparser.add_argument("--db-write-period", type=int, required=False,default=30, help="Частота записи данных в БД. По умолчанию \"30\" сек.")

        args = argparser.parse_args()
        self.__config_file_path = args.config_file

        if args.init:
            print("Переинициализация конфигурации")
            self.config_dict = {
                'api_server':{
                    'server_address': args.api_host,
                    'server_port': args.api_port
                },
                'modbus_parameters':{
                    'query_freq':args.modbus_query_freq
                    },
                'db_params':{
                    'db_host':args.db_host,
                    'db_name':args.db_name,
                    'db_user':args.db_user,
                    'db_password':args.db_password,
                    'db_write_period':args.db_write_period
                }
            }
            self.__config_is_valid = True

        elif os.path.exists(self.__config_file_path) and os.path.getsize(self.__config_file_path) > 0:
            try:
                with open(self.__config_file_path, 'r') as config_file:
                    self.config_dict = json.load(config_file)
                    self.__config_is_valid = True
            except(json.JSONDecodeError, UnicodeDecodeError):
                self.__config_is_valid = False
        else:
            self.__config_is_valid = False

 
    def save_config(self) -> bool:
        """
        Метод записывает содержимое словаря конфигураций в файл json
        Возвращает True - если успешно, False - если нет
        """
        try:
            with open(self.__config_file_path, 'w') as config_file:
                json.dump(self.config_dict, config_file, indent=4)
            return True
        except(IOError):
            return False
    

    @property
    def is_config_valid(self):
        """
        Возвращает статус загрузки конфига.
        """
        return self.__config_is_valid
    
    @property
    def config_file_name(self):
        """
        Геттер пути к конфигурационному файлу
        """
        return self.__config_file_path