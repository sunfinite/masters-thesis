import sys
sys.path.append("/Users/skatkuri/cuckoofilter")
from cuckoofilter import CuckooFilter, CountingBloomFilter
import rocksdb
import random
from pybloom import BloomFilter
import os
import time

def test_cuckoo_insert(items, n):
    c = CuckooFilter(n, 2)
    for item in items:
        c.insert(item) 
    return c

def test_filter_access(items, filter_):
    for item in items:
        item in filter_

def test_rocksdb_insert(items):
    file_ = 'temp_%f.db' % random.random()
    db = rocksdb.DB(file_, rocksdb.Options(create_if_missing=True))
    for item in items:
        db.put(item, b'')
        db.key_may_exist(item)

def test_counting_insert(items, n):
    c = CountingBloomFilter(n)
    for item in items:
        c.add(item)
    return c
        
def test_bloom_insert(items, n):
    c = BloomFilter(n, 0.01)
    for item in items:
        c.add(item)
    return c

if __name__ == '__main__':
    start = 1000
    end = 10000
    step = 1000
    for fn in [test_cuckoo_insert, test_bloom_insert, test_counting_insert]:
        print(fn)
        insert = []
        access = []
        for trial  in range(start, end + 1, step): 
            items = [os.urandom(49) for i in range(trial)]
            mid = int(len(items) / 2)
            str_items = [item.hex() for item in items]
            lookup_items = list(items)
            str_lookup_items = [item.hex() for item in lookup_items]
            random.shuffle(lookup_items)
            lookup_items = lookup_items[:random.randint(mid - 50, mid + 50)]
            while len(lookup_items) < trial:
                lookup_items.append(os.urandom(49))

            def timeit(fn, *args, **kwargs):
                loops = 10
                times = []
                for i in range(loops):
                    st = time.time()
                    fn(*args, **kwargs)
                    et = time.time()
                    times.append(et - st)
                return sum(times) / len(times)

            if fn != test_bloom_insert: 
                arg_items = str_items
                arg_lookup_items = str_lookup_items
            else:
                arg_items = items
                arg_lookup_items = lookup_items

            insert.append('%d,%f' % (trial, timeit(fn, arg_items, end)))
            c = fn(arg_items, end)
            access.append('%d,%f' % (trial, timeit(test_filter_access, arg_lookup_items, c))) 

        print('Insert')
        for i in insert:
            print(i)
        print('Access')
        for i in access:
            print(i)

