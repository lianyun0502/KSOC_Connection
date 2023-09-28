import socket
from typing import Any, Union, Optional
from VComPort import KKTVComPort
from backend import ThreadBackend as Backend
from queue import Queue, Empty
from packet import Packet, Command, Direction, get_CDC_packet

class TimeoutException(Exception):
    pass

class KKTConnection:
    engine:Backend=None
    def __del__(self):
        self.close()
    def connect(self,*args, **kwargs)->None:
        raise NotImplementedError
    def sendCDCPacket(self, packet: Union[bytearray, bytes]) -> None:
        if not self.is_connected:
            raise Exception('Not connected')
        print(f'===== ====== =====')
        print(f'send: {packet.hex(" ")}')
        self.engine.send(packet, cmd=packet[3])
    def receiveCDCPacket(self, cmd: int = 0x00, response_only: bool = False) -> bytes:
        if not self.is_connected:
            raise Exception('Not connected')
        while True:
            try:
                response = self.engine.recv(response_only, time_out=1)
            except Empty as error:
                raise TimeoutException(f'response timeout')

            if (response[3] == cmd) or (cmd == 0x00):
                # print(f'recv: {response.hex(" ")}')
                return response

    def sendCDCPacketWithResponse(self, request:Packet) -> Packet:
        request.update_checksum()
        for i in range(100):
            self.sendCDCPacket(request.CDC_packet)
            try:
                response = self.receiveCDCPacket(cmd=request.command)
                response = get_CDC_packet(response)
                return response
            except TimeoutException as error:
                print(f'retry {i+1} time')
                continue
        raise TimeoutException(f'retry timeout')


    def clearQueue(self, q:Queue):
        print(f'cleaning queue :{q}')
        while not q.empty():
            q.get(timeout=1)
        print(f'clear queue')

    def getQueue(self, recv_only:bool)->Queue:
        return self.engine.get_recv_queue(response_only=recv_only)

    def close(self):
        if self.engine.is_alive():
            self.engine.stop()
        self.is_connected = False
        print('client closed')
class KKTWIFIConnection(KKTConnection):
    def __init__(self, timeout:Optional[float]=None):
        self.engine = Backend(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.is_connected = False


    def connect(self, host:str, port:int, **kwargs)->None:
        self.engine.connect(__address=(host, port))
        self.is_connected = True

class KKTVComPortConnection(KKTConnection):
    def __init__(self, timeout:Optional[float]=None):
        self.engine = Backend(KKTVComPort())
        self.is_connected = False


    def connect(self, **kwargs)->None:
        ports = KKTVComPort.get_com_port_list()
        self.engine.connect(port=ports[0].device)
        self.is_connected = True


