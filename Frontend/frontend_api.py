# Модуль фронта для работы с API

import httpx
import json

class APIClient:
    """
    Класс API клиента. Который выполняет запросы к backend.
    """
    def __init__(self, base_url: str):
        self.__base_url = base_url

    async def get_all_current_temp(self):
        """
        Получаем от backend текущую температуру по всем датчикам
        """
        async with httpx.AsyncClient() as api_client:
            response = await api_client.get(f"{self.__base_url}/current_temp/")
        if response.status_code == 200:
            return response.json()
        else:
            return None
        
    
    async def get_current_temp(self, sensor_ip: str, modbus_offset: int):
        """
        Получаем текущую температуру с дачика по sensor id
        """
        tmp_response = await self.get_all_current_temp()
        if tmp_response is not None:
            temp_value = tmp_response.get(sensor_ip, {}).get(modbus_offset, {}).get('last_temperature_value')
            return temp_value
        else:
            return None
        
    async def get_config(self):
        """
        Получаем конфигурацию.
        """
        async with httpx.AsyncClient() as api_client:
            response = await api_client.get(f"{self.__base_url}/config/")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    async def add_sensor(self, sensor_activiti: str, sensor_ip: str, sensor_port: int, sensor_offsets: list):
        """
        Метод добавляет датчик, или меняет его (так работает API)
        """
        async with httpx.AsyncClient() as client:
            post_data = {
                "active": sensor_activiti,
                "ip_address": sensor_ip,
                "tcp_port": sensor_port,
                "modbus_offsets": sensor_offsets
            }
            response = await client.post(f"{self.__base_url}/sensor/", data=json.dumps(post_data))
        if response.status_code == 200:
            return True
        else:
            return False
        
    async def del_sensor(self, ip: str):
        """
        Метод удаляет датчик с указаным IP
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(url=f"{self.__base_url}/sensor/{ip}")
        if response.status_code == 200:
            return True
        else:
            return False
    
    async def get_historyc_data(self, ip: str, modbus_offset: int, period: str):
        """
        Метод получает исторические данные по показаниям датчика за указаный период. 
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.__base_url}/history/{ip}/{modbus_offset}/{period}")
        if response.status_code == 200:
            return response.json()
        else:
            return None