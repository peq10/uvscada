'''
Erase until the chip reports erased stable for 10% of the lead up time
'''

from uvscada.minipro import Minipro
import json
import datetime
import time
import zlib
import binascii
import md5

def popcount(x):
    return bin(x).count("1")

def is_erased1(fw, prog_dev):
    # for now assume all 1's is erased
    # on some devices like PIC this isn't true due to file 0 padding
    percent = 100.0 * sum(bytearray(fw)) / (len(fw) * 0xFF)
    return percent == 100.0, percent

def is_erased(fw, prog_dev):
    # for now assume all 1's is erased
    # on some devices like PIC this isn't true due to file 0 padding
    percent = 100.0 * sum([popcount(x) for x in bytearray(fw)]) / (len(fw) * 8)
    return percent == 100.0, percent

def run(fnout, prog_dev, ethresh=20., interval=3.0):
    prog = Minipro(device=prog_dev)
    with open(fnout, 'w') as fout:
        j = {'type': 'header', 'prog_dev': prog_dev, 'date': datetime.datetime.utcnow().isoformat(), 'interval': interval, 'ethresh': ethresh}
        fout.write(json.dumps(j) + '\n')

        tstart = time.time()
        tlast = None
        thalf = None
        passn = 0
        nerased = 0
        while True:
            if tlast is not None:
                while time.time() - tlast < interval:
                    time.sleep(0.1)
    
            tlast = time.time()
            now = datetime.datetime.utcnow().isoformat()
            passn += 1
            fw = prog.read()
            erased, erase_percent = is_erased(fw, prog_dev)
            if erased:
                nerased += 1
            else:
                nerased = 0
            pcomplete = 100.0 * nerased / passn

            j = {'iter': passn, 'date': now, 'fw': binascii.hexlify(zlib.compress(fw)), 'pcomplete': pcomplete, 'erase_percent': erase_percent, 'erased': erased}
            fout.write(json.dumps(j) + '\n')

            signature = binascii.hexlify(md5.new(fw).digest())[0:8]
            print('%s iter %u: erased %u w/ erase_percent %0.3f%%, sig %s, erase completion: %0.1f' % (now, passn, erased, erase_percent, signature, 100. * pcomplete / ethresh))
            if thalf is None and erase_percent >= 50:
                thalf = tlast
                dt_half = thalf - tstart
                print('50%% erased after %0.1f sec' % (dt_half,))
            if pcomplete >= ethresh:
                break
        dt = tlast - tstart
        print('120%% erased after %0.1f sec' % (dt,))

        j = {'type': 'footer', 'etime': dt, 'half_etime': dt_half}
        fout.write(json.dumps(j) + '\n')
    return dt, dt_half

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--prog-device', required=True, help='')
    parser.add_argument('fout', help='')
    args = parser.parse_args()

    run(args.fout, args.prog_device)
