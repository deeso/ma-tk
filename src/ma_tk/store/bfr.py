from .memory import MemoryObject

class BufferBacked(MemoryObject):

    def __init__(self, bytes_data, va_start: int, size: int, phy_start: int = 0, 
                 page_size: int = 4096, filename: str = None, flags: str = 0):
        super().__init__(va_start, phy_start, size, page_size=page_size, flags=flags) 
        self.va_end = self.va_start + size
        self.filename = filename if filename else 'anonymous'
        self.name = "{:016x}-{:016x}:bytes:{}".format(va_start, va_start+size, filename)   
        self.bytes_data = bytes_data
        self.pos = 0

    def _read (self, size=1, paddr=None):
        data = b''
        if paddr is None:
            paddr=self.pos
        
        if self.size-self.pos < size:
            size = self.size-self.pos
        data = self.bytes_data[paddr:paddr+size]
        self.pos = self.pos+len(data)
        if self.pos > self.size:
            self.pos = self.size
        return data

    def _seek(self, addr=None, offset=None, phy_addr=None):
        r = False
        if addr is not None and self.va_start <= addr and \
           addr < self.va_start + self.size:
            self.pos = vaddr - self.va_start
            r = True
        elif offset is not None and self.pos + offset >= 0 and self.pos + offset < self.size:
            self.pos = offset + self.pos
            r = True
        elif phy_addr is not None and self.phy_start <= phy_addr and \
           phy_addr < self.phy_start + self.size:
            self.pos = phy_addr - self.phy_start
            r = True
        return r