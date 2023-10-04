from ksoc_connection.packet import Packet, get_CDC_packet, calculate_checksum
import pytest

@pytest.mark.unfinished
def test_packet():
    packet = Packet(direction='>', command=0x01, payload_length=0, payload=b'', checksum=0x00)
    assert packet.CDC_packet == b'$K>\x01\x01\x00\x00\x00'
    assert get_CDC_packet(packet.CDC_packet) == packet

@pytest.mark.finished
def test_packet2():
    packet = Packet(direction='>', command=0x10, payload_length=3, payload=bytearray([0xa4,0xa5,0xa6]), checksum=0x08)
    assert packet.CDC_packet == b'$K>\x10\x01\x00\x03\xa4\xa5\xa6\x08'
    assert get_CDC_packet(packet.CDC_packet) == packet

@pytest.mark.finished
def test_calculate_checksum():
    packet = get_CDC_packet(b'$K>\x01\x00\x00\x00\x00')
    assert packet.checksum == 0x00
    assert calculate_checksum(packet.CDC_packet) == 254

@pytest.mark.finished
def test_get_CDC_packet():
    packet = get_CDC_packet(b'$K>\x10\x00\x00\x03\xa4\xa5\xa6\x08')
    assert packet.direction == '>'
    assert packet.payload_length == 3
    assert len(packet.payload) == packet.payload_length
    assert packet.payload == bytearray([0xa4,0xa5,0xa6])
    assert packet.checksum == 0x08
    assert packet.command == 0x10
    assert packet.CDC_packet == b'$K>\x10\x01\x00\x03\xa4\xa5\xa6\x08'
    assert get_CDC_packet(packet.CDC_packet) == packet
