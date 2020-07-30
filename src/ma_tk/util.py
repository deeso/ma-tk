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