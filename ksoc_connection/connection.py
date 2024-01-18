import socket
from typing import Any, Union, Optional
from .VComPort import KKTVComPort
from .engine import ThreadServerEngine as Engine
from queue import Queue, Empty
from .packet import Packet, get_CDC_packet
from abc import abstractmethod, ABCMeta
from .logger import log

class TimeoutException(Exception):
    pass

class KKTConnectionException(Exception):
    pass

class KKTConnection(metaclass=ABCMeta):
    '''Abstract class for KKT connection ways.
     This class will bind EventEngine and transmission protocol for standard operation.
     '''
    engine:Optional[Engine]=None

    def __enter__(self):
        print('__enter__')
        return self
    def __exit__(self, exc_type, exc_value, exc_tb):
        log.info('exc_type: %s' % exc_type)
        log.info('exc_value: %s' % exc_value)
        log.info('exc_tb: %s' % exc_tb)
        self.close()
    def __del__(self):
        self.close()

    @abstractmethod
    def connect(self,*args, **kwargs)->None:
        '''Connect to KKT device.'''
        ...

    def sendCDCPacket(self, packet: Union[bytearray, bytes]) -> None:
        '''Send CDC packet (bytes) to KKT device.

        Args:
            packet (Union[bytearray, bytes]): CDC packet in bytes.

        '''
        if not self.is_connected:
            raise KKTConnectionException('Connection is not established.')
        log.debug(f'===== ====== =====')
        log.debug(f'send: {packet.hex(" ")}')
        self.engine.send(packet, cmd=packet[3])

    def receiveCDCPacket(self,* ,cmd: int = 0x00, response_only: bool = False) -> bytes:
        '''Receive CDC packet (bytes) from KKT device.
        Args:
            cmd (int, optional): Command code to check the response is expected. Defaults to 0x00 for any command.
            response_only (bool, optional): Receive response only. False for necessary to receive request response which is registered by sendCDCPacket.
        '''
        if not self.is_connected:
            raise KKTConnectionException('Connection is not established.')

        for i in range(10):
            try:
                response = self.engine.recv(response_only=response_only, time_out=0.5)
            except Empty as error:
                log.debug(f'retry to receive CDC packet response: {i+1} time')
                continue
            # check cmd
            if (response[3] == cmd) or (cmd == 0x00):
                # print(f'recv: {response.hex(" ")}')
                return response

        raise KKTConnectionException(f'response timeout')

    def sendCDCPacketWithResponse(self, request:Packet) -> Packet:
        '''Send CDC packet (bytes) to KKT device and receive response.

        Args:
            request (Packet): CDC packet in Packet class.
        '''
        request.update_checksum()
        for i in range(100):
            self.sendCDCPacket(request.CDC_packet)
            try:
                response = self.receiveCDCPacket(cmd=request.command)
                response = get_CDC_packet(response)
                return response
            except TimeoutException as error:
                log.debug(f'retry {i+1} time')
                continue
        raise TimeoutException(f'retry timeout')

    def clearQueue(self, q:Queue):
        '''For clear event loop engines queue.'''
        log.info(f'cleaning queue :{q}')
        while not q.empty():
            q.get(timeout=1)
        log.info(f'clear queue')

    def getQueue(self, recv_only:bool)->Queue:
        '''Get queue for response packet or request response packet

        Args:
            recv_only (bool, optional): True for response packet only Queue, False for request response packet Queue.
        '''
        return self.engine.get_recv_queue(response_only=recv_only)

    def close(self):
        '''Close connection.'''
        if self.engine.is_alive():
            self.engine.stop()
            log.info('engine closed')
        self.is_connected = False




class KKTWIFIConnection(KKTConnection):
    '''Implement KKTConnection for websocket connection.'''
    def __init__(self, timeout:Optional[float]=None):
        self.engine = Engine(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.is_connected = False

    def connect(self, host:str, port:int, **kwargs)->None:
        '''Connect to KKT device.

        Args:
            host (str): IP address of KKT device.
            port (int): Port of KKT device.
        '''
        self.engine.connect(__address=(host, port))
        self.is_connected = True

class KKTVComPortConnection(KKTConnection):
    '''Implement KKTConnection for serial port connection (WinAPI).'''
    def __init__(self, timeout:Optional[float]=None):
        self.engine = Engine(KKTVComPort())
        self.is_connected = False


    def connect(self, **kwargs)->None:
        '''Connect to KKT device.
        '''
        ports = KKTVComPort.get_com_port_list()
        self.engine.connect(port=ports[0].device)
        log.info(f'connected to {ports[0].device}')
        self.is_connected = True


