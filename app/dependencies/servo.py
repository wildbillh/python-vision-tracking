import logging, serial, time

logger = logging.getLogger()

class USBServo:
    """
    Simple class that encapsolates use of the compact protocal to control servo's serially
    """

    DEFAULT_CONTROLLER_PROPS = {"min": 992, "max": 2000}
    DEFAULT_SERVO_PROPS = {"home": 1560, "speed": 200, "acceleration": 0}
    MAX_SERVOS = 6
    RATE = 115200

    def __init__(self, controllerProps = {}, servoProps = {}, actives = [i for i in range(6)]):
        """
        """
        
        self.port = None
        self.actives = actives
    
        # Store the controller properties
        self.controller_props = self.setControllerProperties(controllerProps)
       
        # If properties are supplied, merge with the defaults 
        self.servo_props = self.setServoProperties(servoProps)  

        # Setup the servo attributes
        self.servo_attrs = self.setServoAttrs()


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
        bytes_written = self.port.write(message)
        self.port.flush()
        if bytes_written != len(message):
            raise Exception (f"Expected {len(message)} bytes to be sent for {commandName} command")


    # -----------------------------------------------------------------------------

    def setServoAttrs (self):
        """
            Setup the servo attributes.
            Indicates whether a servo is disabled
        """
        servo_attrs = {}
        for i in range(USBServo.MAX_SERVOS):
            servo_attrs[i] = {"disabled": True, "pos": self.servo_props[i]["home"]}   

        return servo_attrs
    
    # ------------------------------------------------------------------------------
    
    def setControllerProperties (self, props):
        """
            Set up the controller properties.
            Determines min and max positions
        """
        controller_props = USBServo.DEFAULT_CONTROLLER_PROPS.copy()
        for key in props.keys():
            if key in controller_props:
                controller_props["key"] = props[key]
            else:
                logger.warning(f'Unexpected controller property: {key}')

        return controller_props
    
    # -------------------------------------------------------------------------

    def setServoProperties (self, props):
        """
            Setup the servo properties.
            Includes speed, acceleration and home position.
            Merge the current props with the new ones given
        """
        servo_props = {}
        for i in range(USBServo.MAX_SERVOS):
            servo_props[i] = USBServo.DEFAULT_SERVO_PROPS.copy()

            if i in props:
                prop = props[i]
                for key in prop.keys():
                    if key in servo_props[i]:
                        servo_props[i][key] = prop[key]

        return servo_props

    # -------------------------------------------------------------------------
    
    def open (self, comPort, rate=115200):
        """
            Open the serial port
        """
        
        self.port = serial.Serial(comPort, USBServo.RATE) 
        if not self.port.is_open:
            raise Exception (f"Could not open port {comPort}")
        
    # -------------------------------------------------------------------------

    def initializeActives (self, actives: list):
        """
            Sets the list of active servos and runs through a short initialization
            of each active servo
        """
        
        if not self.port.is_open:
            raise Exception ("Initialize call on unopen serial port")
        
        # Store the actives list
        self.actives = actives
        
        # For each channel, enable the servo and move to the min, max and home positions
        for channel in self.actives:

            speed = self.servo_props[channel]["speed"]
           
            # Set a slow speed to run through the min and max
            self.setSpeed(channel, 40)
            
            if self.servo_attrs[channel]["disabled"]:
                self.setEnabled(channel)
            
            # Go to the min, max and home positions
            self.setPositionSync(channel, self.controller_props["min"])
            self.setPositionSync(channel, self.controller_props["max"])
            self.returnToHome(channel)

            # Set the speed to the correct property value
            self.setSpeed(channel, speed)      
    
    # --------------------------------------------------------------------------    

    def close (self) -> None:
        """
            Close the port 
        """
        if self.port is not None:
            self.port.close()
            self.port = None
   
    # -------------------------------------------------------------------------------------

    def returnToHome (self, channel) -> int:
        """
            Return to the defined neutral position
        """
        pos = self.servo_props[channel]["home"]    
        self.setPositionSync(channel, pos)

        return pos

    # ---------------------------------------------------------------------------------------

    def setAcceleration(self, channel: int, val: int) -> None:
        """
            Set the acceleration to get smooth transitions
        """
    
        message = bytearray([0x89, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setAcceleration")

    # ----------------------------------------------------------------------------------------

    def setDisabled (self, channel) -> None:
        """
            Disable the servo and store the last position
        """
        pos = self.getPosition(channel)
        self.setPosition(channel, 0)
        self.servo_attrs[channel]["disabled"] = True
        self.servo_attrs[channel]["pos"] = pos if pos > 0 else self.servo_props[channel]["home"]
    
    # ---------------------------------------------------------------------------------------

    def setEnabled (self, channel) -> None:
        """
            Enable the servo and set a position
        """

        self.setPosition (channel, self.servo_attrs[channel]["pos"] if self.servo_attrs[channel]["pos"] > 0 else self.servo_props[channel]["home"])
        self.servo_attrs[channel]["disabled"] = False
        self.setSpeed(channel, self.servo_props[channel]["speed"])

    # ---------------------------------------------------------------------------------------

    def setSpeed(self, channel: int, val: int) -> None:
        """
            Set the acceleration to get smooth transitions
        """
        
        message = bytearray([0x87, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setSpeed")
        self.servo_props[channel]["speed"] = val

    # --------------------------------------------------------------------------------------

    def setPositionSync (self, channel: int, microSeconds: int, timeout:int = 2) -> None:
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
        
    def setPosition (self, channel: int, microSeconds: int) -> None:
        """
            Sets the microseconds for the designated channel 
        """
        
        quarter_ms = microSeconds * 4
        message = bytearray([0x84, channel, quarter_ms & 0x7F, (quarter_ms >> 7) & 0x7F])
        
        self.writeCommand(message, "setPosition")
        
        # Store the new position
        self.servo_attrs[channel]["pos"] = microSeconds
        
    # -------------------------------------------------------------------------------    


    def getPosition(self, channel: int) -> int:
        """
            Get the designated channel's position in microseconds
        """
        send_message = bytearray([0x90, channel])
        self.writeCommand(send_message, "getPosition")
       
        # Get the 2 byte position message
        receive_message = self.port.read(2)
        if len(receive_message) != 2:
            raise Exception (f'Error. Expected 2 bytes in return of getServerPosition but found {len(receive_message)}')

        # Decode the 2 bytes into an int
        position = (receive_message[0] | (receive_message[1] << 8)) // 4
        
        return position


usb = USBServo()
usb.open('COM4')
usb.initializeActives([5])
usb.setDisabled (5)


#usb.setEnabled(5)
#usb.setPositionSync(5, 1000)
#usb.setDisabled(5)
usb.close()



