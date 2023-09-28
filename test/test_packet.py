from ksoc_wifi_connection.packet import Packet, get_CDC_packet, calculate_checksum

def test_packet():
    packet = Packet(direction='>', command=0x01, payload_length=0, payload=b'', checksum=0x00)
    assert packet.CDC_packet == b'$$>\x01\x00\x00\x00\x00'
    assert get_CDC_packet(packet.CDC_packet) == packet

def test_packet2():
    packet = Packet(direction='>', command=0x10, payload_length=3, payload=bytearray([0xa4,0xa5,0xa6]), checksum=0x08)
    assert packet.CDC_packet == b'$K>\x10\x00\x03\x00\xa4\xa5\xa6\x08'
    assert get_CDC_packet(packet.CDC_packet) == packet


def test_get_CDC_packet():
    packet = get_CDC_packet(b'$$>\x01\x00\x00\x00\x00')
    assert packet.CDC_packet == b'$$>\x01\x00\x00\x00\x00'
    assert get_CDC_packet(packet.CDC_packet) == packet

def test_calculate_checksum():
    packet = get_CDC_packet(b'$$>\x01\x00\x00\x00\x00')
    assert packet.checksum == calculate_checksum(packet.CDC_packet)
    assert packet.checksum == 0x00

def test_get_CDC_packet2():
    packet = get_CDC_packet(b'$K>\x10\x00\x03\x00\xa4\xa5\xa6\x08')
    assert packet.CDC_packet == b'$K>\x10\x00\x03\x00\xa4\xa5\xa6\x08'
    assert get_CDC_packet(packet.CDC_packet) == packet

def test_calculate_checksum2():
    packet = get_CDC_packet(b'$K>\x10\x00\x03\x00\xa4\xa5\xa6\x08')
    assert packet.checksum == calculate_checksum(packet.CDC_packet)
    assert packet.checksum == 0x08