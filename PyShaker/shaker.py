import serial
import time

class PyShaker:

    def __init__(self, comport):
        
        self.interface=serial.Serial(comport, 9600, timeout=1)
        
    def _send_command(self, cmd_string):
        cmd_string = cmd_string + " \r"
        print(cmd_string)
        command = bytes(cmd_string, encoding='utf-8')
        self.interface.write(command)
        return self.interface.readline()
        
    def start(self, rpm=100, ramp_time=10):
        print(rpm)
        er = self._send_command("V"+str(rpm))
        print(er)
        er = self._send_command("A"+str(ramp_time))
        print(er)
        er = self._send_command("G")
        print(er)
        print("time start")
        time.sleep(ramp_time)
        print("time end")
    
    def stop(self):
        er = self._send_command("S")
        print(er)
    
    def get_speed(self):
        er = self._send_command("?W")
        print(er)