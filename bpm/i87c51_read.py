import binascii
import time
import usb1
import libusb1
import sys
import struct
import inspect

from uvscada.wps7 import WPS7

from uvscada.usb import usb_wraps
from uvscada.bpm.bp1410_fw import load_fx2
from uvscada.bpm import bp1410_fw_sn, startup
from uvscada.bpm.startup import bulk2, bulk86
from uvscada.bpm.startup import sm_read, gpio_readi, led_mask, cmd_49, cmd_2
from uvscada.bpm.startup import sm_info0, sm_info1, sm_insert, sn_read
from uvscada.util import hexdump, add_bool_arg
from uvscada.util import str2hex
from uvscada.usb import validate_read, validate_readv

import i87c51_read_fw as fwm

def where():
    # 0 represents this line
    # 1 represents line at caller
    callerframerecord = inspect.stack()[1]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    print '%s.%s():%d' % (info.filename, info.function, info.lineno)

def dexit():
    print 'Debug break'
    sys.exit(0)

def open_dev(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    print 'Scanning for devices...'
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        if (vid, pid) == (0x14b9, 0x0001):
            print
            print
            print 'Found device'
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid)
            return udev.open()
    raise Exception("Failed to find a device")

def fw_verify(dev, fw, cont):
    print 'Verifying firmware readback'
    # Generated from packet 381/382
    # WARNING: unexpected suffix: 0x01
    if cont:
        buff = bulk2(dev, "\x08\x00\x57\x8F\x00", target=2048, truncate=True)
    else:
        buff = bulk2(dev, "\x08\x00\x57\x8C\x00", target=2048, truncate=True)
    # Discarded 259 / 512 bytes => 253 bytes
    # Generated from packet 385/386
    validate_read(fw, buff, "packet W: 381/382, R 383/384, 399/400")
    print 'Readback ok'

def replay(dev, fw, cont):
    replay1(dev, fw, cont)
    replay2(dev, cont)

def replay1(dev, fw, cont=True):
    bulkRead, bulkWrite, controlRead, controlWrite = usb_wraps(dev)

    # Generated by uvusbreplay 0.1
    # uvusbreplay copyright 2011 John McMaster <JohnDMcMaster@gmail.com>
    # cmd: /home/mcmaster/bin/usbrply i87c51_02_read_id_cont.cap --packet-numbers --no-setup --comment --fx2 -j
    # Generated from packet 11/12
    # None (0xB0)
    # NOTE:: req max 4096 but got 3
    buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
    # Req: 4096, got: 3
    validate_read("\x00\x00\x00", buff, "packet 11/12")
    # Generated from packet 13/14
    # Discarded 3 / 4 bytes => 1 bytes
    buff = bulk86(dev, target=0x01)
    validate_read("\x16", buff, "packet 13/14")

    if 1 or cont:
        # NOTE:: req max 512 but got 4
        # Generated from packet 15/16
        buff = bulk2(dev, "\x01", target=0x85)
        # Discarded 3 / 136 bytes => 133 bytes
        validate_readv((
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x92\x00\xA0\x63\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00",
    
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00",
            ), buff, "packet W: 15/16, R: 17/18")
    else:
        # NOTE:: req max 512 but got 4
        # Generated from packet None/None
        buff = bulk2(dev, "\x01", target=0x2A)
        # Discarded 3 / 45 bytes => 42 bytes
        validate_read(
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x8F\x00\x20\x1C\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00"
            , buff, "packet W: None/None, R: None/None")
        # NOTE:: req max 512 but got 45
        # Generated from packet None/None
        # Discarded 3 / 94 bytes => 91 bytes
        buff = bulk86(dev, target=0x5B)
        validate_read(
            "\x00\xB4\x46\x00\x00\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01" \
            "\x00\x00\x00\x30\x55\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0" \
            "\x01\x02\x00\x01\x00\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84" \
            "\x25\x00\x00\x00\x00\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80" \
            "\x25\x00\x00\x74\x46\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40" \
            "\x11\x00\x00\x44\x11\x00\x00\xC0\x1E\x00\x00"
            , buff, "packet None/None")

    # NOTE:: req max 512 but got 136
    # Generated from packet 19/20
    buff = bulk2(dev, 
        "\x43\x19\x10\x00\x00\x3B\x7E\x25\x00\x00\xFE\xFF\x3B\x7C\x25\x00" \
        "\x00\xFE\xFF\x00"
        , target=0x02)
    # Discarded 3 / 5 bytes => 2 bytes
    validate_read("\xA4\x06", buff, "packet W: 19/20, R: 21/22")

    # NOTE:: req max 512 but got 5
    # Generated from packet 23/24
    buff = bulk2(dev, "\x01", target=0x85)
    # Discarded 3 / 136 bytes => 133 bytes
    validate_readv((
        "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
        "\x00\x30\x00\x92\x00\xA0\x63\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
        "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
        "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
        "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
        "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
        "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
        "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
        "\x00\xC0\x1E\x00\x00",
        
        "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
        "\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
        "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
        "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
        "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
        "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
        "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
        "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
        "\x00\xC0\x1E\x00\x00",
        ), buff, "packet W: 23/24, R: 25/26")

    # Generated from packet 27/28
    sn_read(dev)

    # NOTE:: req max 512 but got 35
    # Generated from packet 31/32
    buff = bulk2(dev, 
        "\x14\x38\x25\x00\x00\x04\x00\x90\x32\x90\x00\xA7\x02\x1F\x00\x14" \
        "\x40\x25\x00\x00\x01\x00\x3C\x36\x0E\x01"
        , target=0x20)
    # Discarded 3 / 35 bytes => 32 bytes
    validate_read(
        "\x14\x00\x54\x41\x38\x34\x56\x4C\x56\x5F\x46\x58\x34\x00\x00\x00" \
        "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3E\x2C"
        , buff, "packet W: 31/32, R: 33/34")


    sm_info1(dev)
    
    
    
    # NOTE:: req max 512 but got 35
    # Generated from packet 55/56
    buff = bulk2(dev, "\x01", target=0x85)
    # Discarded 3 / 136 bytes => 133 bytes
    validate_readv((
        "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
        "\x00\x30\x00\x92\x00\xA0\x63\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
        "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
        "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
        "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
        "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
        "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
        "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
        "\x00\xC0\x1E\x00\x00",
        
        "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
        "\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
        "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
        "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
        "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
        "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
        "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
        "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
        "\x00\xC0\x1E\x00\x00"
        ), buff, "packet W: 55/56, R: 57/58")

    # NOTE:: req max 512 but got 136
    # Generated from packet 59/60
    bulkWrite(0x02, "\x43\x19\x10\x00\x00")
    # Generated from packet 61/62
    bulkWrite(0x02, "\x20\x01\x00\x0C\x04")
    # Generated from packet 63/64
    bulkWrite(0x02, "\x41\x00\x00")

    # Generated from packet 65/66
    buff = bulk2(dev, "\x10\x80\x02", target=0x06)
    # Discarded 3 / 9 bytes => 6 bytes
    validate_read("\x80\x00\x00\x00\x09\x00", buff, "packet W: 65/66, R: 67/68")

    sm_read(dev)
    '''
    validate_read(
        "\x11\x00\x53\x4D\x34\x38\x44\x00\x00\x00\x00\x00\x00\x00\x5D\xF4" \
        "\x39\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x62\x6C"
        , buff, "packet W: 69/70, R: 71/72")
    '''

    sm_insert(dev)
    
    # NOTE:: req max 512 but got 35
    # Generated from packet 77/78
    buff = bulk2(dev, "\x45\x01\x00\x00\x31\x00\x06", target=0x64)
    # Discarded 3 / 103 bytes => 100 bytes
    validate_read(
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF"
        , buff, "packet W: 77/78, R: 79/80")

    # Generated from packet 81/82
    cmd_49(dev)

    sm_info1(dev)

    sm_insert(dev)
    # NOTE:: req max 512 but got 35
    # Generated from packet 117/118
    buff = bulk2(dev, "\x22\x02\x10\x00\x13\x00\x06", target=0x08)
    # Discarded 3 / 11 bytes => 8 bytes
    '''
    validate_readv((
            "\x3B\x01\x00\x00\x9C\x00\x00\x00",
            "\x65\x01\x00\x00\xC6\x00\x00\x00",
            "\x66\x01\x00\x00\xC7\x00\x00\x00",
            "\x67\x01\x00\x00\xC8\x00\x00\x00",
            ), buff, "packet W: 117/118, R: 119/120")
    '''
    # NOTE:: req max 512 but got 11
    # Generated from packet 121/122
    bulkWrite(0x02, 
        "\x3B\x0C\x22\x00\xC0\x40\x00\x3B\x0E\x22\x00\xC0\x00\x00\x3B\x1A" \
        "\x22\x00\xC0\x18\x00"
        )
    # Generated from packet 123/124
    buff = bulk2(dev, "\x4A\x03\x00\x00\x00", target=0x02)
    # Discarded 3 / 5 bytes => 2 bytes
    validate_read("\x03\x00", buff, "packet W: 123/124, R: 125/126")
    # NOTE:: req max 512 but got 5
    # Generated from packet 127/128
    bulkWrite(0x02, "\x4C\x00\x02")
    # Generated from packet 129/130
    # None (0xB2)
    buff = controlWrite(0x40, 0xB2, 0x0000, 0x0000, "")
    # Generated from packet 131/132
    bulkWrite(0x02, "\x50\x5D\x00\x00\x00")
    # Generated from packet 133/134
    buff = bulk2(dev, 
        "\xE9\x03\x00\x00\x00\x90\x00\x00\xE9\x03\x00\x00\x00\x90\x01\x10" \
        "\xE9\x03\x00\x00\x00\x90\x00\x00\xE9\x03\x00\x00\x00\x90\x01\x80" \
        "\xE9\x02\x00\x00\x00\x90\x00\xE9\x04\x00\x00\x00\x00\x00\x00\x00" \
        "\xE9\x03\x00\x00\x00\x90\x00\x00\xE9\x03\x00\x00\x00\x90\x00\x00" \
        "\xE9\x03\x00\x00\x00\x90\x00\x00\xE9\x03\x00\x00\x00\x90\x00\x00" \
        "\x66\xB9\x00\x00\xB2\x00\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x80\x00", buff, "packet W: 133/134, R: 135/136")

    # Generated from packet 137/138
    cmd_2(dev, "\x81\x00\x60\x00\x09\x00", "packet W: 137/138, R: 139/140")

    # Generated from packet 141/142
    bulkWrite(0x02, "\x50\xC0\x00\x00\x00")
    # Generated from packet 143/144
    buff = bulk2(dev, 
        "\x66\xB8\x01\x2D\x81\xE3\xFF\xFF\x00\x00\x66\xBB\x18\x00\x66\xC7" \
        "\x05\x30\x40\x00\xC0\xF0\xFF\x89\xD9\xC1\xE1\x02\x66\xC7\x81\x02" \
        "\x00\x00\x00\xF0\xFF\x66\x03\x05\xE4\x46\x00\x00\x66\x89\x05\x90" \
        "\x40\x00\xC0\x89\xDA\x81\xCA\x00\x80\x00\x00\x66\x89\x15\x50\x40" \
        "\x00\xC0\xC6\x05\x14\x22\x00\xC0\x7B\x81\xCA\x00\x40\x00\x00\x66" \
        "\x89\x15\x50\x40\x00\xC0\x89\xD9\x66\xC1\xE1\x02\x66\x89\x81\x00" \
        "\x00\x00\x00\x66\x2B\x05\xE4\x46\x00\x00\xC6\x05\x14\x22\x00\xC0" \
        "\xBB\x81\xCB\x00\x80\x00\x00\x66\x89\x1D\x50\x40\x00\xC0\x89\xC2" \
        "\x81\xE2\x07\x00\x00\x00\x03\xD2\x81\xCA\x01\x00\x00\x00\x89\xD9" \
        "\x81\xE1\x03\x00\x00\x00\xD3\xE2\xD3\xE2\xD3\xE2\xD3\xE2\xD3\xE2" \
        "\xC1\xE2\x0A\x89\xD9\x81\xE1\xFC\x03\x00\x00\x09\xCA\x88\x82\x00" \
        "\x00\x00\x40\x66\xB9\x00\x00\xB2\x00\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x81\x00", buff, "packet W: 143/144, R: 145/146")

    # Generated from packet 147/148
    cmd_2(dev, "\x82\x00\x20\x01\x09\x00", "packet W: 147/148, R: 149/150")

    # Generated from packet 151/152
    bulkWrite(0x02, "\x09\x10\x57\x81\x00")

    # Generated from packet 153/154
    cmd_2(dev, "\x82\x00\x20\x01\x09\x00", "packet W: 153/154, R: 155/156")

    # added
    sm_insert(dev)
    
    print 'Going active'
    led_mask(dev, 'active')
    
    # Generated from packet 161/162
    bulkWrite(0x02, "\x50\x18\x00\x00\x00")
    # Generated from packet 163/164
    buff = bulk2(dev, 
        "\x66\xB8\x01\x32\x66\x89\x05\x06\x00\x09\x00\x66\xB9\x00\x00\xB2" \
        "\x00\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x82\x00", buff, "packet W: 163/164, R: 165/166")

    # Generated from packet 167/168
    cmd_2(dev, "\x83\x00\x40\x01\x09\x00", "packet W: 167/168, R: 169/170")

    # Generated from packet 171/172
    buff = bulk2(dev, 
        "\x57\x82\x00\x20\x01\x00\x2B\x3B\x0C\x22\x00\xC0\x40\x00\x3B\x0E" \
        "\x22\x00\xC0\x00\x00\x3B\x1A\x22\x00\xC0\x18\x00\x0E\x01"
        , target=0x20, truncate=True)
    # Discarded 480 / 512 bytes => 32 bytes
    validate_read(
        "\x14\x00\x54\x41\x38\x34\x56\x4C\x56\x5F\x46\x58\x34\x00\x00\x00" \
        "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3E\x2C"
        , buff, "packet W: 171/172, R: 173/174")


    sm_info0(dev)


    # Generated from packet 195/196
    buff = bulk2(dev, "\x48\x00\x10\x82\x02", target=0x06, truncate=True)
    # Discarded 506 / 512 bytes => 6 bytes
    validate_read("\x82\x00\x20\x01\x09\x00", buff, "packet W: 195/196, R: 197/198")
    # Generated from packet 199/200
    bulkWrite(0x02, "\x20\x01\x00\x50\x7D\x02\x00\x00")
    # Generated from packet 201/202
    buff = bulk2(dev, fwm.p201, target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x82\x00", buff, "packet W: 201/202, R: 203/204")

    # Generated from packet 205/206
    cmd_2(dev, "\x83\x00\xA0\x03\x09\x00", "packet W: 205/206, R: 207/208")

    # Generated from packet 209/210
    bulkWrite(0x02, "\x57\x82\x00\x50\x1D\x00\x00\x00")
    # Generated from packet 211/212
    buff = bulk2(dev, 
        "\xC7\x05\x74\x46\x00\x00\x0B\x00\x00\x00\xFF\x15\x38\x11\x00\x00" \
        "\x66\xB9\x00\x00\xB2\x00\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x83\x00", buff, "packet W: 211/212, R: 213/214")
    
    # Generated from packet 215/216
    cmd_2(dev, "\x84\x00\xC0\x03\x09\x00", "packet W: 215/216, R: 217/218")


    if cont:
        '''
        Seems these must be done together
        Increments socket insertion count
        '''
        # Generated from packet 219/220
        bulkWrite(0x02, "\x57\x83\x00\x50\x18\x3A\x00\x00")
        # p221.bin: DOS executable (COM)
        # Generated from packet 221/222
        buff = bulk2(dev, fwm.p221, target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x84\x00", buff, "packet W: 221/222, R: 223/224")
    
        # Generated from packet 225/226
        cmd_2(dev, "\x85\x00\xE0\x3D\x09\x00", "packet W: 225/226, R: 227/228")
    
        # Generated from packet 229/230
        bulkWrite(0x02, 
            "\x57\x84\x00\xF0\xFF\xFF\x0F\xF0\xFF\xFF\x00\x00\x00\x00\x00\x00" \
            "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
            "\x00\x00\x00\x00\xF0\x0F\x00\x00\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
            "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
            )
        # Generated from packet 231/232
        bulkWrite(0x02, "\x50\xDE\x03\x00\x00")
        # Generated from packet 233/234
        buff = bulk2(dev, fwm.p233, target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x85\x00", buff, "packet W: 233/234, R: 235/236")
    
        # Generated from packet 237/238
        cmd_2(dev, "\x86\x00\xC0\x41\x09\x00", "packet W: 237/238, R: 239/240")

        # Generated from packet 241/242
        buff = bulk2(dev, "\x57\x85\x00", target=0x01, truncate=True)
        # Discarded 511 / 512 bytes => 1 bytes
        validate_read("\x01", buff, "packet W: 241/242, R: 243/244")
        # Generated from packet 245/246
        bulkWrite(0x02, "\x50\x62\x00\x00\x00")
    else:
        bulkWrite(0x02, "\x57\x83\x00\x50\x62\x00\x00\x00")
    
    # Generated from packet 247/248
    buff = bulk2(dev, 
        "\x00\x00\x3C\x00\x38\x00\x34\x00\x30\x00\x3D\x00\x39\x00\x35\x00" \
        "\x31\x00\x3E\x00\x3A\x00\x36\x00\x32\x00\x3F\x00\x3B\x00\x37\x00" \
        "\x33\x00\x1E\x00\x1A\x00\x16\x00\x00\x00\x02\x00\x06\x00\x0A\x00" \
        "\x0E\x00\x23\x00\x27\x00\x2B\x00\x2F\x00\x22\x00\x26\x00\x2A\x00" \
        "\x2E\x00\x21\x00\x25\x00\x29\x00\x2D\x00\x20\x00\x24\x00\x28\x00" \
        "\x1C\x00\x00\x00\x04\x00\x08\x00\x0C\x00\x10\x00\x14\x00\x18\x00" \
        "\x1C\x00"
        , target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x86\x00", buff, "packet W: 247/248, R: 249/250")
    else:
        validate_read("\x84\x00", buff, "packet W: None/None, R: None/None")

    if cont:
        # Generated from packet 251/252
        cmd_2(dev, "\x87\x00\x30\x42\x09\x00", "packet W: 251/252, R: 253/254")
    else:
        cmd_2(dev, "\x85\x00\x30\x04\x09\x00", "packet W: 251/252, R: 253/254")

    if cont:
        # Generated from packet 255/256
        bulkWrite(0x02, 
            "\x1D\xC0\x41\x09\x00\x28\x00\x15\x60\x00\x00\x00\x00\x00\x00\x00" \
            "\x00\x00\x01\x00\x00\x00\x1C\x30\x00\x00\x00\x08\x00\x00\x00\x48" \
            "\x00\x50\x71\x09\x00\x00")
    else:
        bulkWrite(0x02, 
            "\x1D\xC0\x03\x09\x00\x28\x00\x15\x60\x00\x00\x00\x00\x00\x00\x00" \
            "\x00\x00\x01\x00\x00\x00\x1C\x30\x00\x00\x00\x08\x00\x00\x00\x48" \
            "\x00")
        
    if cont:
        # Generated from packet 257/258
        buff = bulk2(dev, fwm.p257, target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x87\x00", buff, "packet W: 257/258, R: 259/260")
    
        # Generated from packet 261/262
        cmd_2(dev, "\x88\x00\xB0\x4B\x09\x00", "packet W: 261/262, R: 263/264")
    
        # Generated from packet 265/266
        buff = bulk2(dev, "\x57\x87\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 265/266, R: 267/268")
        
    # Generated from packet 269/270
    bulkWrite(0x02, "\x50\x17\x00\x00\x00")
    # Generated from packet 271/272
    buff = bulk2(dev, 
        "\xC7\x05\x2C\x00\x09\x00\x24\x04\x00\x00\x66\xB9\x00\x00\xB2\x00" \
        "\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x88\x00", buff, "packet W: 271/272, R: 273/274")
    else:
        validate_read("\x85\x00", buff, "packet W: None/None, R: None/None")

    if cont:
        # Generated from packet 275/276
        cmd_2(dev, "\x89\x00\xD0\x4B\x09\x00", "packet W: 275/276, R: 277/278")
    else:
        cmd_2(dev, "\x86\x00\x50\x04\x09\x00", "packet W: 275/276, R: 277/278")

    if cont:
        # Generated from packet 279/280
        bulkWrite(0x02, "\x57\x88\x00\x50\x32\x07\x00\x00")
    else:
        bulkWrite(0x02, "\x57\x85\x00\x50\x32\x07\x00\x00")
    # Generated from packet 281/282
    buff = bulk2(dev, fwm.p281, target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x89\x00", buff, "packet W: 281/282, R: 283/284")
    else:
        validate_read("\x86\x00", buff, "packet W: None/None, R: None/None")

    if cont:
        # Generated from packet 285/286
        cmd_2(dev, "\x8A\x00\x10\x53\x09\x00", "packet W: 285/286, R: 287/288")
    else:
        cmd_2(dev, "\x87\x00\x90\x0B\x09\x00", "packet W: 285/286, R: 287/288")
    
    if cont:
        # Generated from packet 289/290
        buff = bulk2(dev, "\x57\x89\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 289/290, R: 291/292")
    else:
        buff = bulk2(dev, "\x57\x86\x00", target=0x02, truncate=True)
        validate_read("\x00\x00", buff, "packet W: 289/290, R: 291/292")
    # Generated from packet 293/294
    bulkWrite(0x02, "\x50\x3D\x03\x00\x00")
    # Generated from packet 295/296
    buff = bulk2(dev, fwm.p295, target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x8A\x00", buff, "packet W: 295/296, R: 297/298")
    else:
        validate_read("\x87\x00", buff, "packet W: 295/296, R: 297/298")

    if cont:
        # Generated from packet 299/300
        cmd_2(dev, "\x8B\x00\x50\x56\x09\x00", "packet W: 299/300, R: 301/302")
    else:
        cmd_2(dev, "\x88\x00\xD0\x0E\x09\x00", "packet W: 299/300, R: 301/302")

    if cont:
        # Generated from packet 303/304
        buff = bulk2(dev, "\x57\x8A\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x89\x00", buff, "packet W: 303/304, R: 305/306")
    else:
        buff = bulk2(dev, "\x57\x87\x00", target=0x02, truncate=True)
        validate_read("\x89\x00", buff, "packet W: 303/304, R: 305/306")
    
    # Generated from packet 307/308
    bulkWrite(0x02, "\x50\x1D\x00\x00\x00")
    # Generated from packet 309/310
    buff = bulk2(dev, 
        "\x66\x8B\x0D\x1A\x24\x00\x00\xB2\x02\xFB\xFF\x25\x44\x11\x00\x00" \
        "\x66\xB9\x00\x00\xB2\x02\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    if cont:
        validate_read("\x8B\x00", buff, "packet W: 309/310, R: 311/312")
        # Generated from packet 313/314
        cmd_2(dev, "\x8C\x00\x70\x56\x09\x00", "packet W: 313/314, R: 315/316")
    else:
        validate_read("\x88\x00", buff, "packet W: None/None, R: None/None")
        cmd_2(dev, "\x89\x00\xF0\x0E\x09\x00", "packet W: 313/314, R: 315/316")

    # Generated from packet 317/318
    buff = bulk2(dev, "\x57\x8B\x00", target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x58\x00", buff, "packet W: 317/318, R: 319/320")

    # Generated from packet 321/322
    bulkWrite(0x02, "\x50\xF8\x04\x00\x00")

    # Generated from packet 323/324
    buff = bulk2(dev, fwm.p323, target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x8C\x00", buff, "packet W: 323/324, R: 325/326")
        # Generated from packet 327/328
        cmd_2(dev, "\x8D\x00\x70\x5B\x09\x00", "packet W: 327/328, R: 329/330")
        # Generated from packet 331/332
        buff = bulk2(dev, "\x57\x8C\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 331/332, R: 333/334")
    else:
        validate_read("\x89\x00", buff, "packet W: None/None, R: None/None")
        cmd_2(dev, "\x8A\x00\xF0\x13\x09\x00", "packet W: 327/328, R: 329/330")
        buff = bulk2(dev, "\x57\x89\x00", target=0x02, truncate=True)
        validate_read("\x00\x00", buff, "packet W: 331/332, R: 333/334")

    # Generated from packet 335/336
    bulkWrite(0x02, "\x50\x18\x00\x00\x00")
    # Generated from packet 337/338
    buff = bulk2(dev, 
        "\x66\xB8\x01\x32\x66\x89\x05\x06\x00\x09\x00\x66\xB9\x00\x00\xB2" \
        "\x00\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x8D\x00", buff, "packet W: 337/338, R: 339/340")
        # Generated from packet 341/342
        cmd_2(dev, "\x8E\x00\x90\x5B\x09\x00", "packet W: 341/342, R: 343/344")
    
        # Generated from packet 345/346
        buff = bulk2(dev, "\x57\x8D\x00\x57\x89\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 345/346, R: 347/348")
    else:
        validate_read("\x8A\x00", buff, "packet W: None/None, R: None/None")
        cmd_2(dev, "\x8B\x00\x10\x14\x09\x00", "packet W: 341/342, R: 343/344")
        buff = bulk2(dev, "\x57\x8A\x00\x57\x86\x00", target=0x02, truncate=True)
        validate_read("\x00\x00", buff, "packet W: 345/346, R: 347/348")

    # Generated from packet 349/350
    bulkWrite(0x02, "\x50\xFA\x01\x00\x00")
    if cont:
        # Generated from packet 351/352
        buff = bulk2(dev, fwm.p351, target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x8E\x00", buff, "packet W: 351/352, R: 353/354")
        # Generated from packet 355/356
        cmd_2(dev, "\x8F\x00\x90\x5D\x09\x00", "packet W: 355/356, R: 357/358")
        # Generated from packet 359/360
        buff = bulk2(dev, "\x08\x01\x57\x8E\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 359/360, R: 361/362")
        # Generated from packet 363/364
        buff = bulk2(dev, "\x57\x8C\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 363/364, R: 365/366")
    else:
        # Generated from packet 315/316
        buff = bulk2(dev, fwm.p351, target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x8B\x00", buff, "packet W: 315/316, R: 317/318")
        # Generated from packet 319/320
        buff = bulk2(dev, "\x02", target=0x06, truncate=True)
        # Discarded 506 / 512 bytes => 6 bytes
        validate_read("\x8C\x00\x10\x16\x09\x00", buff, "packet W: 319/320, R: 321/322")
        # Generated from packet 323/324
        buff = bulk2(dev, "\x08\x01\x57\x8B\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 323/324, R: 325/326")
        # Generated from packet 327/328
        buff = bulk2(dev, "\x57\x89\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 327/328, R: 329/330")

def replay2(dev, cont):
    bulkRead, bulkWrite, controlRead, controlWrite = usb_wraps(dev)

    if cont:
        # Generated from packet 367/368
        buff = bulk2(dev, "\x57\x8D\x00\x57\x89\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 367/368, R: 369/370")
    else:
        # Generated from packet 331/332
        buff = bulk2(dev, "\x57\x8A\x00\x57\x86\x00", target=0x02, truncate=True)
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x00\x00", buff, "packet W: 331/332, R: 333/334")


    # Generated from packet 371/372
    bulkWrite(0x02, "\x50\xDD\x05\x00\x00")
    # Generated from packet 373/374
    buff = bulk2(dev, fwm.p373, target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x8F\x00", buff, "packet W: 373/374, R: 375/376")
    else:
        validate_read("\x8C\x00", buff, "packet W: None/None, R: None/None")

    # works
    # fw_verify(dev, fw, cont)

    if cont:
        # Generated from packet 377/378
        cmd_2(dev, "\x90\x00\x70\x63\x09\x00", "packet W: 377/378, R: 379/380")
    else:
        cmd_2(dev, "\x8D\x00\xF0\x1B\x09\x00", "packet W: 377/378, R: 379/380")

    # original
    #fw_verify(dev, fw, cont)
    
    # Generated from packet 401/402
    if cont:
        buff = bulk2(dev, "\x57\x8C\x00", target=0x02, truncate=True)
    else:
        buff = bulk2(dev, "\x57\x89\x00", target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x00\x00", buff, "packet W: 401/402, R: 403/404")

    # Generated from packet 405/406
    bulkWrite(0x02, "\x50\x0D\x00\x00\x00")
    # Generated from packet 407/408
    buff = bulk2(dev, "\x66\xB9\x00\x00\xB2\x00\xFB\xFF\x25\x44\x11\x00\x00", target=0x02, truncate=True)

    # Discarded 510 / 512 bytes => 2 bytes
    if cont:
        validate_read("\x90\x00", buff, "packet W: 407/408, R: 409/410")
    else:
        validate_read("\x8D\x00", buff, "packet W: None/None, R: None/None")

    if cont:
        # Generated from packet 411/412
        cmd_2(dev, "\x91\x00\x80\x63\x09\x00", "packet W: 411/412, R: 413/414")
    else:
        cmd_2(dev, "\x8E\x00\x00\x1C\x09\x00", "packet W: 411/412, R: 413/414")
    
    if cont:
        # Generated from packet 415/416
        bulkWrite(0x02, "\x57\x90\x00\x50\x1A\x00\x00\x00")
    else:
        bulkWrite(0x02, "\x57\x8D\x00\x50\x1A\x00\x00\x00")

    # Generated from packet 417/418
    buff = bulk2(dev, 
        "\x66\xB9\x00\x00\xB2\x02\xFB\xFF\x25\x44\x11\x00\x00\x66\xB9\x00" \
        "\x00\xB2\x02\xFB\xFF\x25\x44\x11\x00\x00"
        , target=0x02, truncate=True)
    if cont:
        # Discarded 510 / 512 bytes => 2 bytes
        validate_read("\x91\x00", buff, "packet W: 417/418, R: 419/420")
    else:
        validate_read("\x8E\x00", buff, "packet W: None/None, R: None/None")

    if cont:
        # Generated from packet 421/422
        cmd_2(dev, "\x92\x00\xA0\x63\x09\x00", "packet W: 421/422, R: 423/424")
    else:
        cmd_2(dev, "\x8F\x00\x20\x1C\x09\x00", "packet W: 421/422, R: 423/424")

    if cont:
        # Generated from packet 425/426
        buff = bulk2(dev, "\x57\x91\x00", target=0x02, truncate=True)
    else:
        buff = bulk2(dev, "\x57\x8E\x00", target=0x02, truncate=True)
    # Discarded 510 / 512 bytes => 2 bytes
    validate_read("\x00\x00", buff, "packet W: 425/426, R: 427/428")
    
    led_mask(dev, 'pass')
    
    sm_info1(dev)

    sm_insert(dev)
    
    # Generated from packet 465/466
    buff = bulk2(dev, "\x22\x02\x10\x00\x13\x00\x06", target=0x08, truncate=True)
    # Discarded 504 / 512 bytes => 8 bytes
    '''
    validate_readv((
            "\x3C\x01\x00\x00\x9D\x00\x00\x00",
            "\x6B\x01\x00\x00\xCC\x00\x00\x00",
            "\x6C\x01\x00\x00\xCD\x00\x00\x00",
            "\x6D\x01\x00\x00\xCE\x00\x00\x00",
            ), buff, "packet W: 465/466, R: 467/468")
    '''

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    add_bool_arg(parser, '--cycle', default=False, help='') 
    add_bool_arg(parser, '--cont', default=True, help='Continuity check') 
    args = parser.parse_args()

    if args.cycle:
        print 'Cycling'
        wps = WPS7(host='raijin')
        wps.cycle([1, 2], t=2.0)
        # 1 second too short
        time.sleep(3)
        print 'Cycled'

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    #dev.resetDevice()
    startup.replay(dev)

    #time.sleep(3)

    fw = 2048 * '\xFF'
    replay(dev, fw, cont=args.cont)

    print 'Complete'
