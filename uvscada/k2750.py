from uvscada.plx_usb import PUGpib

import re
import time

# -1.25629986E-02VDC,+2319.404SECS,+10155RDNG#
# -3.47094010E-06VDC,+4854.721SECS,+20115RDNG#
volt_dc_re = re.compile("(.*)VDC,(.*)SECS,(.*)RDNG#")
# -4.15096054E-07ADC,+5064.727SECS,+22239RDNG#
curr_dc_re = re.compile("(.*)ADC,(.*)SECS,(.*)RDNG#")
# +9.9E37,+201975.327SECS,+1846855RDNG#
# +6.97856784E-01OHM,+201938.582SECS,+1846490RDNG#
res_re = re.compile("(.*),(.*)SECS,(.*)RDNG#")

class K2750(object):
    def __init__(self, port='/dev/ttyUSB0', clr=True, ident=True):
        self.gpib = PUGpib(port=port, addr=16, clr=clr, eos=3, ser_timeout=1.0, gpib_timeout=0.9)
        self.func = None
        self.vendor = None
        self.model = None
        self.sn = None
        if ident:
            vendor, model = self.ident()
            if (vendor, model) != ('KEITHLEY INSTRUMENTS INC.', 'MODEL 2750'):
                raise ValueError('Bad instrument: %s, %s' % (vendor, model))

    def ident(self):
        # just vendor, model
        return self.ident_ex()[0:2]
        
    def ident_ex(self):
        '''
        Returns the manufacturer, model number, serial
        number, and firmware revision levels of the
        unit.
        ['KEITHLEY INSTRUMENTS INC.', 'MODEL 2750', '0967413', 'A07  /A01']
        '''
        ret = self.gpib.sendrecv_str("*IDN?").split(',')
        self.vendor = ret[0]
        self.model = ret[1]
        sn = ret[2]
        fw = ret[3]
        return (self.vendor, self.model, sn, fw)

    def card_sn(self):
        return self.gpib.sendrecv_str("SYSTem:CARD1:SNUMber?")

    def tim_int(self):
        '''Query timer interval'''
        return float(self.gpib.snd_rcv('TRIGger:TIMer?'))

    def local(self):
        '''Go to local mode'''
        # Error -113
        self.gpib.snd('GTL')

    def set_beep(self, en):
        '''
        You can disable the beeper for limits and continuity tests. However, when limits or CONT
        is again selected, the beeper will automatically enable.
        '''
        if en:
            self.gpib.snd("SYSTEM:BEEPER OFF")
        else:
            self.gpib.snd("SYSTEM:BEEPER ON")

    def error(self):
        '''Get next error from queue'''
        return self.gpib.snd_rcv("SYSTEM:ERROR?")

    def errors(self):
        ret = []
        while True:
            e = self.error()
            if e == '0,"No error"':
                return ret
            ret.append(e)
    
    def volt_dc_ex(self):
        if self.func != 'VOLT:DC':
            self.gpib.snd(":FUNC 'VOLT:DC'")
            time.sleep(0.20)
            self.func = 'VOLT:DC'

        raw = self.gpib.snd_rcv(":DATA?")
        m = volt_dc_re.match(raw)
        if not m:
            raise Exception("Bad reading: %s" % (raw,))
        vdc = float(m.group(1))
        secs = float(m.group(2))
        rdng = float(m.group(3))
        return {"VDC": vdc, "SECS": secs, "RDNG#": rdng}

    def volt_dc(self):
        return self.volt_dc_ex()["VDC"]

    def curr_dc_ex(self):
        if self.func != 'CURR:DC':
            self.gpib.snd(":FUNC 'CURR:DC'")
            # Seems to take at least 0.1 sec
            # had problems with 0.15
            time.sleep(0.20)
            self.func = 'CURR:DC'

        raw = self.gpib.snd_rcv(":DATA?")
        m = curr_dc_re.match(raw)
        if not m:
            raise Exception("Bad reading: %s" % (raw,))
        adc = float(m.group(1))
        secs = float(m.group(2))
        rdngn = float(m.group(3))
        return {"ADC": adc, "SECS": secs, "RDNG#": rdngn}

    def curr_dc(self):
        return self.curr_dc_ex()["ADC"]

    def res_ex(self):
        if self.func != 'RES':
            self.gpib.snd(":FUNC 'RES'")
            # Seems to take at least 0.1 sec
            # had problems with 0.15
            time.sleep(0.20)
            self.func = 'RES'

        raw = self.gpib.snd_rcv(":DATA?")
        m = res_re.match(raw)
        if not m:
            raise Exception("Bad reading: %s" % (raw,))
        adc = m.group(1)
        if adc.find('OHM') >= 0:
            adc = float(adc.replace('OHM', ''))
        else:
            adc = float('inf')
        secs = float(m.group(2))
        rdngn = float(m.group(3))
        return {"ADC": adc, "SECS": secs, "RDNG#": rdngn}

    def res(self):
        return self.res_ex()["ADC"]
