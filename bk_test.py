#!/usr/bin/env python3

__author__ = "John Musarra"
__license__ = "Apache 2.0"
__email__ = "john@mightymu.net"
__maintainer__ = "John Musarra"
__version__ = "alpha"

import serial, os, psycopg, time, requests, sys, random, sqlite3, json
import constants
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

db_connection = psycopg.connect(host='localhost', dbname='jsm', user='jsm')
cursor = db_connection.cursor()

def make_pdf(test_id):
    sql_get_from_id = 'SELECT "Show", piece, test_id, MAX(current), MAX(timestamp) - MIN(timestamp) as duration, length_of_tape, MAX(voltage) FROM jsm WHERE test_id = %s GROUP BY test_id, "Show", piece, length_of_tape'
    with psycopg.connect(host='localhost', dbname='jsm', user='jsm') as conn:
        with conn.cursor() as cur:
           cur.execute(sql_get_from_id, (test_id,))
           for record in cur:
               show_name = record[0]
               piece_name = record[1]
               max_current = record[3]
               duration = record[4]
               tape_length = record[5]
               voltage = record[6]
    cur.close()
    print('Generating PDF....')
    document_title = '/home/jsm/Desktop/TestReports/' + show_name + "-" + piece_name + '.pdf'
    watts_per_ft = (voltage * max_current) / tape_length
    print(f'Watts / ft: {watts_per_ft}')
    print(document_title)
    page = canvas.Canvas('test-report.pdf', pagesize = letter)
    page.drawString(250,750, 'Report Generated: ')
    page.drawString(355,750, datetime.now().strftime('%Y-%m-%d %-I:%M%p'))
    page.drawString(15, 750, "Show Name: ")
    page.drawString(100,750, show_name)
    page.drawString(15, 700, "Piece Name: ")
    page.drawString(100,700, piece_name)
    page.drawString(15,650, "Max Current: ")
    page.drawString(100,650, str(max_current))
    page.drawString(15,600, "Test ID: ")
    page.drawString(100,600, test_id)
    page.drawString(15,550, "Test Duration: ")
    page.drawString(100,550, str(duration))
    page.drawString(15,500,"Supply Voltage: ")
    page.drawString(110,500, str(voltage))
    page.drawString(15,450, "Length of Tape:")
    page.drawString(110,450, str(tape_length))
    page.drawString(15,400, "Watts / ft: ")
    page.drawString(100,400, str(watts_per_ft))
    width, height = letter
    page.showPage()
    page.save()

def bk_comm(command):
    #send command to BK PSU, receive and return response
    # print(f'Sending command: {command}')
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
        #print(f'Response: {response_string}')
        return response_string
    else:
        error = 'No response. Is PSU on?'
        print(error)
        pass

def generate_test_id():
    n = random.getrandbits(32)
    if n==0: return "0"
    chars="0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    length=len(chars)
    result=""
    remain=n
    while remain>0:
        pos = remain % length
        remain = remain // length
        result = chars[pos] + result
    return result[0:6]

def write_to_db(data):
    cursor.execute(
        'INSERT INTO jsm (timestamp, piece, test_id, current, "Show", length_of_tape, voltage) VALUES(%s, %s, %s, %s, %s, %s, %s)',
        (datetime.now(), data[0], data[1], data[2], data[3], data[4], data[5]))
    db_connection.commit()

device = "/dev/ttyUSB0" #dammit #"/dev/BK_1687" #symlinked to whatever the real TTY is
#Is the PSU plugged in?
if (os.path.exists(device)):
	device_connected = True
else:
	device_connected = False
	print('Power supply not found. Exiting.')
	sys.exit()
print(f'Device Connected? {device_connected}')
#how to detect if the PSU is powered on....
bk = serial.Serial(port = "/dev/BK_1687", baudrate = 9600, timeout = 0.5) #todo: add bytesize, parity, stopbits
bk_comm('SOUT1') #First thing, turn off the PSU output. Turn it back on when ready to start test.
#If PSU display reads "O P OFF" the last command has succeeded, yay I guess

#Begin logging first, while output is off, then turn output on
def do_test(piece_name, strip_length, test_id, show_name, output, duration, interval): #TODO: Add annotation for beginning of test with piece name and time of day
    print(f'Duration: {duration} seconds')
    test_start = datetime.now()
    if output == "on":
        bk_comm('SOUT0')
    else:
        bk_comm('SOUT1')
    while datetime.now() - test_start <= timedelta(seconds=duration):
        time.sleep(interval)
        display_values = bk_comm('GETD') #GETD is short for Get Display values. As opposed to (manually-input) settings values.
        assert display_values[0:5], "What now"
        # print(f'Response: {display_values}')
        display_volts = (int(display_values[0:5])/1000)
        display_curr = (int(display_values[5:-4])/100)
        print(str(display_values[9]))
        print('Time Elapsed: [DO THIS]')
        print(f'Volts: {display_volts}')
        print(f'Current: {display_curr}')
        data = [piece_name, test_id, display_curr, show_name, strip_length, display_volts]
        write_to_db(data)
    # data = [piece_name, 0, show_name, strip_length, display_volts] - WHY
    test_end_time = datetime.now()
    return data

def send_annotation(piece_name, test_begin_time, test_end_time, test_id):
    print("sending grafana annotation...")
    auth_url = 'http://localhost:3000/'
    headers = {'Authorization': constants.grafana_token, 'content-type': 'application/json', 'accept': 'application/json'}
    annotation_text = f'Piece Name: {piece_name} | Test ID: {test_id}'
    dashboard_uid = 'uz1kXiV4z'
    panel_id = 2
    annotation_data = {'dashboardUID':dashboard_uid,'time':test_begin_time, 'timeEnd':test_end_time,'text':annotation_text}
    response = requests.post('http://localhost:3000/api/annotations', data = json.dumps(annotation_data), headers = headers)
    #print(f'Test Begin: {test_begin_time}')
    #print(f'Test End: {test_end_time}')
    return response

#TODO: print /dev devices, both symlink and target
#udev rule makes (unfortunately) any CP102x USB-serial device get symlinked as /dev/BK_1687
print("Press 't' to begin test, 'o' to toggle output")
control = input()
if control == 't':
    try:
        test_id = generate_test_id()
        print(f'Test ID: {test_id}')
        print('Name of show?')
        show_name = input()
        print('Name of piece?')
        piece_name = input()
        print('LED tape length (in decimal feet)?')
        strip_length = input()
        test_begin = datetime.now().timestamp()
        test_begin_time = int(test_begin*1000)
        do_test(piece_name, strip_length, test_id, show_name, output = 'off', duration = 9, interval = 3)
        do_test(piece_name, strip_length, test_id, show_name, output = 'on',  duration = 300, interval = 5)
        do_test(piece_name, strip_length, test_id, show_name, output = 'off', duration = 10, interval = 3)
        test_end = datetime.now().timestamp()
        test_end_time = int(test_end*1000)
        send_annotation(piece_name, test_begin_time, test_end_time, test_id)
        pdf_data = "Time of test: , Test Duration: , Max Current: , Wattage: "
        bk_comm('SOUT1')
        # print(f'Test Duration: {test_duration}')
        make_pdf(test_id)
        print("Test Concluded! Hurrah!")
    except KeyboardInterrupt:
        bk_comm('SOUT1') #turn output off
        print("Exiting.")
        sys.exit()
if control == 'o':
    bk_comm('SOUT0')
    time.sleep(60)


#TODO: create test session, and create results PDF
