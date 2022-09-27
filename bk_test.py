#/usr/bin/env python3

import serial, os, psycopg, time
from reportlab.pdfgen import canvas

db_connection = psycopg.connect(host='localhost', dbname='jsm', user='jsm', password='Cattail*Unharmed*Clubbing6')
cursor = db_connection.cursor()

def make_pdf():
	print('Not yet implemented 😿')
	return

def bk_comm(command):
	#send command to BK PSU, receive and return response
	print(f'Sending command: {command}')
	command_bytes = bytes(command + '\r', 'ascii') #append a carriage return and encode as bytes
	bk.write(command_bytes)
	response = bk.readline()
	if response:
	   response_string = response.decode('UTF-8')
	   print(f'Response: {response_string}')
	   return response_string
	else:
	    error = 'No response. Is PSU on?'
	    print(error)
	    return error

def write_to_db(data):
    cursor.execute('''
    	INSERT INTO jsm (timestamp, piece, current, Show, length_of_tape) 
    	VALUES(%s, %s. %s. %s. %s)
    	'''
    	(data[0], data[1]. data[2], data[3])
    cursor.commit()

device = "/dev/BK_1687" #symlinked to whatever the real TTY is
#Is the PSU plugged in?
if (os.path.exists(device)):
	device_connected = True
print(f'Device Connected? {device_connected}')
#how to detect if the PSU is powered on....
bk = serial.Serial(port = "/dev/BK_1687", baudrate = 9600, timeout = 0.5) #todo: add bytesize, parity, stopbits
bk_comm('SOUT1') #First thing, turn off the PSU output. Turn it back on when ready to start test.
#If PSU display reads "O P OFF" the last command has succeeded, yay I guess



#TODO: print /dev devices, both symlink and target
#udev rule makes (unfortunately) any CP102x USB-serial device get symlinked as /dev/BK_1687
bk_comm('SOUT0')
time.sleep(3)
display_values = bk_comm('GETD') #GETD is short for Get Display values. As opposed to (manually-input)settings values.
print(f'Response: {display_values}')
if type(display_values[0:5]) == int:
    display_volts = (int(display_values[0:5])/1000)
else:
	print('Not a valid response. Is PSU on?')
display_curr = (int(display_values[5:-5])/100)
#print(bk_response[0:5]) #volts
#print(bk_response[5:-5]) #amps
print(str(display_values[9]))
print(f'Volts: {display_volts}')
print(f'Current: {display_curr}')
data = ['name of piece', display_curr, 'name of show', 'length_of_tape']

write_to_db(data)

#TODO: write values to database
#TODO: create test session, and create results PDF
