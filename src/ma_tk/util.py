from .consts import *

def get_page_mask(page_size):
    page_mask = MASK_64BIT
    while (page_mask & page_size) != 0:
        page_mask = page_mask << 1
    page_mask = page_size | page_mask
    return page_mask & MASK_64BIT

def get_page_mask_complement(page_size):
    return ~(-page_size) 

def get_perms_str(flags):
    flag_bits = {1:'x', 2:'w', 4:'r', 0:'-'}
    and_bit = lambda x, v: flag_bits[x & v] 
    get_flag_str = lambda flags: ''.join([and_bit(flags, m) for m in [4, 2, 1]])
    return get_flag_str(flags)

def bytes_to_struct(data, cstruct_klass):
    tmp = ctypes.cast(data, ctypes.POINTER(cstruct_klass)).contents
    # there is an odd bug, but the data gets corrupted if we
    # return directly after the cast, so we create a deep copy
    # and return that value
    # Note if there are any pointers in the struct it will fail
    # https://stackoverflow.com/questions/1470343/python-ctypes-copying-structures-contents
    dst = copy.deepcopy(tmp)
    return dst

def json_serialize_struct(strct):
    r = {}
    for f, ct in strct._fields_:
        v = getattr(strct, f)
        if isinstance(v, (ctypes.Structure, ctypes.Union)):
            r[f] = json_serialize_struct(v)
        else:
            r[f] = v
    return r
