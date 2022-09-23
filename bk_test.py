#/usr/bin/env python3

import serial


bk = serial.Serial(port = "/dev/ttyUSB0", baudrate = 9600, timeout = 1) #todo: add bytesize, parity, stopbits
bk.write(b'GETD\r')
bk_response = bk.readline()
print(f'Response: {bk_response}')
display_volts = (int(bk_response[0:5])/1000)
display_curr = (int(bk_response[5:-4])/1000)
print(f'Volts: {display_volts}')
print(f'Current: {display_curr}')

#TODO: write values to database
#TODO: create test session, and create results PDF