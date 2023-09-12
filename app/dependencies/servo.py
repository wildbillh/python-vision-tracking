import logging, serial, time

logger = logging.getLogger()

class USBServo:
    """
    Simple class that encapsolates use of the compact protocal to control servo's serially
    """

    def __init__(self, controllerProps = {}, servoProps = {}, actives = [i for i in range(6)]):
        """
        """
        self.com_port = None
        self.max_servos = 6
        self.rate = 115200
        self.ssc = None
        self.actives = actives
        self.servo_props = {}

        self.controller_props = {"min": 992, "max": 2000}
        for key in controllerProps.keys():
            if key in self.controller_props:
                self.controller_props["key"] = controllerProps[key]
            else:
                logger.warning(f'Unexpected controller property: {key}')

        
        # Setup the default properties for each servo
        
        self.servo_attrs = {}
        for i in range(self.max_servos):
            self.servo_props[i] = {"home": 1560, "speed": 200, "acceleration": 0}
            self.servo_attrs[i] = {"disabled": True, "pos": self.servo_props[i]["home"]}

        # If properties are supplied, merge with the defaults
        if servoProps:
            self.setServoProperties(servoProps)  
   
                
        self.servo_attrs = {}


    # -------------------------------------------------------------------------

    def __del__(self):
        """
        """
        self.close()
    
    
    # -------------------------------------------------------------------------

    def writeCommand (self, message: bytearray, commandName: str):
        """
            Writes the bytearray command structure and checks for bytes written. Flushes the port
        """
        bytes_written = self.ssc.write(message)
        self.ssc.flush()
        if bytes_written != len(message):
            raise Exception (f"Expected {len(message)} bytes to be sent for {commandName} command")

    
    # -------------------------------------------------------------------------

    def setServoProperties (self, props):
        """
            Merge the current props with the new ones given
        """
        for i in range(self.max_servos):
            self.servo_props[i] = {"home": 1560, "speed": 200, "acceleration": 0}

        for i in range (self.max_servos):
            if i in props:
                prop = props[i]
                for key in prop.keys():
                    if key in self.servo_props[i]:
                        self.servo_props[i][key] = prop[key]


    # -------------------------------------------------------------------------
    
    def open (self, comPort, rate=115200):
        """
            Open the serial port
        """
        self.com_port = comPort
        self.rate = rate
        self.ssc = serial.Serial(comPort, rate) 
        
    # -------------------------------------------------------------------------

    def initializeActives (self, actives: list):
        """
            Sets the list of active servos and runs through a short initialization
        """
        
        if not self.ssc.is_open:
            raise Exception ("Initialize call on unopen serial port")
        
        self.actives = actives
        
        for channel in self.actives:
           
            # Set a slow speed to run through the min and max
            self.setSpeed(channel, 40)
            
            # If the servo is asleep, wake it up
            pos = self.getPosition(channel)
            self.setPositionSync(channel, pos if pos >= self.controller_props["min"] and pos <= self.controller_props["max"] else self.servo_props[channel]["home"])
            
            # Go to the min, max and home positions
            self.setPositionSync(channel, self.controller_props["min"])
            self.setPositionSync(channel, self.controller_props["max"])
            self.returnToHome(channel)

            # Set the speed to the correct property value
            self.setSpeed(channel, self.servo_props[channel]["speed"])

            
    
    # --------------------------------------------------------------------------    

    def close (self):
        """
            Close the port 
        """
        if self.ssc is not None:
            self.ssc.close()
            self.ssc = None

    # -----------------------------------------------------------------------------
    
    def disableServo (self, channel):
        self.setPositionSync(channel, 0)
    
    # -------------------------------------------------------------------------------------

    def returnToHome (self, channel):
        """
            Return to the defined neutral position
        """
        self.setPositionSync(channel, self.servo_props[channel]["home"])


    # -------------------------------------------------------------------------------------
    
    def flush (self):
        self.ssc.flush()

    # ---------------------------------------------------------------------------------------

    def setAcceleration(self, channel: int, val: int):
        """
            Set the acceleration to get smooth transitions
        """
    
        message = bytearray([0x89, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setAcceleration")

    
    # ---------------------------------------------------------------------------------------

    def setSpeed(self, channel: int, val: int):
        """
            Set the acceleration to get smooth transitions
        """
        
        message = bytearray([0x87, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setSpeed")
        self.servo_props[channel]["speed"] = val

    
    # --------------------------------------------------------------------------------------

    def setPositionSync (self, channel: int, microSeconds, timeout = 2):
        """
            Sets the position but doesn't return until the position is acheived or a timeout occurs
        """
        start = time.monotonic()
        self.setPosition(channel, microSeconds)
        while self.getPosition(channel) != microSeconds:
            time.sleep(0.004)
            if (time.monotonic() - start) > timeout:
                logger.warning("Timeout occured before setPositionSync() function completed")
                break
    
    # ---------------------------------------------------------------------------------------
        
    def setPosition (self, channel: int, microSeconds: int):
        """
            Sets the microseconds for the designated channel 
        """
        
        quarter_ms = microSeconds * 4
        message = bytearray([0x84, channel, quarter_ms & 0x7F, (quarter_ms >> 7) & 0x7F])
        
        self.writeCommand(message, "setPosition")
        
    # -------------------------------------------------------------------------------    


    def getPosition(self, channel: int):
        """
            Get the designated channel's position in microseconds
        """
        send_message = bytearray([0x90, channel])
        self.writeCommand(send_message, "getPosition")
       
        receive_message = self.ssc.read(2)
        if len(receive_message) != 2:
            raise Exception (f'Error. Expected 2 bytes in return of getServerPosition but found {len(receive_message)}')

        position = (receive_message[0] | (receive_message[1] << 8)) // 4
        
        return position


usb = USBServo()
usb.open('COM4')
usb.initializeActives([5])


usb.disableServo (5)

usb.close()



