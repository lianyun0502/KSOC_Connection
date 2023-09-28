import time
from enum import Enum
from typing import Any, Union, Optional, Tuple, Dict, Callable, TypeVar, Generic, Type, cast, NewType, Sequence
from .packet import Packet, Command, Direction, get_CDC_packet
from .connection import *


class KKTClassStatus(Enum):
    KKT_SUCCESS = 0
    KKT_ERROR_ACCESS_DENIED = 1
    KKT_ERROR_DRIVER_INIT_FAILED = 2
    KKT_ERROR_DEVICE_INFO_FETCH_FAILED = 3
    KKT_ERROR_DRIVER_OPEN_FAILED = 4
    KKT_ERROR_INVALID_PARAMETER = 5
    KKT_ERROR_REQUEST_FAILED = 6
    KKT_ERROR_DOWNLOAD_FAILED = 7
    KKT_ERROR_FIRMWARE_INVALID_SIGNATURE = 8
    KKT_ERROR_INVALID_FIRMWARE = 9
    KKT_ERROR_DEVICE_NOT_FOUND = 10
    KKT_ERROR_IO_TIMEOUT = 11
    KKT_ERROR_PIPE_HALTED = 12
    KKT_ERROR_BUFFER_OVERFLOW = 13
    KKT_ERROR_INVALID_HANDLE = 14
    KKT_ERROR_ALLOCATION_FAILED = 15
    KKT_ERROR_I2C_DEVICE_BUSY = 16
    KKT_ERROR_I2C_NAK_ERROR = 17
    KKT_ERROR_I2C_ARBITRATION_ERROR = 18
    KKT_ERROR_I2C_BUS_ERROR = 19
    KKT_ERROR_I2C_BUS_BUSY = 20
    KKT_ERROR_I2C_STOP_BIT_SET = 21
    KKT_ERROR_STATUS_MONITOR_EXIST = 22
    KKT_ERROR_FAILURE = 23

    KKT_ERROR_FILE_PATH_INVALIDATION = 24
    KKT_ERROR_FILENAME_INVALIDATION = 25
    KKT_ERROR_FILE_OPEN_CREATE_ERROR = 26
    KKT_ERROR_FILE_NOT_FOUND = 27
    KKT_ERROR_SIZE_ERROR = 28
    KKT_ERROR_PARSING_ERROR = 29
    KKT_ERROR_WRITE_ERROR = 30
    KKT_ERROR_READ_ERROR = 31
    KKT_ERROR_COMPARE_ERROR = 32
    KKT_ERROR_ARGUMENTS_ERROR = 33
    KKT_ERROR_TIMEOUT_ERROR = 34
    KKT_ERROR_CONFIG_ERROR = 35
    KKT_ERROR_DEVICE_FAILED = 36
    KKT_ERROR_DEVICE_CONFIG_FAILED = 37
    KKT_ERROR_DATA_NOT_READY = 38
    KKT_ERROR_CMD_ERROR = 39
    KKT_ERROR_USUALLY_FOR_RECIVING_TIMEOUT = 40
    KKT_ERROR_WIN_API_WRITE_FILE = 41
    KKT_ERROR_WIN_API_READ_FILE = 42
    KKT_ERROR_WIN_API_READ_ZERO_SIZE = 43
    KKT_ERROR_FIRMWARE_INTERNAL_CODE = 44
    KKT_ERROR_PHASE_K_CALIBRATION_FAILED = 45
    KKT_ERROR_EFUSE_CAL_FAIL = 46
    KKT_ERROR_EFUSE_PROGRAMMING_FAIL = 47
    KKT_ERROR_EFUSE_FT_FAIL = 48

    def __init__(self):
        self.connection = KKTVComPortConnection(timeout=1)

    def connectDevice(self, device:str='WIFI')->KKTClassStatus:
        if device.upper() != 'WIFI':
            return KKTClassStatus.KKT_ERROR_DEVICE_NOT_FOUND
        HOST = '192.168.88.1'
        PORT = 80
        try:
            self.connection.connect(host=HOST, port=PORT)
        except Exception as e:
            print(e)
            return KKTClassStatus.KKT_ERROR_DRIVER_INIT_FAILED

        self.switchSPIChannel(1)

        return KKTClassStatus.KKT_SUCCESS

    def switchSPIChannel(self, channel:int)->KKTClassStatus:
        request = Packet(direction=Direction.REQUEST.value, command=Command.SWITCH_SPI_CHANNEL.value, payload_length=4, payload=bytes([0,0,0,channel]), checksum=0x9A)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def disconnectDevice(self)->KKTClassStatus:
        try:
            self.connection.close()
        except Exception as e:
            print(e)
            return KKTClassStatus.KKT_ERROR_DRIVER_INIT_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def getChipID(self)->Tuple[KKTClassStatus, str]:
        request = Packet(direction=Direction.REQUEST.value, command=Command.GET_CHIP_ID.value, payload_length=0, payload=b'', checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        return KKTClassStatus.KKT_SUCCESS, response.payload.decode('utf-8')

    def getFirmwareVersion(self)->Tuple[KKTClassStatus, str]:
        request = Packet(direction=Direction.REQUEST.value, command=Command.GET_FIRMWARE_VERSION.value, payload_length=0, payload=b'', checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        return KKTClassStatus.KKT_SUCCESS, response.payload.decode('utf-8')

    def setPowerSavingMode(self, mode:int)->KKTClassStatus:
        '''
        mode:
            0: Disable Mode
            1: Sniff Mode
            2: Gesture Mode
            3: Motion Mode
            4: Stop Mode (Sleep Mode)
            5: Deep Sleep Mode
        '''
        request = Packet(direction=Direction.REQUEST.value, command=Command.SET_POWER_SAVING_MODE.value, payload_length=1, payload=bytes([mode]), checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def getPowerSavingMode(self)->Tuple[KKTClassStatus, int]:
        request = Packet(direction=Direction.REQUEST.value, command=Command.GET_POWER_SAVING_MODE.value, payload_length=0, payload=b'', checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED, 0
        return KKTClassStatus.KKT_SUCCESS, int.from_bytes(response.payload, byteorder='big', signed=False)

    def stopPowerStateMachine(self, is_stop:int)->KKTClassStatus:
        '''
        :param is_stop: 0: Start, 1: Stop
        :return:
        '''
        payload = is_stop.to_bytes(1, byteorder='big')
        request = Packet(direction=Direction.REQUEST.value, command=Command.STOP_POWER_STATE_MACHINE.value, payload_length=1, payload=payload, checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def readHWRegister(self, addr:int)->Tuple[KKTClassStatus, int]:

        payload = bytearray(8)
        payload[:4] = addr.to_bytes(4, byteorder='big')
        payload[4:] = 0x01.to_bytes(4, byteorder='big')

        request = Packet(direction=Direction.REQUEST.value, command=Command.REG_READ.value, payload_length=8, payload=payload, checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED, 0
        return KKTClassStatus.KKT_SUCCESS, int.from_bytes(response.payload, byteorder='big')

    def writeHWRegister(self, addr:int, value:int)->KKTClassStatus:
        request = Packet(direction=Direction.REQUEST.value, command=Command.REG_WRITE.value, payload_length=8, payload=addr.to_bytes(4, byteorder='little') + value.to_bytes(4, byteorder='little'), checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS


    def switchCollectionOfMultiResults(self,
                                       actions:int,
                                       read_interrupt:int,
                                       clear_interrupt:int,
                                       raw_size:int,
                                       ch_of_RBank:int,
                                       reg_address:Optional[Sequence[int]]=None,
                                       frame_setting:int=0)->KKTClassStatus:
        payload_length = 5
        if actions & 0b1 == 1:
            payload_length += 2
        if actions & 0b10 == 1:
            payload_length += 1
        if actions & 0b100 == 1:
            payload_length += 4 * (len(reg_address) + 1)
        if actions & 0b1000 == 1:
            payload_length += 2

        payload = bytearray(payload_length)

        payload[1:5] = actions.to_bytes(4, byteorder='big')
        offset = 5
        if actions & 0b1 == 1:
            payload[offset:offset+2] = raw_size.to_bytes(2, byteorder='big')
            offset += 2
        if actions & 0b10 == 1:
            payload[offset:offset+1] = ch_of_RBank.to_bytes(1, byteorder='big')
            offset += 1

        if actions & 0b100 == 1:
            payload[offset:offset+2] = len(reg_address).to_bytes(2, byteorder='big')
            offset += 2
            interrupt = (read_interrupt & 0b1)<<4 + (clear_interrupt & 0b1)
            payload[offset:offset+1] = interrupt.to_bytes(1, byteorder='big')
            offset += 1
            for reg in reg_address:
                payload[offset:offset+4] = reg.to_bytes(4, byteorder='big')
                offset += 4

        if actions & 0b1000 == 1:
            payload[offset:offset+2] = frame_setting.to_bytes(2, byteorder='big')
            offset += 2

        request = Packet(direction=Direction.REQUEST.value, command=Command.SWITCH_COLLECTION_OF_MULTI_RESULTS.value,
                         payload_length=payload_length, payload=payload, checksum=0xF7)
        request.update_checksum()
        self.connection.sendCDCPacket(request.CDC_packet)
        response = self.connection.receiveCDCPacket()
        response = get_CDC_packet(response)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS


    def getMultiResults(self)->Union[KKTClassStatus, Tuple[KKTClassStatus, Dict[int, bytes]]]:
        response = self.connection.receiveCDCPacket(Command.GET_COLLECTION_OF_MULTI_RESULTS.value, response_only=True)
        response = get_CDC_packet(response)
        if response.command != Command.GET_COLLECTION_OF_MULTI_RESULTS.value:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED

        actions = int.from_bytes(response.payload[1:4], byteorder='big')
        print(f'actions : {bin(actions)}')
        offset = 5
        data_dict:Dict[int, bytes] = {}
        while offset < len(response.payload):
            action_num = int.from_bytes(response.payload[offset:offset+1], byteorder='big', signed=True)
            data_length = int.from_bytes(response.payload[offset+2:offset+4], byteorder='big', signed=True)
            print(f'action_num : {action_num}, data_length : {data_length}')
            data = response.payload[offset+4:offset+4+data_length]
            data_dict.update({action_num: data})
            offset += 4 + data_length

        return KKTClassStatus.KKT_SUCCESS, data_dict

class KKTIntegration:
    def __init__(self, connection:KKTConnection):
        self.connection = connection

    def __del__(self):
        self.disconnectDevice()
    def connectDevice(self, *args, **kwargs)->KKTClassStatus:
        try:
            self.connection.connect(*args, **kwargs)
        except Exception as e:
            print(e)
            return KKTClassStatus.KKT_ERROR_DRIVER_INIT_FAILED

        self.switchSPIChannel(1)

        return KKTClassStatus.KKT_SUCCESS

    def disconnectDevice(self)->KKTClassStatus:
        try:
            self.connection.close()
        except Exception as e:
            print(e)
            return KKTClassStatus.KKT_ERROR_DRIVER_INIT_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def setCustomCDCPacket(self, direction:bytes, command:bytes, payload_len:bytes, payload:bytes)->Tuple[KKTClassStatus, bytes]:

        assert direction in [b'>', b'<'] and len(direction) == 1, f'direction must be ">" or "<", but got {direction}'
        assert len(command) == 1, f'command must be 1 byte, but got {command}'
        assert len(payload_len) == 2, f'payload_len must be 2 bytes, but got {payload_len}'
        assert len(payload) == int.from_bytes(payload_len, byteorder='big'),\
            f'payload length must be {int.from_bytes(payload_len, byteorder="big")}, but got {len(payload)}'

        request = Packet(direction=direction.decode(), command=int.from_bytes(command, byteorder='big'),
                         payload_length=int.from_bytes(payload_len, byteorder='big'), payload=payload)
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED, b''
        return KKTClassStatus.KKT_SUCCESS, response.CDC_packet

    def switchSPIChannel(self, channel:int)->KKTClassStatus:
        request = Packet(direction=Direction.REQUEST.value, command=Command.SWITCH_SPI_CHANNEL.value, payload_length=4, payload=bytes([0,0,0,channel]))
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def getChipID(self)->Tuple[KKTClassStatus, str]:
        request = Packet(direction=Direction.REQUEST.value, command=Command.GET_CHIP_ID.value, payload_length=0, payload=b'', checksum=0xF7)
        response = self.connection.sendCDCPacketWithResponse(request)
        return KKTClassStatus.KKT_SUCCESS, response.payload.decode('utf-8')

    def getFirmwareVersion(self)->Tuple[KKTClassStatus, str]:
        request = Packet(direction=Direction.REQUEST.value, command=Command.GET_FIRMWARE_VERSION.value, payload_length=0, payload=b'', checksum=0xF7)
        response = self.connection.sendCDCPacketWithResponse(request)
        return KKTClassStatus.KKT_SUCCESS, response.payload.decode('utf-8')

    def setPowerSavingMode(self, mode:int)->KKTClassStatus:
        '''
        mode:
            0: Disable Mode
            1: Sniff Mode
            2: Gesture Mode
            3: Motion Mode
            4: Stop Mode (Sleep Mode)
            5: Deep Sleep Mode
        '''
        request = Packet(direction=Direction.REQUEST.value, command=Command.SET_POWER_SAVING_MODE.value, payload_length=1, payload=bytes([mode]), checksum=0xF7)
        request.update_checksum()
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def getPowerSavingMode(self)->Tuple[KKTClassStatus, int]:
        request = Packet(direction=Direction.REQUEST.value, command=Command.GET_POWER_SAVING_MODE.value, payload_length=0, payload=b'', checksum=0xF7)
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED, 0
        return KKTClassStatus.KKT_SUCCESS, int.from_bytes(response.payload, byteorder='big', signed=False)

    def stopPowerStateMachine(self, on_stop:bool)->KKTClassStatus:
        '''
        :param is_stop: 0: Start, 1: Stop
        :return:
        '''
        payload = on_stop.to_bytes(1, byteorder='big')
        request = Packet(direction=Direction.REQUEST.value, command=Command.STOP_POWER_STATE_MACHINE.value, payload_length=1, payload=payload, checksum=0xF7)
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def readHWRegister(self, addr:int)->Tuple[KKTClassStatus, int]:

        payload = bytearray(8)
        payload[:4] = addr.to_bytes(4, byteorder='big')
        payload[4:] = 0x01.to_bytes(4, byteorder='big')

        request = Packet(direction=Direction.REQUEST.value, command=Command.REG_READ.value, payload_length=8, payload=payload)
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED, 0
        return KKTClassStatus.KKT_SUCCESS, int.from_bytes(response.payload, byteorder='big')

    def writeHWRegister(self, addr:int, value:int)->KKTClassStatus:
        request = Packet(direction=Direction.REQUEST.value, command=Command.REG_WRITE.value, payload_length=8, payload=addr.to_bytes(4, byteorder='little') + value.to_bytes(4, byteorder='little'), checksum=0xF7)
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED
        return KKTClassStatus.KKT_SUCCESS

    def switchCollectionOfMultiResults(self,
                                       actions:int,
                                       read_interrupt:int,
                                       clear_interrupt:int,
                                       raw_size:int,
                                       ch_of_RBank:int,
                                       reg_address:Optional[Sequence[int]]=None,
                                       frame_setting:int=0)->KKTClassStatus:
        payload_length = 5
        if actions & 0b1 == 1:
            payload_length += 2
        if actions & 0b10 == 1:
            payload_length += 1
        if actions & 0b100 == 1:
            payload_length += 4 * (len(reg_address) + 1)
        if actions & 0b1000 == 1:
            payload_length += 2

        payload = bytearray(payload_length)

        payload[1:5] = actions.to_bytes(4, byteorder='big')
        offset = 5
        if actions & 0b1 == 1:
            payload[offset:offset+2] = raw_size.to_bytes(2, byteorder='big')
            offset += 2
        if actions & 0b10 == 1:
            payload[offset:offset+1] = ch_of_RBank.to_bytes(1, byteorder='big')
            offset += 1

        if actions & 0b100 == 1:
            payload[offset:offset+2] = len(reg_address).to_bytes(2, byteorder='big')
            offset += 2
            interrupt = (read_interrupt & 0b1)<<4 + (clear_interrupt & 0b1)
            payload[offset:offset+1] = interrupt.to_bytes(1, byteorder='big')
            offset += 1
            for reg in reg_address:
                payload[offset:offset+4] = reg.to_bytes(4, byteorder='big')
                offset += 4

        if actions & 0b1000 == 1:
            payload[offset:offset+2] = frame_setting.to_bytes(2, byteorder='big')
            offset += 2

        request = Packet(direction=Direction.REQUEST.value, command=Command.SWITCH_COLLECTION_OF_MULTI_RESULTS.value,
                         payload_length=payload_length, payload=payload)
        response = self.connection.sendCDCPacketWithResponse(request)
        if response.command != request.command:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED

        if actions == 0: # clear queue
            q = self.connection.getQueue(recv_only=True)
            self.connection.clearQueue(q=q)

        return KKTClassStatus.KKT_SUCCESS

    def getMultiResults(self)->Union[KKTClassStatus, Tuple[KKTClassStatus, Dict[int, bytes]]]:
        response = self.connection.receiveCDCPacket(Command.GET_COLLECTION_OF_MULTI_RESULTS.value, response_only=True)
        response = get_CDC_packet(response)
        if response.command != Command.GET_COLLECTION_OF_MULTI_RESULTS.value:
            return KKTClassStatus.KKT_ERROR_REQUEST_FAILED

        # parsing
        actions = int.from_bytes(response.payload[1:4], byteorder='big')
        print(f'actions : {bin(actions)}')
        offset = 5
        data_dict:Dict[int, bytes] = {}
        while offset < len(response.payload):
            action_num = int.from_bytes(response.payload[offset:offset+1], byteorder='big', signed=True)
            data_length = int.from_bytes(response.payload[offset+2:offset+4], byteorder='big', signed=True)
            print(f'action_num : {action_num}, data_length : {data_length}')
            data = response.payload[offset+4:offset+4+data_length]
            data_dict.update({action_num: data})
            offset += 4 + data_length

        return KKTClassStatus.KKT_SUCCESS, data_dict


if __name__ == '__main__':
    integration = KKTIntegration(KKTVComPortConnection(timeout=1))
    integration.connectDevice()
    print(f'Chirp ID : {integration.getChipID()[1]}')
    read = integration.readHWRegister(0x50000530)
    print(f'read reg ({hex(0x50000504)}) : {read[0]} {hex(read[1])}')
    print(f'write reg ({hex(0x50000504)}) : {integration.writeHWRegister(0x50000504, 0x00000000)}')
    read = integration.readHWRegister(0x50000504)
    print(f'read reg ({hex(0x50000504)}) : {read[0]} {hex(read[1])}')
    # integration.setPowerSavingMode(2)
    # print(f'power saving mode: {integration.getPowerSavingMode()[1]}')
    integration.switchCollectionOfMultiResults(actions=0b1, read_interrupt=0, clear_interrupt=0, raw_size=(8192+2)*2, ch_of_RBank=1, reg_address=[])
    s = time.time_ns()
    for i in range(100):
        print(f'=================={i}==================')
        data = integration.getMultiResults()[1]
        print(f'getMultiResults : {data[0][:4].hex(" ")}')
        print(f'getMultiResults time : {(time.time_ns()-s)/1000000} ms')
        s = time.time_ns()


    print(integration.switchCollectionOfMultiResults(actions=0b0, read_interrupt=0, clear_interrupt=0, raw_size=(8192 + 2) * 2,
                                              ch_of_RBank=1, reg_address=[]))

    integration.disconnectDevice()