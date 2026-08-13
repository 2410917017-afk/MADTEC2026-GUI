from snap7.util import get_bool, get_dword, get_int, get_real, set_bool, set_int


def write_int(plc, db_number, byte_offset, value: int):
    data = bytearray(2)
    set_int(data, 0, value)
    plc.db_write(db_number, byte_offset, data)


def read_int_array(plc, db_number, start_byte, count):
    data = plc.db_read(db_number, start_byte, size=count * 2)
    return [get_int(data, index * 2) for index in range(count)]

def read_byte_array(plc, db_number, start_byte, count):
    data = plc.db_read(db_number, start_byte, size=count)
    return data

def read_dword_array(plc, db_number, start_byte, count):
    data = plc.db_read(db_number, start_byte, size=count * 4)
    return [get_dword(data, index * 4) for index in range(count)]


def read_real_array(plc, db_number, start_byte, count):
    data = plc.db_read(db_number, start_byte, size=count * 4)
    return [get_real(data, index * 4) for index in range(count)]


def read_bool(plc, db_number, byte_offset, bit):
    data = plc.db_read(db_number, byte_offset, 1)
    return get_bool(data, 0, bit)


def write_bool(plc, db, byte_offset, bit, value: bool):
    data = plc.db_read(db, byte_offset, 1)
    set_bool(data, 0, bit, value)
    plc.db_write(db, byte_offset, data)
