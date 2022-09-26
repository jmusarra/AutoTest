#/usr/bin/env python3

import serial, os psycopg
from reportlab.pdfgen import canvas

def make_pdf():
	print('Not yet implemented 😿')
	return

device = "/dev/BK_1687" #symlinked to whatever the real TTY is
#Is the PSU plugged in?
if (os.path.exists(device)):
	device_connected = True
print(f'Device Connected? {device_connected}')
#how to detect if the PSU is powered on....
bk = serial.Serial(port = "/dev/BK_1687", baudrate = 9600, timeout = 0.5) #todo: add bytesize, parity, stopbits
bk.write(b'SOUT1\r') #First thing, turn off the PSU output. Turn it back on when ready to start test.
#If PSU display reads "O P OFF" the last command has succeeded, yay I guess


#TODO: print /dev devices, both symlink and target
#udev rule makes (unfortunately) any CP102x USB-serial device get symlinked as /dev/BK_1687

bk.write(b'GETD\r') #GETD is short for Get Display values. As opposed to (manually-input)settings values.
bk_response = bk.readline()
print(f'Response: {bk_response}')
display_volts = (int(bk_response[0:5])/1000)
display_curr = (int(bk_response[5:-5])/100)
print(bk_response[0:5]) #volts
print(bk_response[5:-5]) #amps
print(str(bk_response[9]))
print(f'Volts: {display_volts}')
print(f'Current: {display_curr}')

#TODO: write values to database
#TODO: create test session, and create results PDF
