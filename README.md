# MY home automation project (temp_dacha_bot)
Проект домашней автоматизации для дачи.
Состоит из:
1. Бекэнд - pytohn + mysql
2. Фронтенд - telegram-бот (python)
3. Прошивка для esp32/esp8266 - источник данных по протоколу MODBUS TCP
Telegram bot, data backend server, and esp32_termosensor firmware(micropytohn)

## Попробую что-то типа ТЗ наваять тут...


## Функции, которые необходимо реализовать:

### Backend:
    1. Опрос датчиков из списка по MODBUS TCP, роль - master(клиент);
    2. Хранение информации о датчиках(BS18B20 и преобразователях esp32)  в СУБД;
    3. Созранение результатов измерений  температуры и событий (переключений и прочее в будущих реализациях) в СУБД с отметкой времени (вероятно будет 2 отметки времени от СУБД и от системы);
    4. Получение текущих данных с датчиков и выдача их во фронтенд;
    5. Получение исторических данных из СУБД и выдача их по запросу frontend (?)

### Frontend:
    1. Организация структурированного интефейса для пользователя;
    2. Организация приема и передачи команд через API
    3. Авторизация пользователя на основе Telegram ID с выдачей ролей (admin\user) через аккаунт superuser
    
### Прошивка для преобразователя (ESP32)
    1. Язык разработки MicroPython
    2. Протокол общения с датчиками - 1 wire;
    3. Протокол общения с системой - MODBUS TCP, роль - slave(сервер);


### Структура конфигурации backend

    Конфиг файл представляет из себя JSON файл в котором для каждой секции конфигурации содержится свой вложеный словарь с параметрами (и\или еще одна секция при необходимости). Файл может быть сгенерирован или перезаписан программой при условии установки ключа "-i True".



        ```
        {
        "api_server": {
            "server_address": "0.0.0.0",
            "server_port": 20000
            }
        "modbus_parameters":{
            "query_freq": <частота опрос в сек.>
            "read_timeout": <таймаут соединения с датчиком в сек.>
        }
        "modbus_sensors":{
            <ip_address>:{
                "active": true\false (boolean)
                "tcp_port": <tcp_port>,
                "modbus_offsets": [<modbus_offset_1>, <modbus_offset_2>, <modbuss_offset_n>]
                }
            }
        }
        ```
    
### Структура словаря оперативных данных

```
{
    <ip_address>:{
        "data_is_valid": True\Fals (bool)
        <modbus_offset_1>:{<timestamp>:<temperature_value>, "valid_flag":<bool>},
        <modbus_offset_2>:{<timestamp>:<temperature_value>}, "valid_flag":<bool>,
        ...
        <modbus_offset_n>:{<timestamp>:<temperature_value>, "valid_flag":<bool>}
    }
}
```
