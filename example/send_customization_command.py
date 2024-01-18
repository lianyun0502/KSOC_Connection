from ksoc_connection import *
from ksoc_connection.logger import log
import logging

HOST = '192.168.2.1'
PORT = 80

log.setLevel(logging.INFO)
if __name__ == '__main__':
    with KKTIntegration(KKTVComPortConnection(timeout=1)) as integration:
        integration.connectDevice()
        print(f'Chirp ID : {integration.getChipID()[1]}')

        res = integration.setCustomCDCPacket(direction=b'>',
                                             command=b'\x12',
                                             payload_len=b'\x00\x08',
                                             payload=b'\x50\x00\x05\x30\x00\x00\x00\x01',
                                             )
        print(f'response : {res[1].hex(" ")}')