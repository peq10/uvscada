RM=rm -f
CP=cp
TAR=tar
GZIP=gzip
MKDIR=mkdir

KDIR:=/lib/modules/$(shell uname -r)/build

EXTRA_CFLAGS += -I$(KDIR)/drivers/usb/serial -Wall -Werror

obj-m:=uvscopetek.o

default:
	$(MAKE) -C $(KDIR) $(EXTRA_CFLAGS) SUBDIRS=$(PWD) modules

clean:
	$(RM) *.mod.c *.o *.ko .*.cmd *~ Modules.* modules.*

load:
	insmod uvscopetek.ko
	
unload:
	rmmod uvscopetek

install:
	insmod ./uvscopetek.ko

uninstall:
	rmmod uvscopetek

.PHONY: default clean load unload install uninstall dist

go: default
	-rmmod uvscopetek
	insmod ./uvscopetek.ko
	#-dd if=/dev/uvscopetek0  of=dump.bin count=1024
	#hexdump -C dump.bin
	#dmesg |tail
	mplayer /dev/uvscopetek0 -rawvideo format=rgb24:w=640:h=480 -demuxer rawvideo

run: default user
	-rmmod uvscopetek
	insmod ./uvscopetek.ko
	./user
	hexdump -C read.bin |head -n 30
	
.PHONY: user
user:
	g++ user.cpp -o user
	

