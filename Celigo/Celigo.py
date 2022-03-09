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


class Celigo:
    
    def __init__(self, dll_path = 'C:\\Program Files (x86)\\HAMILTON\\Library\\Brooks Celigo\\BrooksCeligo'):
        import clr
        clr.AddReference(dll_path)
        import clr # Must be called twice
        self.CeligoObj = clr.BrooksCeligo.Reader()
        
    def connect(self, ip):
        self.CeligoObj.Connect(ip)
        
    def login(self, username, password):
        self.CeligoObj.LogIn("svc_aicspipeline","P#ableDH")
        status = self.getSystemStatusEx()[1]
        self.ensureSystemReady(timeout = 10)
        
    
    def getSystemStatus(self):
        state = self.CeligoObj.GetSystemStatus(str())
        return state
    
    def getSystemStatusEx(self):
        state = self.CeligoObj.GetSystemStatusEx(str(),int(),int(),int(),str(),str())
        return state
    
    def ensureSystemReady(self, timeout = 120):
        start_time = time.time()
        status = self.getSystemStatusEx()[1]
        while 'Idle, HardwarePresent, ' not in status:
            time.sleep(1)
            status = self.getSystemStatusEx()[1]

            wait_time = time.time() - start_time
            if wait_time > timeout:
                raise ValueError
        
    
    def loadPlate(self, plateID = 0, description = '', plateType = ''):
        self.ensureSystemReady()
        self.CeligoObj.LoadPlate(plateID,  description, plateType)
        
    def ejectPlate(self):
        self.ensureSystemReady()
        self.CeligoObj.EjectPlate()
    
    def closeDoor(self):
        self.ensureSystemReady()
        self.CeligoObj.CloseDoor()
        
    def scan(self, acquire_settings):
        self.ensureSystemReady()
        acquisition_id = self.CeligoObj.Acquire(acquire_settings)
        return acquisition_id
    
    def exportImages(self, target_directory, image_format, stitching_mode): #image_format: 0 = jpg, 1 = tiff, 2 = bmp
        self.ensureSystemReady()
        self.CeligoObj.ExportImages(target_directory, image_format, stitching_mode)
    
        
    