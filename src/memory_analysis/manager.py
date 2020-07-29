from .store.io import IOBacked
from .store.buffer import BufferBacked


class Manager(object):

    def __init__(self, **kargs):
        self.maps = []
        self.maps_by_name = {}
        self.maps_by_page = {}

        self.known_pages = set()
        self.page_size = kargs.get('page_size', 4096)
        self.page_mask = util.get_page_mask(self.page_size)

    def calc_page(self, vaddr):
        return self.page_mask & vaddr

    def does_map_exist(self, vastart, filename, name, bm):
        if len(bm.get_page_cache() & self.known_pages) > 0:
            return True
        return False

    def add_iomap(self, filename, va_start, size, offset=0, flags=0, page_size=4096):
        phy_start = offset
        ibm = IOBacked(io_obj, va_start, size, phy_start, page_size, filename, flags)
        
        if check_presence(ibm):
            del ibm
            io_obj.close()
            return None
        self.add_map_to_kb(ibm)
        return ibm

    def add_buffermap(self, bytes_obj, va_start, size, filename=None, offset=0, flags=0, page_size=4096):
        phy_start = offset
        bbm = BufferBacked(bytes_obj, va_start, len(size), phy_start=offset, 
                            page_size=flags, filename=filename, flags=flags)
        
        if check_presence(bbm):
            del bbm
            return None
        self.add_map_to_kb(bbm)
        return bbm

    def add_null_buffermap(self, va_start, size, filename=None, offset=0, flags=0, page_size=4096):
        bytes_obj = b'\x00' * size
        phy_start = offset
        bbm = BufferBacked(bytes_obj, va_start, len(size), phy_start=offset, 
                            page_size=flags, filename=filename, flags=flags)
        
        if check_presence(bbm):
            del bbm
            io_obj.close()
            return None
        self.add_map_to_kb(bbm)
        return bbm

    def add_map_to_kb(self, bm):
        name = bm.get_name()
        pc = bm.get_page_cache()
        
        if self.check_presence(bm):
            return False

        self.known_pages = self.known_pages | pc
        for p in pc:
            self.maps_by_page[pc] = bm
        self.maps_by_name[name] = bm
        return True

    def remove_map_from_kb(self, bm):
        name = bm.get_name()
        pc = bm.get_page_cache()
        
        if not self.check_presence(bm):
            return True

        self.known_pages = {i for i in self.known_pages if i not in pc}        

        for p in pc:
            del self.maps_by_page[pc]

        del self.maps_by_name[name]
        return True


    def check_presence(self, bm=None, name=None, vaddr=None):
        if vaddr and \
           (vaddr in self.known_pages or vaddr in self.maps_by_page):
           return True

        if name and \
           (name in self.maps_by_name):
           return True

        if bm is not None:
            name = bm.get_name()
            pc = bm.get_page_cache()

            return len(pc & self.known_pages) > 0 or \
                   name in self.maps_by_name
        return False

    def get_page(self, vaddr):
        page = self.calc_page(vaddr)
        if page in self.known_pages and page in self.maps_by_page:
            return self.maps_by_page[page]
        return None

    

