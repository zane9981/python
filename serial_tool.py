#Create by Freedom:huangzheng@sinosims.com
import serial #http://pypi.python.org/pypi/pyserial
import sys
import thread

def read_com(handle):
    while True:
        sys.stdout.write(handle.read())

def write_com(handle):
    while True:
        handle.write(sys.stdin.readline()+'\r\n')

if __name__ == "__main__":
    if len(sys.argv) == 3:
        dev = sys.argv[1]
        rate = sys.argv[2]
    else:
        dev = '/dev/ttyUSB0'
        rate = 115200

    s = serial.Serial(dev, baudrate=rate,
                      bytesize=serial.EIGHTBITS,
                      parity=serial.PARITY_NONE,
                      stopbits=1)

    try:
        thread.start_new_thread( read_com, (s,) )
        thread.start_new_thread( write_com, (s,) )
    except:
        print "Error: unable to start thread"
        exit(-1)
    while 1:
        pass
