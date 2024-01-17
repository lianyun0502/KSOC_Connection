from dataclasses import dataclass
import win32file
import win32con
import win32api
import win32event
import serial
import serial.tools.list_ports
from typing import Optional
from .logger import log

@dataclass
class VirtualInfo:
    name: str
    vid: int
    pid: int


class KKTVComPort:
    info_list = (
        VirtualInfo('Nu_Dongle', 0x0416, 0xDC02),
        VirtualInfo('Nu_Dongle', 0x152D, 0x0581),
    )

    def __init__(self):
        log.info('KKTVComPort init')
        self.py_handle = None

        pass

    def connect(self, port: str):
        self.py_handle = win32file.CreateFile(
            f"//./{port}",
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32con.OPEN_EXISTING,
            0,
            None
        )
        if self.py_handle.handle != 0:
            log.debug(f'py_handle = {self.py_handle}')
        # Clear buffers:
        # Remove anything that was there
        win32file.PurgeComm(self.py_handle,
                            win32file.PURGE_TXCLEAR | win32file.PURGE_TXABORT |
                            win32file.PURGE_RXCLEAR | win32file.PURGE_RXABORT)

        timeouts = (0, 0, 1, 0, 0)
        win32file.SetCommTimeouts(self.py_handle, timeouts)

        self._overlappedRead = win32file.OVERLAPPED()
        self._overlappedRead.hEvent = win32event.CreateEvent(None, 1, 0, None)
        self._overlappedWrite = win32file.OVERLAPPED()
        self._overlappedWrite.hEvent = win32event.CreateEvent(None, 0, 0, None)

    def close(self):
        if self.py_handle.handle:
            self.clear_RX_queue()
            self.py_handle.close()  # 清除序列通訊物件
            log.info('serial com port closed')

    def send(self, data: bytes):
        if self.py_handle.handle:
            err_code, data_len = win32file.WriteFile(self.py_handle, data)
            if err_code != 0:
                raise Exception(f'WriteFile error code = {err_code}')

    def clear_RX_queue(self):
        if self.py_handle.handle:
            # win32file.PurgeComm(self.py_handle, win32con.PURGE_RXCLEAR)
            err_code, com_state = win32file.ClearCommError(self.py_handle)
            if err_code != 0:
                return False

            if com_state.cbInQue > 0:
                win32file.ReadFile(self.py_handle, com_state.cbInQue)
                log.debug(f'clear {com_state.cbInQue} bytes')
                return True

        return False

    def recv(self, size: int = 4096, time_out: int = 0) -> bytes:
        if self.py_handle.handle == 0:
            raise Exception('py_handle is None')

        if time_out == 0:
            err_code, com_state = win32file.ClearCommError(self.py_handle)
            if err_code != 0:
                raise Exception(f'ClearCommError error code = {err_code}')

            size = min(com_state.cbInQue, 4096)

            if size == 0:
                raise Exception(f'com_state.cbInQue = {com_state.cbInQue}')

            err_code, data = win32file.ReadFile(self.py_handle, size)
            if err_code != 0:
                raise Exception(f'ReadFile error code = {err_code}')
        else:
            err_code, data = win32file.ReadFile(self.py_handle, win32file.AllocateReadBuffer(size),
                                                self._overlappedRead)
            n = win32file.GetOverlappedResult(self.py_handle, self._overlappedRead, time_out)
            data = data[:n]

        return data

    @staticmethod
    def get_com_port_list() -> list:
        ports = serial.tools.list_ports.comports()
        KKT_ports = []
        for port in sorted(ports):
            for info in KKTVComPort.info_list:
                if info.vid == port.vid and info.pid == port.pid:
                    log.debug(f"{port.device}: {port.description} [{port.hwid}]")
                    KKT_ports.append(port)
                    break
        return KKT_ports


if __name__ == '__main__':
    import numpy as np

    c_list = KKTVComPort.get_com_port_list()
    print(c_list)
    engine = KKTVComPort()
    port = c_list[0]
    engine.connect(port=port.device)
    engine.send(bytes([0x24, 0x4B, 0x3E, 0x60, 0x01, 0x00, 0x04, 0x00, 0x00, 0x00, 0x01, 0x9A]))
    print(engine.recv(time_out=10).hex(' '))

    engine.send(bytes([0x24, 0x4B, 0x3E, 0x01, 0x01, 0x00, 0x01, 0x00, 0xFD, 0x00, 0x00, 0x00]))
    data = engine.recv(time_out=20)
    print(data.hex(' '))
    payload = np.frombuffer(data[7:19], dtype=np.uint16)
    print(f'{payload[4]}-{payload[3]}-v{payload[2]}.{payload[1]}.{payload[0]}')

    engine.close()


