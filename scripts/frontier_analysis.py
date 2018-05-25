import os
import sys
sys.path.append('/home/ubuntu/Py-IBLT')
import gzip
import glob
import json
from iblt import IBLT
import codecs
import time
from datetime import datetime

def reconcile_iblts(i1, i2, diff):
    for i in range(i1.m):
        prev_count = i1.T[i][0]
        temp = [i1.T[i][0] - i2.T[i][0]]
        for j in range(1, 4):
            temp.append((i1.T[i][j] ^ i2.T[i][j]))
        i1.T[i] = temp

    i = 0
    recovered_txs_ids = set()
    while True:
        if i1.T[i][0] == 1 or i1.T[i][0] == -1:
            k = i1.T[i][1].tobytes().rstrip(b'0')
            if i1.key_hash(k) == i1.T[i][3]:
                print("Found a pure cell")
                print(k)
                i1.delete(k, i1.T[i][2].tobytes())
                k = codecs.encode(k, 'hex')
                print(k.decode('utf-8'))
                # print(k)
                # print(skipped_txs_ids)
                # print(k in skipped_txs_ids)
                if k.decode('utf-8') in diff:
                    print("Recovered %s" % k)
                    recovered_txs_ids.add(k)
                i = 0
            else:
                i += 1
        else:
            i += 1

        if i == i1.m:
            break
    if diff == recovered_txs_ids:
        print("All skipped tx ids have been recovered!")
    else:
        print("Could not recover %s" % (diff - recovered_txs_ids))
    print("Finished reconciling")

def run():
    files = glob.glob("*.out.gz")
    files.sort(key=lambda x: os.path.getmtime(x))
    for i in range(0, len(files), 2):
        with gzip.open(files[i]) as fin, gzip.open(files[i+1]) as fin2:
            s = fin.read()
            d1 = json.loads(s.decode('utf-8'))
            s = fin2.read()
            d2 = json.loads(s.decode('utf-8'))
            set1 = set(d1.values())
            set2 = set(d2.values())
            diff = set1.symmetric_difference(set2)

            # start = time.time()
            # i1 = IBLT(128, 3, 32, 32)
            #for k, v in d1.items():
            #    i1.insert(v, k)
            #i2 = IBLT(128, 3, 32, 32)
            #for k, v in d2.items():
            #    i2.insert(v, k)
            #reconcile_iblts(i1, i2, diff)
            #end = time.time()

            frontier_time = files[i+1].split('.')[0]
            from_f, to_f = frontier_time.split('_')
            frontier_time = int(to_f) - int(from_f)
            d = datetime.fromtimestamp(float(from_f))
            print("%s,%d,%d,%d" % (d.isoformat(), len(d2), frontier_time, len(diff)))
        
if __name__ == '__main__':
    run()
