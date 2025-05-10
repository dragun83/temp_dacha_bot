from pymodbus.client import AsyncModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import asyncio

async def read_temperature():
    async with AsyncModbusTcpClient(
        host="192.168.2.115",
        port=502,
        timeout=3,
        retries=3
    ) as client:
        # Читаем 2 регистра (для float)
        response = await client.read_holding_registers(
            address=100,
            count=2,
            slave=1
        )
        
        if response.isError():
            print(f"Modbus error: {response}")
            return None
            
        # Декодируем float
        decoder = BinaryPayloadDecoder.fromRegisters(
            response.registers,
            byteorder=Endian.BIG,
            wordorder=Endian.LITTLE  # Ваш рабочий вариант
        )
        return decoder.decode_32bit_float()

async def main():
    while True:
        try:
            temp = await read_temperature()
            if temp is not None:
                print(f"Температура: {temp:.2f}°C (асинхронно)")
            else:
                print("Нет данных от датчика")
        except Exception as e:
            print(f"Критическая ошибка: {e}")
        
        await asyncio.sleep(1)  # Интервал опроса

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Программа остановлена")