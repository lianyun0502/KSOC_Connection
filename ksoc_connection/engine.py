import sys
from multiprocessing import Process
from queue import Queue,LifoQueue
from threading import Thread, Event
import socket
import time
from typing import Any, Union, Optional, Dict, Tuple
from .logger import log
class CDCCollection:
    '''CDC packet Composer'''
    def __init__(self):
        super().__init__()
        self._buffer:Optional[bytearray] = None
        self.temp_bytes = b'' # buffered bytes to compose CDC packet
        self.offset = 0 # pointer of start frame
        self.byte_without_payload = 11

    def init(self):
        '''reset temp_bytes and byte_without_payload'''
        self.temp_bytes = b''
        self.byte_without_payload = 11

    def collect(self, data:bytes)->Optional[bytes]:
        '''collect and compose CDC packet from data'''
        # check if data is a complete packet, return packet if true
        is_packet, packet = self.check_is_packet(data)
        if is_packet:
            log.debug(f'put packet length : {len(packet)}')
            return packet

        # if data is not a complete packet, append data to temp_bytes
        self.temp_bytes += data
        data_length = len(self.temp_bytes)
        log.debug(f'temp_bytes_length = {data_length}')

        # find start frame in temp_bytes ($K<)
        offset = self.temp_bytes.find(b'$K<')
        # print(offset)

        # if start frame not found in temp_bytes, clear temp_bytes and return
        if offset == -1:
            log.debug(f'start frame not found, data[0:3] == {self.temp_bytes[offset:3]}')
            log.debug(f'data = {self.temp_bytes.hex(" ")}')
            self.init()
            return

        # if start frame found, move pointer to start frame
        self.temp_bytes = self.temp_bytes[offset:]
        # print('0 get start frame')
        # offset = 0

        # just double check if start frame is correct, not necessary
        if self.temp_bytes[:3] != b'$K<':
            raise Exception(f'header[0:3] invalid, data[0:3] == {self.temp_bytes[:3]}')

        # get payload length
        payload_length = int.from_bytes(self.temp_bytes[5:7], byteorder='big', signed=False)
        # print(f'payload_length = {payload_length}')

        # if data_length >= 8 + payload_length, packet should be complete
        if data_length >= 8 + payload_length:
            # print('data_length >= 8 + payload_length')
            CDC_packet = self.temp_bytes[:8 + payload_length]
            log.debug(f'get packet len : {len(CDC_packet)}')
            temp = self.temp_bytes[8 + payload_length:]
            self.init()
            self.temp_bytes = temp
            return CDC_packet

    def check_is_packet(self, data:bytes)->Tuple[bool, Optional[bytes]]:
        '''check if data is a complete CDC packet'''

        data = bytes(data)
        offset = data.find(b'$K<')

        if offset == -1: # kkt header not found
            return False, data

        assert data[
               offset:offset + 3] == b'$K<', f'data[0:3] == {data[offset:3]}, data = {data.hex(" ")}'

        data = data[offset:]
        data_length = len(data)

        if data_length < 7: # header + cmd + payload length not enough
            return False, data

        log.debug('get start frame')
        payload_length = int.from_bytes(data[5:7], byteorder='big', signed=False)
        # print(f'payload_length = {payload_length}')

        if data_length >= 8 + payload_length: # packet is complete
            # print('data_length >= 8 + payload_length')
            CDC_packet = data[:8 + payload_length]
            # self.packet_queue.put(CDC_packet)
            # print(f'put packet len : {len(CDC_packet)}')

            return True, CDC_packet

        else:
            return False, data

class ServerEngine(Process):
    '''Event loop engine implement by process'''
    def __init__(self, porto):
        super().__init__()
        self.porto = porto
        self.CDC_response_only = Queue()
        self.CDC_request_response = Queue()
        self.response_cmd = set([])

    def run(self):
        CDC_collection = CDCCollection()
        while self.is_alive():
            recv_data = self.porto.recv(4096 * 2)
            if recv_data == b'':
                continue
            packet = CDC_collection.collect(recv_data)
            if packet is not None:
                if packet[3] in self.response_cmd:
                    log.debug(f'to request response queue, cmd = {packet[3]}')
                    self.CDC_request_response.put(packet)
                else:
                    log.debug(f'to response only queue, cmd = {packet[3]}')
                    self.CDC_response_only.put(packet)
        print('process stop')

    def send(self, data:bytes, cmd:Optional[int]=None):
        if cmd is not None:
            self.response_cmd.add(cmd)
        self.porto.send(data)

    def get_recv_queue(self, response_only: bool = False) -> Queue:
        if response_only:
            return self.CDC_response_only
        else:
            return self.CDC_request_response

    def recv(self, response_only: bool = False) -> bytes:
        return self.get_recv_queue(response_only).get()

    def stop(self):
        self.terminate()
        time.sleep(1)
        self.porto.close()

    def connect(self, *args, **kwargs):
        self.porto.connect(*args, **kwargs)
        self.start()
        print(self.porto)
        time.sleep(1)

class ThreadServerEngine(Thread):
    '''Event loop engine implement by thread'''
    def __init__(self, porto):
        super().__init__()
        self.porto = porto # protocol object
        self.CDC_response_only = Queue() # queue for response only packet
        self.CDC_request_response = Queue() # queue for request response packet
        self.response_cmd = set([]) # set of cmd that need response
        self.active = Event()
    def start(self):
        '''start thread'''
        self.active.set()
        super().start()

    def run(self):
        '''Event loop'''
        CDC_collection = CDCCollection()
        while self.active.is_set():
            try:
                recv_data = self.porto.recv(4096*2, time_out=10)
            except Exception as error:
                log.warning(error)
                self.stop()

            if recv_data == b'':
                continue

            packet = CDC_collection.collect(recv_data)

            if packet is not None:
                if packet[3] in self.response_cmd:
                    log.debug(f'to request response queue, cmd = {hex(packet[3])}')
                    self.CDC_request_response.put(packet)
                else:
                    log.debug(f'to response only queue, cmd = {hex(packet[3])}')
                    self.CDC_response_only.put(packet)

        log.info('event loop stopped')

    def send(self, data:bytes, *, cmd:Optional[int]=None):
        '''send data (cdc packet in bytes) to porto

        Args:
            data (bytes): cdc packet in bytes
            cmd (Optional[int], optional): command of packet. Defaults is None. If cmd is not None, add cmd which need response to Set "response_cmd".
        '''
        if cmd is not None:
            self.response_cmd.add(cmd)
        self.porto.send(data)

    def get_recv_queue(self,* ,response_only:bool=False)->Queue:
        '''
        get queue for response packet or request response packet

        Args:
            response_only (bool, optional): True for response packet only Queue, False for request response packet Queue.

        '''

        if response_only:
            return self.CDC_response_only
        else:
            return self.CDC_request_response

    def recv(self,* ,response_only:bool=False, time_out:Optional[float]=None)->bytes:
        '''get response cdc packet (bytes)

        Args:
            response_only (bool, optional): True for response packet only, False for request response packet. Defaults to False.
            time_out (Optional[float], optional): timeout in seconds. If None, wait forever. Defaults to None.
        '''
        return self.get_recv_queue(response_only=response_only).get(timeout=time_out)

    def stop(self):
        '''stop thread'''
        self.active.clear()
        self.join()
        self.porto.close()
    def connect(self, *args, **kwargs):
        '''connect to injected porto'''
        self.porto.connect(*args, **kwargs)
        self.start()
        # print(self.porto)
        time.sleep(1)

if __name__ == '__main__':
    HOST = '192.168.1.106'
    PORT = 7000
    porto = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    p = ThreadServerEngine(porto)
    p.connect(HOST, PORT)
    while True:
        text = input('input')
        if text == 'aa':
            p.send(b'\xaa')
            for i in range(10):
                data = p.recv(response_only=True)
                print(f'response of request:\n{data}')
        if text == 'bb':
            p.send(b'\xbb', cmd=0xbb)
            data = p.recv()
            print(f'response of request:\n{data}')
        elif text.lower() == 'q':
            p.send('q'.encode('utf-8'))
            break
        else:
            p.send(text.encode('utf-8'))

    print('end')
    p.stop()
    sys.exit()


