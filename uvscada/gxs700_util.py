import gxs700_fw
import gxs700

# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import sys
import numpy as np
import struct
import os

def check_device(usbcontext=None, verbose=True):
    if usbcontext is None:
        usbcontext = usb1.USBContext()

    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()

        try:
            desc, _size = gxs700_fw.pidvid2name_post[(vid, pid)]
        except KeyError:
            continue

        if verbose:
            print
            print
            print 'Found device (post-FW): %s' % desc
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid)
        return udev
    return None

def open_dev(usbcontext=None, verbose=None):
    '''
    Return a device with the firmware loaded
    '''

    verbose = verbose if verbose is not None else os.getenv('GXS700_VERBOSE', 'N') == 'Y'

    if usbcontext is None:
        usbcontext = usb1.USBContext()

    print 'Checking if firmware load is needed'
    if gxs700_fw.load_all(wait=True, verbose=verbose):
        print 'Loaded firmware'
    else:
        print 'Firmware load not needed'

    print 'Scanning for loaded devices...'
    udev = check_device(usbcontext, verbose=verbose)
    if udev is None:
        raise Exception("Failed to find a device")

    dev = udev.open()
    return dev

def ez_open_ex(verbose=False, init=True):
    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext, verbose=verbose)

    # FW load should indicate size
    vid = dev.getDevice().getVendorID()
    pid = dev.getDevice().getProductID()
    _desc, size = gxs700_fw.pidvid2name_post[(vid, pid)]

    return usbcontext, dev, gxs700.GXS700(usbcontext, dev, verbose=verbose, size=size, init=init)

def ez_open(verbose=False):
    _usbcontext, _dev, gxs700 = ez_open_ex(verbose)
    return gxs700

# http://www.janeriksolem.net/2009/06/histogram-equalization-with-python-and.html
def histeq(buff, nbr_bins=256):
    depth = 2
    width, height = gxs700.sz_wh(len(buff))

    buff = bytearray(buff)
    im =  np.zeros(width * height)
    i = 0
    for y in range(height):
        line0 = buff[y * width * depth:(y + 1) * width * depth]
        for x in range(width):
            b0 = line0[2*x + 0]
            b1 = line0[2*x + 1]

            # FIXME: 16 bit pixel truncation to fit into png
            im[i] = (b1 << 8) + b0
            i += 1


    #get image histogram
    imhist,bins = np.histogram(im.flatten(),nbr_bins,normed=True)
    cdf = imhist.cumsum() #cumulative distribution function
    cdf = 255 * cdf / cdf[-1] #normalize

    #use linear interpolation of cdf to find new pixel values
    im2 = np.interp(im.flatten(),bins[:-1],cdf)

    #return im2.reshape(im.shape), cdf
    rs = im2.reshape(im.shape)

    ret = bytearray()
    for i in xrange(len(rs)):
        ret += struct.pack('>H', int(rs[i]))
    return str(ret)

def ram_r(dev, addr, datal):
    bs = 16
    offset = 0
    ret = bytearray()
    while offset < datal:
        l = min(bs, datal - offset)
        #print 'Read 0x%04X: %d' % (addr + offset, l)
        ret += dev.controlRead(0xC0, 0xA0, addr + offset, 0x0000, l, timeout=1000)
        offset += bs
    return str(ret)

def sn_flash_r(gxs):
    s = gxs.flash_r(addr=0x0C, n=11).replace('\x00', '')
    return int(s)

def sn_eeprom_r(gxs):
    s = gxs.eeprom_r(addr=0x40, n=11).replace('\x00', '')
    return int(s)
