import serial




class USBServo:
    """
    Simple class that encapsolates use of the compact protocal to control servo's serially
    """

    def __init__(self):
        """
        """
        self.com_port = None
        
        self.rate = 115200
        self.ssc = None

    # -------------------------------------------------------------------------

    def __del__(self):
        """
        """
        self.close()
    
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
        
    def setServoPosition (self, channel, microSeconds):
        """
            Sets the microseconds for the designated channel 
        """
        quarter_ms = microSeconds * 4
        message = bytearray([0x84, channel, quarter_ms & 0x7F, (quarter_ms >> 7) & 0x7F])
        
        bytes_written = self.ssc.write(message)
        if bytes_written != 4:
            raise Exception ("Expected 4 bytes to be sent for setServerPosition command")
        
    # -------------------------------------------------------------------------------    


    def getServoPosition(self, channel):
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
usb = USBServo()
usb.open('COM4')



pos = usb.getServoPosition(5)
print(f'pos = {pos}')
usb.setServoPosition(5, 0)
pos = usb.getServoPosition(5)
print(f'pos = {pos}', flush=True)


usb.close()

"""