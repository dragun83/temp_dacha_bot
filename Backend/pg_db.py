# Импортируемый модуль асинхронной работы с СУБД PostgreSQL
#  
import asyncpg
import logging
from datetime import datetime

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO) #Надо понизить уровень логирования.
logger = logging.getLogger(__name__)

class PGConnector:
    """
    Класс для работы с СУБД PostgreSQL.

    Args:
        db_name(str) : Имя базы данных
        db_user_name(str) : Имя пользователя БД
        db_password(str) : Пароль БД
        db_host(str) : Хост или ip адрес сервера БД. По умолчанию \"localhost\"
        db_db_port(str) : Порт сервера БД. По умолчагнию - 5432 
    """
    def __init__(self, db_name: str, db_username: str, db_password: str, db_host : str = 'localhost', db_port: int = 5432):
        self.__db_pool = None
        self.__db_host = db_host
        self.__db_name = db_name
        self.__db_username = db_username
        self.__db_password = db_password
        self.__db_port = db_port
        print(f"DB: {self.__db_name}, HOST: {self.__db_host}, USERNAME: {self.__db_username}, PASSWORD: {self.__db_password}. ")
    async def connect(self):
        """
        Иницируем подключение к БД (Создаем пул подключений)
        """
        self.__db_pool = await asyncpg.create_pool(host = self.__db_host,
                                                   database = self.__db_name,
                                                   user = self.__db_username,
                                                   password = self.__db_password,
                                                   min_size = 1,
                                                   max_size = 10
                                                   )

    async def write_data_to_db(self, oper_dict: dict):
        """
        Метод сохраняет данные из словаря oper_dict в БД 
        Args:
            oper_dict(dict) Стоварь оперативных данных
        Ret:
            True(bool): при условии успешной записи
            False(bool): при неудачной записи
        """
        async with self.__db_pool.acquire() as connection:
            data_to_insert = []
            for sensor_ip in oper_dict.keys():
                for modbus_offset in oper_dict.get(sensor_ip).keys():
                    for timestamp, temperature_value in oper_dict.get(sensor_ip).get(modbus_offset).items():
                        data_to_insert.append((datetime.fromtimestamp(timestamp), sensor_ip, modbus_offset, temperature_value))
            if data_to_insert:                    
                await connection.executemany('''
                        INSERT INTO historic_temperature (software_timestamp, sensor_ip_address, sensor_modbus_offset, temperature_value)
                        VALUES ($1, $2, $3, $4)
                    ''', data_to_insert)
                return True
            else:
                return False
                

    async def get_history_data(self, ip: str, modbus_offset: int, period: str):
        """
        Функция выбирает из БД исторические данные. По IP и MODBUS OFFSEET. Возвращает выборку (JSON).
        """
        intervals = {
            'hour': ("1", "hour"),
            '24_hours': ("24", "hour"),
            'week': ("7", "day"),
            'month': ("1", "month")
        }
        if period == "day":
            query = """SELECT software_timestamp, sensor_ip_address, sensor_modbus_offset, temperature_value FROM historic_temperature
                        WHERE sensor_ip_address = $1 AND sensor_modbus_offset = $2 AND software_timestamp >= CURRENT_DATE
                        ORDER BY software_timestamp DESC"""
            params = [ip, modbus_offset]
        elif period in intervals:
            query = """SELECT software_timestamp, sensor_ip_address, sensor_modbus_offset, temperature_value FROM historic_temperature
                        WHERE sensor_ip_address = $1 AND sensor_modbus_offset = $2 AND software_timestamp >= NOW() - (($3 || ' ' || $4)::interval)
                        ORDER BY software_timestamp DESC"""
            value, unit = intervals[period]
            params = [ip, modbus_offset, value, unit]
        else:
            raise ValueError("Неопознаный период.")
        async with self.__db_pool.acquire() as db_con:
            result = await db_con.fetch(query, *params)
        return result
