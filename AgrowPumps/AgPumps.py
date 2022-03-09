# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 13:32:51 2021

@author: stefa
"""

import minimalmodbus
from minimalmodbus import (MODE_ASCII, MODE_RTU)
import serial
import logging
import time


from pymodbus.client.sync import ModbusSerialClient as ModbusClient

class AgrowModbusInterface():
    
    modbus_pump_map={
    1:100,
    2:101,
    3:102,
    4:103,
    5:104,
    6:105
    } # Pump number to modbus register
    
    def __init__(self):
        pass
        #self.modbus = ModbusClient(method='rtu', port='COM14', baudrate=115200, timeout=1, stopbits = 1, bytesize = 8, parity = 'E')
        #self.modbus.connect()
    
    def __enter__(self):
        return self

    def pump_by_address(self,address,volume,speed='low'):
        
        try:
            assert(address in range(100,106))
        except:
            raise ValueError("Pump address out of range")
        
        if speed=='low':
            pumptime=volume/2
            power=60
    
        if speed=='high':
            pumptime=volume/7
            power=100
            
        self.ensure_set_speed(address = address, set_speed = power)
        
        print(volume)
        print(pumptime)
        time.sleep(pumptime)
    
        self.ensure_set_speed(address = address, set_speed = 0)
    
    def ensure_set_speed(self, address, set_speed):
    
        speed = self.modbus.read_holding_registers(address, 1, unit = self.unit).registers[0]
        
        while speed!=set_speed:
            self.modbus.write_register(address, set_speed, unit = self.unit)
            time.sleep(3)
            print(speed)
            
            try:
                speed = self.modbus.read_holding_registers(address, 1, unit = self.unit).registers[0]
            except:
                self.modbus.write_register(address, set_speed, unit = self.unit)
                break
            
    def pump_by_number(self, pump, volume, speed):
        self.pump_by_address(self.modbus_pump_map[pump], volume, speed = speed)
        
    def __exit__(self, type, value, tb):
        
        for pump in modbus_pump_map:
            address = modbus_pump_map[pump]
            self.ensure_set_speed(address, 0)
        
class AgrowPumps(AgrowModbusInterface):
    
    bacteria_pump_map={'0':1,'1':2,'2':3}
    
    def __init__(self, port, unit):
        #super().__init__()
        self.port = port
        self.unit = unit
        self.connect(self.port)
    
    def connect(self, port):
        self.modbus = ModbusClient(method = 'rtu', port = port, baudrate = 115200, timeout = 1, stopbits = 1, bytesize = 8, parity = 'E')
        self.modbus.connect()
    
    def ensure_empty(self):
        self.pump_by_number(pump = 6, volume = 65, speed = 'high') #Pump 6 is waste
    
    def bleach_clean(self):
        self.pump_by_number(pump = 4, volume = 28, speed = 'high')
        self.ensure_empty()
        self.pump_by_number(pump = 5, volume = 28, speed = 'high')
        self.ensure_empty()
    
    def refill_culture(self, culture_id, add_culture_vol):
        self.ensure_empty()
        if culture_id not in self.bacteria_pump_map:
            raise ValueError
        select_pump=self.bacteria_pump_map[culture_id]
        self.pump_by_number(pump = select_pump, volume=10, speed = 'low')
        self.pump_by_number(pump = 6, volume=15, speed = 'high')
        self.pump_by_number(pump = select_pump, volume = add_culture_vol, speed = 'low')
    
    def rinse_out(self, rinse_cycles=3):
        
        for _ in range(rinse_cycles):
            self.ensure_empty()
            self.pump_by_number(pump=5, volume=28, speed = 'high')
        self.ensure_empty()