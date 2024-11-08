import threading
import time
import serial
import struct
from bleak import BleakClient
import asyncio

class CommunicationHandler:
    def __init__(self, mode='SERIAL'):
        self.mode = mode.upper()
        self.latest_value = None
        self._stop_event = threading.Event()
        self._thread = None
        self.lock = threading.Lock()
        # Serial settings
        self.serial_port = 'COM6'  # Replace with your serial port
        self.baudrate = 9600
        self.ser = None
        # BLE settings
        self.device_address = '96:18:FC:FA:30:FA'  # Replace with your BLE device address
        self.ble_characteristic_uuid = '12345678-1234-5678-1234-56789abcdef1'  # Replace with your characteristic UUID
        self.client = None
        self.loop = None

    def set_mode(self, mode):
        self.mode = mode.upper()

    def start(self):
        self._stop_event.clear()
        if self.mode == 'SERIAL':
            self.ser = serial.Serial(self.serial_port, self.baudrate)
            self._thread = threading.Thread(target=self._read_serial, daemon=True)
        elif self.mode == 'BLE':
            self.loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._read_ble, daemon=True)
        else:
            raise ValueError("Unsupported mode. Choose 'SERIAL' or 'BLE'.")
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        if self.ser and self.ser.is_open:
            self.ser.close()
        if self.client and self.client.is_connected:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)

    def _read_serial(self):
        while not self._stop_event.is_set():
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8').strip()
                    value = int(line)
                    with self.lock:
                        self.latest_value = value
                except Exception as e:
                    print(f"Serial read error: {e}")
                    continue
            else:
                time.sleep(0.01)

    def _read_ble(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._ble_main())

    async def _ble_main(self):
        try:
            self.client = BleakClient(self.device_address, loop=self.loop)
            await self.client.connect()
            await self.client.start_notify(self.ble_characteristic_uuid, self._handle_notification)
            while not self._stop_event.is_set():
                await asyncio.sleep(0.1)
            await self.client.stop_notify(self.ble_characteristic_uuid)
            await self.client.disconnect()
        except Exception as e:
            print(f"BLE error: {e}")

    def _handle_notification(self, sender, data):
        try:
            # Assuming the data is a 32-bit float sent from the BLE device
            value = struct.unpack('f', data)[0]
            with self.lock:
                self.latest_value = value
        except Exception as e:
            print(f"BLE notification error: {e}")

    def get_sensor_value(self):
        with self.lock:
            return self.latest_value
