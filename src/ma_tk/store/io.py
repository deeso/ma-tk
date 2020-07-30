from .memory import MemoryObject
from threading import RLock

class IOBacked(MemoryObject):

    def __init__(self, io_obj, va_start: int, size: int, 
                 phy_start: int = 0, page_size: int = 4096, filename: str = None,
                 flags: int = 0):
        super().__init__(va_start, phy_start, size, page_size, flags) 
        self.va_end = va_end
        self.filename = filename if filename else 'anonymous'
        self.name = "{016:x}-{016:x}:file:{}".format(va_start, self.filename)   
        self.io_obj = io_obj
        self.pos = self.io_obj.tell()
        self.io_lock = RLock()

    def _read(self, size, paddr=None):
        # TODO try except finally needed here
        data = b''
        # self.io_lock.acquire()
        try:
            if paddr is None:
                paddr = self.pos
            if self.pos != paddr:
                self.io_obj.seek(paddr)
            data = self.io_obj.read(size)
            self.pos = pos+len(data)
        except:
            pass
        # finally:
        #     self.io_lock.release()
        return data