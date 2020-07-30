import os
import uuid
import ctypes
import struct
import copy

from .. consts import *

from .. import util as util

class MemoryObject(object):

    def __init__(self, va_start: int, phy_start: int, size: int, 
                 page_size: int=4096, flags: int = 0):
        self.size = size
        self.va_start = va_start
        self.phy_start = phy_start

        self.page_size = page_size
        self.page_mask = util.get_page_mask(page_size)
        self.page_cache = {i & self.page_mask for i in range(self.va_start, 
                                            self.va_start + self.size, 
                                            self.page_size)}
        
        self.name = "{:016x}-{:016x}:anonymous".format(va_start,va_start+size)
        self.flags = flags

    def get_va_start(self):
        return self.va_start

    def get_name(self):
        return self.name

    def calc_page(self, va):
        return va & self.page_mask

    def has(self, va: int):
        return self.va_start <= va and va < self.va_start + self.size  

    def get_page_cache(self):
        return self.page_cache

    def translate_paddr_to_offset(self, paddr):
        if not self.check_paddr(paddr):
            return None
        return paddr - self.phy_start
    
    def translate_vaddr_to_offset(self, vaddr):
        if not self.has(vaddr):
            return None
        return vaddr - self.va_start

    def translate_offset_to_vaddr(self, offset):
        # offset is less that physical start or exceeds the memory map
        if not self.check_offset(offset):
            return None
        return offset + self.va_start

    def translate_offset_to_paddr(self, offset):
        # offset is less that physical start or exceeds the memory map
        if not self.check_offset(offset):
            return None
        return offset + self.phy_start

    def translate_paddr_to_vaddr(self, paddr):
        # offset is less that physical start or exceeds the memory map
        offset = self.translate_paddr_to_offset(paddr)
        return offset if offset is None else self.va_start + offset

    def translate_vaddr_to_paddr(self, vaddr):
        # offset is less that physical start or exceeds the memory map
        offset = self.translate_vaddr_to_offset(vaddr)
        return offset if offset is None else self.phy_start + offset

    def check_paddr(self, paddr):
        return self.check_offset(paddr - self.phy_start)

    def check_vaddr(self, vaddr):
        return self.has(vaddr)

    def check_offset(self, offset):
        # offset is less that physical start or exceeds the memory map
        return  self.phy_start <= offset and offset < (self.phy_start + self.size)

    def read_vaddr(self, vaddr: int, size: int = 1):
        paddr = self.translate_vaddr_to_paddr(va)
        if not self.check_paddr(paddr+size):
            return None
        return self.read(paddr, size)

    def read_paddr(self, paddr: int, size: int = 1):
        if self.check_paddr(paddr) and \
           not self.check_paddr(paddr+size):
            return None
        return self.read(paddr, size)

    def get_size(self):
        return self.size

    def vaddr_in_range (self, vaddr):
        return self.has(vaddr)

    def paddr_in_range (self, paddr):
        return self.check_paddr(paddr)

    def can_read (self, offset, len_):
        if not self.check_offset(offset) or not self.check_offset(offset+len_):
            return False 
        return True

    def __getstate__(self):
        odict = copy.deepcopy(self.__dict__)
        return odict

    def __str__ (self):
        #return "filename: %s start: 0x%08x end: 0x%08x"%(self.filename, self.start, self.end)
        ps = util.get_perms_str(self.flags)
        return "0x{:016x}-0x{:016x} {}".format(self.va_start, self.va_start + self.size, ps )

    def __setstate__(self, _dict):
        self.__dict__.update(_dict)

    def get_pos_as_vaddr (self):
        return self.va_start + self.pos

    def get_pos_as_paddr (self):
        return self.phy_start + self.pos

    def name (self):
        return self.filename

    def read(self, size, paddr=None):
        if paddr is None:
            paddr = self.pos
        return self._read(size, paddr)

    def read_at_vaddr(self, addr, size):
        offset = self.translate_vaddr_to_offset(addr)
        if offset is None:
            return None
        return self.read(size, offset)

    def read_at_paddr(self, addr, size):
        offset = self.translate_paddr_to_offset(addr)
        if offset is None:
            return None
        return self.read(size, offset)

    def seek(self, addr=None, offset=None, phy_addr=None):
        return self._seek(addr=addr, offset=offset, phy_addr=phy_addr)

    def _seek(self, addr=None, offset=None, phy_addr=None):
        raise Exception("Not implemented")

    def get_current_pos(self):
        return self.pos

    def get_current_vaddr(self):
        return self.pos + self.va_start

    ######################## Read word operations
    def read_word(self, addr=None, offset=None, littleendian = True, signed=False):
        if not addr is None:
            return self.read_word_at_vaddr(addr, littleendian, signed)
        elif not offset is None:
            return self.read_word_at_offset(offset, littleendian, signed)
        else:
            return self.read_word_at_offset(self.pos, littleendian, signed)

    def read_word_at_vaddr(self, addr, littleendian=True, signed=False):
        offset = self.translate_vaddr_to_offset(addr)
        if offset is None:
            return None
        return self.read_word_at_offset(offset, littleendian, signed)

    def read_word_at_offset(self, offset, littleendian=True, signed=False):
        if offset is None or not self.check_offset(offset) and \
           not self.check_offset(offset+2):
            return None
        result = self.read(2, offset)
        if len(result) != 2:
            return None


        fmt = 'h' if signed else 'H'
        endian = '<' if littleendian else '>'
        if littleendian:
            return struct.unpack("{}{}".format(endian, fmt), result)[0]
        else:
            return struct.unpack("{}{}".format(endian, fmt), result)[0]


    ######################## Read dword operations
    def read_dword(self, addr=None, offset=None, littleendian = True, signed=False):
        if not addr is None:
            return self.read_dword_at_vaddr(addr, littleendian, signed)
        elif not offset is None:
            return self.read_dword_at_offset(offset, littleendian, signed)
        else:
            return self.read_dword_at_offset(self.pos, littleendian, signed)

    def read_dword_at_vaddr(self, addr, littleendian=True, signed=False):
        offset = self.translate_vaddr_to_offset(addr)
        if offset is None:
            return None
        return self.read_dword_at_offset(offset, littleendian, signed)

    def read_dword_at_offset(self, offset, littleendian=True, signed=False):
        if offset is None or not self.check_offset(offset) and \
           not self.check_offset(offset+2):
            return None
        
        result = self.read(4, offset)
        if len(result) != 4:
            return None

        fmt = 'i' if signed else 'I'
        endian = '<' if littleendian else '>'
        if littleendian:
            return struct.unpack("{}{}".format(endian, fmt), result)[0]
        else:
            return struct.unpack("{}{}".format(endian, fmt), result)[0]

    ######################## Read qword operations
    def read_qword(self, addr=None, offset=None, littleendian = True, signed=False):
        if not addr is None:
            return self.read_qword_at_vaddr(addr, littleendian, signed)
        elif not offset is None:
            return self.read_qword_at_offset(offset, littleendian, signed)
        else:
            return self.read_qword_at_offset(self.pos, littleendian, signed)

    def read_qword_at_vaddr(self, addr, littleendian=True, signed=False):
        offset = self.translate_vaddr_to_offset(addr)
        if offset is None:
            return None
        return self.read_qword_at_offset(offset, littleendian, signed)

    def read_qword_at_offset(self, offset, littleendian=True, signed=False):
        if not self.check_offset(offset) and \
           not self.check_offset(offset + 8):
            return None
        result = self.read(8, offset)

        fmt = 'q' if signed else 'Q'
        endian = '<' if littleendian else '>'
        if littleendian:
            return struct.unpack("{}{}".format(endian, fmt), result)[0]
        else:
            return struct.unpack("{}{}".format(endian, fmt), result)[0]

    ######################## Read ctype structure operations
    def read_cstruct(self, cstruct, addr=None, offset=None):
        if not addr is None:
            return self.read_cstruct_at_vaddr(addr, cstruct)
        elif not offset is None:
            return self.read_cstruct_at_offset(offset, cstruct)
        else:
            return self.read_cstruct_at_offset(self.pos, cstruct)

    def read_cstruct_klass_at_vaddr(self, addr, cstruct_klass):
        offset = self.translate_vaddr_to_offset(addr)
        if offset is None:
            return None
        return self.read_cstruct_at_offset(offset, cstruct_klass)

    def read_cstruct_at_offset(self, offset, cstruct, to_json=False):
        size = ctypes.sizeof(cstruct_klass)
        if not self.check_offset(offset) and \
           not self.check_offset(offset + size):
            return None
        result = self.read(size, offset)
        return self.bytes_to_struct(result, cstruct_klass)

    @classmethod
    def bytes_to_struct(cls, data, cstruct_klass):
        tmp = ctypes.cast(data, ctypes.POINTER(cstruct_klass)).contents
        # there is an odd bug, but the data gets corrupted if we
        # return directly after the cast, so we create a deep copy
        # and return that value
        # Note if there are any pointers in the struct it will fail
        # https://stackoverflow.com/questions/1470343/python-ctypes-copying-structures-contents
        dst = copy.deepcopy(tmp)
        return dst

    @classmethod
    def json_serialize_struct(strct):
        r = {}
        for f, ct in strct._fields_:
            v = getattr(strct, f)
            if isinstance(v, (ctypes.Structure, ctypes.Union)):
                r[f] = json_serialize_struct(v)
            else:
                r[f] = v
        return r

    def dump(self, filename=None, dump_path=None, block_size=512):

        if filename is None:
            filename = os.path.join(self.name, '.bin')

        if dump_path is None:
            dump_path = 'memory-dump-' + str(uuid.uuid4())

        if not os.path.exists(dump_path):
            os.makedirs(path, exist_ok=True)

        f = open(os.path.join(dump_path, filename), 'wb')
        offset = 0
        while offset < self.size:
            data = self.read(size, offset)
            if data is None or len(data) == b'':
                break
            f.write(data)
            offset += len(data)
        f.flush()
        f.close()
        return offset
