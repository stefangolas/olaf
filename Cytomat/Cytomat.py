# -*- coding: utf-8 -*-
"""
Created on Mon Mar  8 17:14:03 2021

@author: stefa
"""
import sqlite3
import serial
import os
import pyodbc
import time
import pyodbc
import logging


class CytomatDBError(Exception):
    pass

class NoMatchesFound(CytomatDBError):
    
    def __init__(self, field, condition):
        self.field = field
        self.condition = condition
        message='No matches in database for condition: '+str(field)+'='+str(condition)
        super().__init__(message)
        

class CytomatDB:
    
    table_dict={'barcode':0,
                'location':1,
                'occupied':2,
                'datetime':3
            }

    
    def __init__(self, database_path):
        
        
        self.database = database_path        
        self.occupied_field='Occupied'
        self.barcode_field='Barcode'
        self.location_field='Location'
        self.datetime_field='Datetime'
        self.all_fields='*'
        

    #def _update_row_single_field(self, update_field, update_value, conditional_field, conditional_value):
    #    update_string='UPDATE slots SET '+ update_field + '=' + update_value + 'WHERE ' + conditional_field + '=' + conditional_value
    #    db_conn=sqlite3.connect(self.database)
    #    c=db_conn.cursor()
    #    c.execute(update_string)
    #    c.commit()

        
    def get_location_by_barcode(self, barcode):
        db_conn=pyodbc.connect(self.database)
        c=db_conn.cursor()
        c.execute('SELECT Location FROM Storage WHERE Barcode=?', (str(barcode)))
        response_list=c.fetchall()
        response = response_list[0]
        output_value = response[0]
        return output_value
    
    def get_occupancy_by_location(self, location):
        db_conn=pyodbc.connect(self.database)
        c=db_conn.cursor()
        c.execute('SELECT Occupied FROM Storage WHERE Location=?', (location))
        response_list=c.fetchall()
        response = response_list[0]
        output_value=response[0]
        return output_value
        
    def _view_table(self, ensure_response=True):
        print("viewing table")
        db_conn=pyodbc.connect(self.database)
        c=db_conn.cursor()
        #c.execute('SELECT ' + output_field + ' FROM Storage WHERE '+ input_field + '=?', (input_arg,))
        c.execute('select * from Storage')
        #c.execute("SELECT * FROM Storage WHERE Barcode = '3500004609'")
        response_list = c.fetchall()
        #if ensure_response and len(response_list)<1:
        #    raise NoMatchesFound(input_field, input_arg)
        print(response_list)
        return response_list

    
    def add_barcoded_plate(self,barcode, location):
        db_conn=pyodbc.connect(self.database)
        c=db_conn.cursor()
        c.execute('UPDATE Storage SET barcode=?, occupied=1 WHERE location=?',(barcode, location,))
        db_conn.commit()
    
    def add_plate_only(self, location):
        db_conn=pyodbc.connect(self.database)
        c=db_conn.cursor()
        c.execute('UPDATE Storage SET occupied=? WHERE location=?',(1, location,))
        db_conn.commit()
    
    def update_barcode_at_position(self,location,barcode):
        db_conn=pyodbc.connect(self.database)
        c=db_conn.cursor()
        c.execute('UPDATE Storage SET barcode=? WHERE location=?',(barcode, location,))
        db_conn.commit()
        
    def remove_plate(self, location):
        db_conn=pyodbc.connect(self.database)
        c=db_conn.cursor()
        c.execute('UPDATE Storage SET occupied=?, barcode=? WHERE location=?',(0, None, location,))
        db_conn.commit()



#a=CytomatDB(path_string)
#a.get_occupancy_by_location(3)
#a.get_location_by_barcode(3501004538)


class Cytomat:
    

    comport_settings='9600,N,8,1,N,CR'
    
    class cmd:
        
        def __init__(self, cmd_str, log_str, cmd_print = True):
            self.cmd_str = cmd_str
            self.log_str = log_str
            self.cmd_print = cmd_print
        
        def __call__(self, param = None):
            logging.info(self.log_str)
            if self.cmd_print:
                print(self.log_str)
            cmd_str = self.cmd_str
            if param:
                cmd_str = cmd_str + str(param)
            response = super()._send_command(cmd_str)
            return response
    
    cmd_get_plate = cmd(cmd_str = 'mv:st ', log_str = 'Getting plate')
    cmd_store_plate = cmd(cmd_str = 'mv:ts ', log_str = 'Storing plate')
    cmd_karousel_position = cmd(cmd_str = 'll:kp ', log_str = 'Positioning karousel')
    cmd_scan_handler_to_stacker = cmd(cmd_str = 'll:dp ', log_str = 'Scanner to stacker')
    cmd_scan_move_to_position = cmd(cmd_str = 'll:hb ', log_str = 'Move scanner to position')
    cmd_scan_read_barcode_position = cmd(cmd_str = 'll:bc ', log_str = 'Reading barcode')
    cmd_scan_get_barcode_position = cmd(cmd_str = 'ch:bc ', log_str = 'Getting barcode')
    
    ready_response = 'bs 00'
    no_error = 'er 00'
    
    max_try_counter = 99

    
    table_dict={'barcode':0,
                'location':1,
                'occupied':2,
                'datetime':3
                }

    def __init__(self, comPort, cytomatType, num_slots, db):
        print("cytomat initialized")
        self.comPort = comPort
        self.cytomatType = cytomatType
        self.num_slots = num_slots
        self.database_path = db
        
        self.database = CytomatDB(self.database_path)

        self.interface = serial.Serial(comPort, 9600, timeout=1)

    def _wait_until_ready(self, wait=3):
        check_if_busy_command = bytes('ch:bs \r', encoding='utf-8')
        response=''
        try_counter = 0
        while response != self.ready_response:
            self.interface.write(check_if_busy_command)
            response = self.interface.readline().decode().rstrip()
            print(response)
            try_counter += 1
            if try_counter > self.max_try_counter:
                raise Exception("Waited too long for ready response")
            time.sleep(wait)
            
        
    def _send_command(self, command):
        self._wait_until_ready()
        print("sending command " + command)
        command = command  + ' \r'
        command=bytes(command, encoding='utf8')
        self.interface.write(command)
        response = self.interface.readline().decode().rstrip()
        return response
    
    
    def get_plate_by_position(self, position):
    
        #Check in database if occupied=1
        occupied = self.database.get_occupancy_by_location(position)
        if occupied != 1:
            raise ValueError
            
        str_position = self.int_to_cytomat_position(position)
        get_plate_str = self.cmd_get_plate(str_position)
        response = self._send_command(get_plate_str)
        
        if response == 'er 00':
            self.database.remove_plate(position)
            
        return response
    
    def get_plate_by_range(self, starting_idx, range_length):
        counter = 0
        position = starting_idx
        occupied = 0
        while counter < range_length:
            occupied = self.database.get_occupancy_by_location(position)
            if occupied == 1:
                self.get_plate_by_position(position)
                print("Found plate at position " + str(position))
                return
            else:
                position += 1
                counter += 1
                
        raise ValueError
    
    def int_to_cytomat_position(self, position):
        position_str = str(position)
        position_str = position_str.zfill(3)
        return position_str

    def get_plate_by_barcode(self, barcode):
        plate_position = self.database.get_location_by_barcode(barcode)
        response = self.get_plate_by_position(plate_position)
        return response
    
    def get_location_by_barcode(self, barcode):
        plate_position = self.database.get_location_by_barcode(barcode)
        return plate_position
    
    def scan_barcode_at_position(self, position):
        
        position_str=self.int_to_cytomat_position(position)
        self.cmd_karousel_position(position_str)
        
        self.cmd_scan_handler_to_stacker('001')
        
        self.cmd_scan_move_to_position(position_str)
        
        self.cmd_scan_read_barcode_position(position_str)
        
        response = self.cmd_scan_get_barcode_position()
        
        if response == self.no_error:
            barcode = response
            self.database.update_barcode_at_position(position, barcode)
        else:
            raise Exception("The Cytomat encountered an error")
        
    def store_plate_by_position(self, position, barcode = None, scan_barcode=False):
                
        is_occupied = self.database.get_occupancy_by_location(position)
        if is_occupied != 0:
            raise Exception('Position is occupied')
        
        position_str = self.int_to_cytomat_position(position)
        self.cmd_store_plate(position_str)
        
        if scan_barcode:
            barcode = self.scan_barcode_at_position(position)
        elif barcode:
            self.database.add_barcoded_plate(barcode, position)
        else:
            self.database.add_plate_only(position)
            
    def get_temp(self):
        response = self._send_command("ch:it")
        return response
    
    def check_busy(self):
        response = self._send_command("ch:bs")
        return response
    
    def check_co2(self):
        response = self._send_command("ch:ic")
        return response
        
    def get_firmware_version(self):
        response = self._send_command("ch:ve")
        return response
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, tb):
        self.interface.close()
        
    