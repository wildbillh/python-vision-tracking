import serial, time


class USBServo:
    """
    Simple class that encapsolates use of the compact protocal to control servo's serially
    """

    def __init__(self, props = {}):
        """
        """
        self.com_port = None
        self.max_servos = 6
        self.rate = 115200
        self.ssc = None
        
        # Setup the default properties for each servo
        self.props = {}
        for i in range(self.max_servos):
            self.props[i] = {"home": 1716, "min": 992, "max": 2000, "speed": 0, "acceleration": 0}

        # If properties are supplied, merge with the defaults
        if props:
            self.setProperties(props)

        print (self.props, flush=True)    


    # -------------------------------------------------------------------------

    def __del__(self):
        """
        """
        self.close()
    
    # -------------------------------------------------------------------------

    def setProperties (self, props):
        """
            Merge the current props with the new ones given
        """

        for i in range (self.max_servos):
            if i in props:
                prop = props[i]
                for key in prop.keys():
                    self.props[i][key] = prop[key]


    # -------------------------------------------------------------------------
    
    def open (self, comPort, rate=115200):
        self.com_port = comPort
        self.rate = rate

        self.ssc = serial.Serial(comPort, rate, timeout=5) 

    # --------------------------------------------------------------------------    

    def close (self):
        """
            Close the port 
        """
        if self.ssc is not None:
            self.ssc.close()
            self.ssc = None

    # ---------------------------------------------------------------------------------------

    def setAcceleration(self, channel: int, val: int):
        """
            Set the acceleration to get smooth transitions
        """

        message = bytearray([0x89, channel, val & 0x7F, (val >> 7) & 0x7F])
        bytes_written = self.ssc.write(message)
        if bytes_written != len(message):
            raise Exception (f"Expected {len(message)} bytes to be sent for setAcceleration command")

    
    # ---------------------------------------------------------------------------------------

    def setSpeed(self, channel: int, val: int):
        """
            Set the acceleration to get smooth transitions
        """

        message = bytearray([0x87, channel, val & 0x7F, (val >> 7) & 0x7F])
        bytes_written = self.ssc.write(message)
        if bytes_written != len(message):
            raise Exception (f"Expected {len(message)} bytes to be sent for setAcceleration command")

    # ---------------------------------------------------------------------------------------
        
    def setPosition (self, channel: int, microSeconds: int):
        """
            Sets the microseconds for the designated channel 
        """
        quarter_ms = microSeconds * 4
        message = bytearray([0x84, channel, quarter_ms & 0x7F, (quarter_ms >> 7) & 0x7F])
        
        bytes_written = self.ssc.write(message)
        if bytes_written != 4:
            raise Exception ("Expected 4 bytes to be sent for setServerPosition command")
        
    # -------------------------------------------------------------------------------    


    def getPosition(self, channel: int):
        """
            Get the designated channel's position in microseconds
        """
        send_message = bytearray([0x90, channel])
        bytes_written = self.ssc.write(send_message)
        if bytes_written != len(send_message):
            raise Exception ('Error trying to send command to getServerPosition')
       
        receive_message = self.ssc.read(2)
        if len(receive_message) != 2:
            raise Exception (f'Error. Expected 2 bytes in return of getServerPosition but found {len(receive_message)}')

        return (receive_message[0] | (receive_message[1] << 8)) // 4

"""
usb = USBServo({5: {"speed": 20, "acceleration": 50}})
usb.open('COM4')



#pos = usb.getPosition(5)
#print(f'pos = {pos}')
usb.setSpeed(5, 100)
usb.setPosition(5, 1300)
time.sleep(0.5)
pos = usb.getPosition(5)
usb.setAcceleration(5, 10)
usb.setPosition(5, 1800)
time.sleep(1.5)
#print(f'pos = {pos}', flush=True)
#usb.setPosition(5, 0)


usb.close()
"""


