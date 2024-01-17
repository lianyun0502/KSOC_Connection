from ksoc_connection import *
import time

HOST = '192.168.2.1'
PORT = 80

if __name__ == '__main__':
    with KKTIntegration(KKTVComPortConnection(timeout=1)) as integration:
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
        for i in range(20):
            print(f'=================={i}==================')
            data = integration.getMultiResults()[1]
            print(f'getMultiResults : {data[0][:4].hex(" ")}')
            print(f'getMultiResults time : {(time.time_ns()-s)/1000000} ms')
            s = time.time_ns()


        print(integration.switchCollectionOfMultiResults(actions=0b0, read_interrupt=0, clear_interrupt=0, raw_size=(8192 + 2) * 2,
                                                  ch_of_RBank=1, reg_address=[]))

    # integration.disconnectDevice()

