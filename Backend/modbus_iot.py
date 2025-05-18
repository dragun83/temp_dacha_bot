#!/bin/python

#Модуль для работы с Modbus
# TODO: Заменить print на logger
from copy import deepcopy
import time
from pymodbus.client import AsyncModbusTcpClient
from pymodbus import exceptions as py_exceptions

class AsyncModBus:
    """
    Класс для работы с датчиками Modbus
    """
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.data_dict  =  {}
        self.last_data_dict = {}

    
    async def mesure_temperature(self):
        """
        Асинхронный метод опроса датчиков температуры
        """
        if self.config_dict is not None:
            config_dict = deepcopy(self.config_dict)
            for sensor_ip in config_dict.get("modbus_sensors").keys():
                if config_dict.get("modbus_sensors").get(sensor_ip).get("active") is True:
                    tcp_port = config_dict.get("modbus_sensors").get(sensor_ip).get("tcp_port")
                    for modbus_offset in config_dict.get("modbus_sensors").get(sensor_ip).get("modbus_offsets"):
                        try:
                            async with AsyncModbusTcpClient(host=sensor_ip, port=tcp_port, timeout=config_dict.get("modbus_parameters").get("read_timeout")) as connection:
                                response = await connection.read_holding_registers(address=modbus_offset, count=2, slave=1)
                                temperature = connection.convert_from_registers(
                                    response.registers,
                                    data_type=connection.DATATYPE.FLOAT32,
                                    word_order='little'
                                )
                                time_stamp = time.time()
                                self.data_dict.setdefault(sensor_ip, {}).setdefault(modbus_offset, {}).update({time_stamp:temperature})
                                self.last_data_dict.setdefault(sensor_ip, {}).setdefault(modbus_offset, {}).update({"last_temperature_value":temperature})
                                #print(f"Показания датчика IP : {sensor_ip} MODBUS OFFSET: {modbus_offset} - {temperature}")
                        except( py_exceptions.ConnectionException, py_exceptions.ModbusIOException):
                            #print(f"Ошибка подключения к датчику {sensor_ip}")
                            continue
                                    
                    else:
                        #print(f"Датчик {sensor_ip} не активен")
                        continue
        else:
            #print("Не указано ни одного датчика")
            pass
    
    async def update_config(self, config_dict: dict):
        """
        Метод обновления конфигураций датчиков. Принимает новый словарь конфигурации на вход.
        """
        self.config_dict = config_dict
    
    def data_dict_clear(self):
        """
        Метод очищает словарь оперативных данных.
        """
        self.data_dict.clear()