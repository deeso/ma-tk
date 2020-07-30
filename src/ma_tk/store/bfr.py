from .memory import MemoryObject

class BufferBacked(MemoryObject):

    def __init__(self, bytes_obj, va_start: int, size: int, phy_start: int = 0, 
                 page_size: int = 4096, filename: str = None, flags: str = 0):
        super().__init__(va_start, phy_start, size, page_size, flags) 
        self.va_end = va_end
        self.name = "{016:x}-{016:x}:bytes:{}".format(va_start, filename)   
        self.filename = filename if filename else str("{}:0x{:08x}-0x{:08x}".format('byte_array', va_start, va_end))
        self.bytes_obj = bytes_obj
        self.pos = 0

    def _read (self, size=1, paddr=None):
        data = b''
        if paddr is None:
            paddr=self.pos
        if size > self.size-pos:
            size = self.size-pos
        data = self.fdata[paddr:paddr+size]
        self.pos = pos+len(data)
        return data