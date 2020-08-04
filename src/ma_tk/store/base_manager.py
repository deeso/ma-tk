from st_log.st_log import Logger
from .. import util
import logging

class BaseManager(object):

    def __init__(self, **kargs):
        self.maps = []
        self.maps_by_name = {}
        self.maps_by_page = {}

        self.vaddr_pos = 0
        self.page_cache = set()
        self.page_size = kargs.get('page_size', 4096)
        self.page_mask = util.get_page_mask(self.page_size)
        self.logger = Logger("matk.store.base_manager.BaseManager", level=kargs.get('loglevel', logging.INFO))


    def get_map(self, vaddr):
        self.logger.debug("get_map retrieving vaddr: {:08x}".format(vaddr))
        if not self.check_presence(vaddr=vaddr):
            return None
        return self.maps_by_page[self.calc_page(vaddr)]

    def add_map_to_kb(self, bm):
        name = bm.get_name()
        pc = bm.get_page_cache()
        self.logger.debug("add_map_to_kb adding memory map {} {:08x}-{:08x}".format(name, bm.get_start(), bm.get_end()))
        if self.check_presence(bm):
            return False
        self.vaddr_pos = bm.get_va_start()
        self.page_cache = self.page_cache | pc
        for p in pc:
            self.maps_by_page[p] = bm
        self.maps_by_name[name] = bm
        return True

    def remove_map_from_kb(self, bm):
        name = bm.get_name()
        self.logger.debug("remove_map_from_kb adding memory map {} {:08x}-{:08x}".format(name, bm.get_start(), bm.get_end()))
        pc = bm.get_page_cache()
        
        if not self.check_presence(bm):
            return True

        self.page_cache = {i for i in self.page_cache if i not in pc}        

        for p in pc:
            del self.maps_by_page[pc]

        del self.maps_by_name[name]
        return True

    def get_vaddr_pos(self):
        return self.vaddr_pos

    def check_presence(self, bm=None, name=None, vaddr=None):
        page = self.calc_page(vaddr) if vaddr else None
        result = False
        how = 'Failed'
        if page and \
           (page in self.page_cache or page in self.maps_by_page):
           result = True
           how = "page: {:08x}".format(page)

        if name and \
           (name in self.maps_by_name):
           result = True
           how = "name: {}".format(name)

        if bm is not None:
            name = bm.get_name()
            pc = bm.get_page_cache()
            result = len(pc & self.page_cache) > 0 or \
                     name in self.maps_by_name
            how = "memory map: {:08x} {}".format(bm.get_start(), name)
        
        self.logger.debug("check_presence for memory map {} {}".format(result, how))
        return result

    def get_page(self, vaddr):
        return self.calc_page(vaddr)

    def get_page_cache(self):
        return self.page_cache
    
    def translate_vaddr_to_offset(self, vaddr):
        bm = self.get_map(vaddr)
        self.logger.debug("translate_vaddr_to_offset Translated addr {:08x} to {}".format(vaddr, bm))
        if bm is None:
            return None
        return bm, bm.translate_vaddr_to_offset(vaddr)

    def translate_vaddr_to_paddr(self, vaddr):
        bm = self.get_map(vaddr)
        self.logger.debug("translate_vaddr_to_paddr Translated addr {:08x} to {}".format(vaddr, bm))
        if bm is None:
            return None

        return bm, bm.translate_vaddr_to_paddr(vaddr)

    def seek(self, addr=None, offset=None):
        bm = None
        r = False
        if addr is not None:
            bm = self.get_map(addr)
            self.logger.debug("seek to position: addr: {:08x} {}".format(addr, bm))
        elif offset is not None:
            addr = self.vaddr_pos+offset
            bm = self.get_map(addr)
            self.logger.debug("seek to position: addr: {:08x} {}".format(addr, bm))
        if bm is not None:
            r = bm.seek(offset=offset)
            self.logger.debug("seek moved to position: addr: {:08x} {}".format(addr, bm))
            if r:
                self.vaddr_pos = bm.get_current_vaddr()
        return r

    def check_vaddr(self, vaddr):
        return self.check_presence(vaddr)

    def read(self, size, addr=None, offset=None):
        # FIXME data does not read across memory boundaries
        addr = self.vaddr_pos if addr is None and offset is None else addr
        self.logger.debug("read {} bytes @ addr: {:08x}".format(size, addr))
        if not addr is None:
            return self.read_at_vaddr(addr, size)
        elif offset is not None:
            vaddr = offset + self.vaddr_pos
            bm = self.get_map(offset + self.vaddr_pos)
            if bm is None:
                return None
            data = bm.read_at_vaddr(vaddr, size)
            self.vaddr_pos = bm.get_current_vaddr()
            return data
        return None


    def read_at_vaddr(self, vaddr: int, size: int = 1):
        # TODO does this read cross a boundary?
        # FIXME
        bm = self.get_map(vaddr)
        if bm is None:
            return None
        data = bm.read_at_vaddr(vaddr, size)
        self.vaddr_pos = bm.get_current_vaddr()
        return data

    def vaddr_in_range(self, vaddr):
        return self.check_presence(vaddr)

    def can_read(self, vaddr, len_):
        if not self.check_presence(vaddr) or not self.check_presence(offset+len_):
            return False 
        return True

    def get_vaddr(self):
        return self.vaddr_pos

    def name (self):
        return self.name


    ######################## Read word operations
    def read_word(self, addr=None, littleendian = True):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None
        data = bm.read_word(addr=addr, littleendian=littleendian)
        self.vaddr_pos = bm.get_current_vaddr()
        return data


    ######################## Read dword operations
    def read_dword(self, addr=None, littleendian = True):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None        
        data = bm.read_dword(addr=addr, littleendian=littleendian)
        self.vaddr_pos = bm.get_current_vaddr()
        return data

    ######################## Read qword operations
    def read_qword(self, addr=None, littleendian = True):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None        
        data = bm.read_qword(addr=addr, littleendian=littleendian)
        self.vaddr_pos = bm.get_current_vaddr()
        return data

    ######################## Read ctype structure operations
    def read_cstruct(self, cstruct_klass, addr=None):
        addr = self.vaddr_pos if addr is None else addr
        bm = self.get_map(addr)
        if bm is None:
            return None
        data = bm.read_cstruct(cstruct_klass, addr)
        self.vaddr_pos = bm.get_current_vaddr()
        return data


    def dump(self, filename=None, dump_path=None, block_size=512):
        # TODO dump all the files
        pass
        # if filename is None:
        #     filename = os.path.join(self.name, '.bin')

        # if dump_path is None:
        #     dump_path = 'memory-dump-' + str(uuid.uuid4())

        # if not os.path.exists(dump_path):
        #     os.makedirs(path, exist_ok=True)

        # f = open(os.path.join(dump_path, filename), 'wb')
        # offset = 0
        # while offset < self.size:
        #     data = self.read(size, offset)
        #     if data is None or len(data) == b'':
        #         break
        #     f.write(data)
        #     offset += len(data)
        # f.flush()
        # f.close()
        # return offset