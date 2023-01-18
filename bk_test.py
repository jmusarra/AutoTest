#/usr/bin/env python3

__author__ = "John Musarra"
__license__ = "Creative Commons CC-BY"
__email__ = "john@mightymu.net"
__maintainer__ = "John Musarra"
__version__ = "alpha"

import serial, os, psycopg, datetime, time, requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

db_connection = psycopg.connect(host='localhost', dbname='jsm', user='jsm')
cursor = db_connection.cursor()

def make_pdf(pdf_data):
	print('Generating PDF....')
	page = canvas.Canvas('Test Report', pagesize = letter)
	page.drawString(350, 350, "Hurry up and do this part")
	width, height = letter
	print('PDF generation is not yet implemented 😿')
	return

def bk_comm(command):
    #send command to BK PSU, receive and return response
    print(f'Sending command: {command}')
    command_bytes = bytes(command + '\r', 'ascii') #append a carriage return and encode as bytes
    try:
        bk.write(command_bytes)
        response = bk.readline()
        #print(type(response))
        #print(response)
        #print(len(response))
    except TypeError:
	    print('PANic! PaniIcC!')
    if len(response) > 1:
        response_string = response.decode('UTF-8').strip('\r')
        print(f'Response: {response_string}')
        return response_string
    else:
        error = 'No response. Is PSU on?'
        print(error)
        pass

def write_to_db(data):
    cursor.execute(
    	'INSERT INTO jsm (timestamp, piece, current, "Show", length_of_tape, voltage) VALUES(%s, %s, %s, %s, %s, %s)',
    	(datetime.datetime.now(), data[0], data[1], data[2], data[3], data[4]))
    db_connection.commit()

device = "/dev/ttyUSB0" #dammit #"/dev/BK_1687" #symlinked to whatever the real TTY is
#Is the PSU plugged in?
if (os.path.exists(device)):
	device_connected = True
print(f'Device Connected? {device_connected}')
#how to detect if the PSU is powered on....
bk = serial.Serial(port = "/dev/BK_1687", baudrate = 9600, timeout = 0.5) #todo: add bytesize, parity, stopbits
bk_comm('SOUT1') #First thing, turn off the PSU output. Turn it back on when ready to start test.
#If PSU display reads "O P OFF" the last command has succeeded, yay I guess

#Begin logging first, while output is off, then turn output on
def do_test(piece_name, strip_length, show_name, active, duration=600, interval=5): #TODO: Add annotation for beginning of test with piece name and time of day
    if active == 'yes':
    	bk_comm('SOUT0')
    	time.sleep(1)
    test_begin_time = time.monotonic()
    iteration = 1
    while time.monotonic() - test_begin_time <= duration:
        display_values = bk_comm('GETD') #GETD is short for Get Display values. As opposed to (manually-input) settings values.
        assert display_values[0:5], "What now"
        print(f'Response: {display_values}')
        display_volts = (int(display_values[0:5])/1000)
        display_curr = (int(display_values[5:-4])/100)
        print(str(display_values[9]))
        print(f'Iteration = {iteration}')
        print(f'Volts: {display_volts}')
        print(f'Current: {display_curr}')
        iteration += 1
        data = [piece_name, display_curr, show_name, strip_length, display_volts]
        write_to_db(data)
        time.sleep(interval)
    bk_comm('SOUT1')
    data = [piece_name, 0, show_name, strip_length, display_volts]
    test_end_time = time.monotonic()
    send_annotation(piece_name, test_begin_time, test_end_time)
    return data

def send_annotation(piece_name, test_begin_time, test_end_time):
	#TODO: This
	pass

#TODO: print /dev devices, both symlink and target
#udev rule makes (unfortunately) any CP102x USB-serial device get symlinked as /dev/BK_1687
print("Press 't' to begin test, 'o' to toggle output")
control = input()
if control == 't':
    print('Name of piece?')
    piece_name = input()
    print('LED tape length?')
    strip_length = input()
    now = time.monotonic()
    do_test(piece_name, strip_length, show_name = 'testing', active = 'no', duration = 10, interval = 3)
    bk_comm('SOUT0')
    pdf_data = do_test(piece_name, strip_length, show_name = '2023 Disney Lighthouse', active = 'yes', duration = 300, interval = 5)
    time.sleep(3)
    bk_comm('SOUT1')
    test_duration = 'whatever'
    make_pdf(pdf_data)
    print("Test Concluded! Hurrah!")
if control == 'o':
    bk_comm('SOUT0')
    time.sleep(60)


#TODO: create test session, and create results PDF
