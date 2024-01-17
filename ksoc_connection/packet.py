from dataclasses import dataclass, field
from enum import Enum
from struct import pack, unpack, calcsize
from typing import List, Union, Optional, Tuple, Dict, Any, Callable, TypeVar, Generic, Type, cast, NewType


class Command(Enum):
    '''Command code for CDC packet.'''
    DEFAULT = 0x00
    GET_FIRMWARE_VERSION = 0x01
    GET_CHIP_ID = 0x08

    REG_WRITE = 0x10
    REG_WRITE_COMPARE = 0x11
    REG_READ = 0x12

    RFIC_REG_WRITE = 0x42
    RFIC_REG_WRITE_COMPARE = 0x43
    RFIC_REG_READ = 0x44

    MULTI_RESULTS_SWITCH = 0xAA
    MULTI_RESULTS_GET = 0xAB

    SWITCH_SPI_CHANNEL = 0x60

    STOP_POWER_STATE_MACHINE = 0x70

    SET_POWER_SAVING_MODE = 0x84
    GET_POWER_SAVING_MODE = 0x85

    SWITCH_COLLECTION_OF_MULTI_RESULTS = 0xAA
    GET_COLLECTION_OF_MULTI_RESULTS = 0xAB

class Direction(Enum):
    '''Direction of CDC packet.'''
    REQUEST = '>'
    RESPONSE = '<'

@dataclass
class Packet:
    '''CDC packet object.

    Attributes:
        start_frame (str): Start frame of CDC packet. Must be '$K'. ([0:1])
        channel (int): Channel number of CDC packet. Default is 1. ([2:2])
        direction (str): Direction of CDC packet. Default is '>'. ([3:3])
        command (int): Command code of CDC packet. Default is 0x00. ([4:4])
        payload_length (int): Payload length of CDC packet. Default is 0. ([5:6])
        payload (Union[bytearray,bytes]): Payload of CDC packet. Default is empty. ([7:payload_length+7])
        checksum (int): Checksum of CDC packet. Default is 0x00. ([payload_length+7+1:payload_length+7+1])
    '''
    # __slots__ = ['start_frame', 'channel', 'command', 'direction', 'payload_length', 'payload', 'checksum']
    direction: str
    command: int
    payload_length:int
    payload:Union[bytearray,bytes]
    checksum:int = 0x00
    def __post_init__(self):
        self.start_frame: str = '$K'
        self.channel: int = 1


    @property
    def CDC_packet(self)->bytes:
        '''CDC packet in bytes.'''
        packet = pack(f'=2s1s1B1b2s{self.payload_length}s1B',
                      self.start_frame.encode('utf-8'),
                      self.direction.encode('utf-8'),
                      self.command,
                      self.channel,
                      self.payload_length.to_bytes(2, byteorder='big', signed=False),
                      bytes(self.payload),
                      self.checksum,
                      )
        return packet

    def __repr__(self):
        return f'Packet(start_frame="{str(self.start_frame)}", direction="{str(self.direction)}",' \
               f' command={hex(self.command)}, payload_length={self.payload_length}, payload={self.payload}, checksum={hex(self.checksum)})'

    def update_checksum(self)->None:
        '''If checksum is not calculated, calculate checksum and update checksum of CDC packet before sending the request.'''
        if not self.validate_checksum():
            self.checksum = calculate_checksum(self.CDC_packet)

    def validate_checksum(self)->bool:
        '''Validate checksum of response CDC packet. True if checksum is correct, False if checksum is incorrect.'''
        return self.checksum == calculate_checksum(self.CDC_packet)

def calculate_checksum(packet:Union[bytes, bytearray])->int:
    '''Calculate checksum of CDC packet.'''
    payload_length = int.from_bytes(packet[5:7], byteorder='big', signed=False)
    return ~(sum(packet[3:-1]))+1 & 0xFF # 2 complement of sum of bytes from command to payload


def get_CDC_packet(packet:Union[bytes, bytearray])->Packet:
    '''Get CDC packet object from bytes.'''
    packet = bytes(packet)
    start_frame = packet[0:2].decode('utf-8')
    assert start_frame == '$K', f'{start_frame}'
    direction = packet[2:3].decode('utf-8')
    command = int.from_bytes(packet[3:4], byteorder='big', signed=False)
    payload_length = int.from_bytes(packet[5:7], byteorder='big', signed=False)
    payload = packet[7:7+payload_length]
    checksum = packet[-1]
    return Packet(direction, command, payload_length, payload, checksum)


if __name__ == '__main__':
    packet = Packet(direction=Direction.RESPONSE.value, command=0xab, payload_length=(8192+2)*2, payload=bytearray((8192+2)*2), checksum=0x08)
    packet.update_checksum()
    print(packet)
    print(packet.CDC_packet)





