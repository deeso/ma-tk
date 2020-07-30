import unittest

import unittest
from ma_tk.manager import Manager
 
BUFFER_VA = 0x14000
FILE_VA = 0x24000

class TestManager(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_create(self):
        mgr = Manager()
        self.assertTrue(True)

    def test_load_buffer(self):
        mgr = Manager()
        self.assertTrue(True)

        data = b'\xab\xab\xcd\xcd'*4096
        mgr.add_buffermap(data, BUFFER_VA, len(data), offset=0, flags=7)
        self.assertTrue(mgr.get_vaddr_pos() == BUFFER_VA)

    def test_get_backend(self):
        mgr = Manager()
        self.assertTrue(True)

        data = b'\xab\xab\xcd\xcd'*4096
        mgr.add_buffermap(data, BUFFER_VA, len(data), offset=0, flags=7)
        self.assertTrue(mgr.get_vaddr_pos() == BUFFER_VA)
        bm = mgr.get_map(BUFFER_VA)
        self.assertTrue(bm is not None)
        self.assertTrue(bm.has(BUFFER_VA))
        self.assertTrue(bm.translate_vaddr_to_offset(BUFFER_VA) == 0)
        self.assertTrue(len(bm.get_page_cache()) > 2)
        self.assertTrue(BUFFER_VA in bm.get_page_cache())
        self.assertTrue(bm.calc_page(BUFFER_VA+4098) in bm.get_page_cache())
        self.assertTrue(bm.translate_vaddr_to_offset(BUFFER_VA+8) == 8)


    def test_load_buffer(self):
        mgr = Manager()
        self.assertTrue(True)

        data = b'\xab\xab\xcd\xcd'*4096
        mgr.add_buffermap(data, BUFFER_VA, len(data), offset=0, flags=7)
        self.assertTrue(mgr.get_vaddr_pos() == BUFFER_VA)
        data = mgr.read_word()
        self.assertTrue(43947 == data)
        mgr.seek(offset=-2)
        data = mgr.read(2)
        self.assertTrue(b'\xab\xab' == data)


if __name__ == '__main__':
    unittest.main()