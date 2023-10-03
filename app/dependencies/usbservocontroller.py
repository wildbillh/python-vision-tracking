
from typing import List
import logging, serial, time

logger = logging.getLogger()


class ServoProperties:
    """
        Class used the hold the properties for each servo
    """


    def __init__(self):
        """
            Class which holds the property values for a single servo
        """
        self.min = 992
        self.max = 2000
        self.home = 1500
        self.pos = 1500
        self.speed = 200
        self.acceleration = 0
        self.disabled = True

    # --------------------------------------------------------------

    def setFromDict (self, propertyDict: dict):
        """
            Sets the individual variables from a full or partial dictionary
        """

        for key, val in propertyDict.items():
            if key in self.__dict__:
                setattr(self, key, val)
            else:
                logger.warning(f'Attempt to set unknown property {key} in {self.__class__.__name__}')
 
 # ================================================================

class USBServoController:
    """
        Class which controls each of the servos in a controller via USB
    """

    MAX_SERVOS = 6
    RATE = 115200

    # -------------------------------------------------------------
    #  
    def __init__(self):
        """
            Create placeholders for the vars and set the default servo properties
        """

        self.port = None
        self.servo_props: dict = []

        for i in range(USBServoController.MAX_SERVOS):
            self.servo_props.append(ServoProperties())
        
    
    # -------------------------------------------------------------------------

    def __del__(self):
        """
        """
        self.close() 
    
    # -------------------------------------------------------------

    def getServoProperties (self, channel) -> ServoProperties:
        """
        """
        return self.servo_props[channel]

    # ------------------------------------------------------------


    def setServoProperties (self, channel: int, props: dict = {}):


        """
            Set all or a subset of a servo's properties from a dictionary
        """

        if props:
            # Capture the state of disabled from the properties
            is_disabled = self.servo_props[channel].disabled
            # Set the new properties
            self.servo_props[channel].setFromDict(props)
            
            # If the disabled property has changed state, call the proper method
            if is_disabled and not self.servo_props[channel].disabled:
                self.setEnabled(channel)
            elif not is_disabled and  self.servo_props[channel].disabled:
                self.setDisabled(channel)
      

    # -------------------------------------------------------------------------
    
    def open (self, port, rate=115200):
        """
            Open the serial port
        """
        
        self.port = serial.Serial(port, USBServoController.RATE) 
        if not self.port.is_open:
            raise Exception (f"Could not open port {port}")
        
    # --------------------------------------------------------------------------    

    def close (self) -> None:
        """
            Close the port 
        """
        if hasattr(self, "port") and self.port is not None:
            self.port.close()
            self.port = None

    # -------------------------------------------------------------------------

    def writeCommand (self, message: bytearray, commandName: str):
        """
            Writes the bytearray command structure and checks for bytes written. Flushes the port
        """
        bytes_written = self.port.write(message)
        self.port.flush()
        if bytes_written != len(message):
            raise Exception (f"Expected {len(message)} bytes to be sent for {commandName} command")

    # -----------------------------------------------------------------------
    
    def setAcceleration(self, channel: int, val: int) -> None:
        """
            Set the acceleration to get smooth transitions
        """
    
        message = bytearray([0x89, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setAcceleration")
        self.servo_props[channel].acceleration = val

    # ---------------------------------------------------------------------------------------

    def getSpeed(self, channel: int) -> int:
        """
        """
        return self.servo_props[channel].speed
    
    # --------------------------------------------------------------------------------------

    def setSpeed(self, channel: int, val: int) -> None:
        """
            Set the acceleration to get smooth transitions
        """
        
        message = bytearray([0x87, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setSpeed")
        self.servo_props[channel].speed = val

    # --------------------------------------------------------------------------------------

    def setPositionSync (self, channel: int, microSeconds: int, timeout:int = 2) -> None:
        """
            Sets the position but doesn't return until the position is acheived or a timeout occurs
        """
        start = time.monotonic()
        self.setPosition(channel, microSeconds)
        while self.getPositionFromController(channel) != microSeconds:
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
        
        # Store the new position if we are not disabling the servo
        if microSeconds > 0:
            self.servo_props[channel].pos = microSeconds
        
    # -------------------------------------------------------------------------------    

    def getPosition (self, channel: int) -> int:
        """
            Return the servo position stored in the properties
        """

        return self.servo_props[channel].pos
    
    # -------------------------------------------------------------------------------

    def getPositionFromController(self, channel: int) -> int:
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
        pos = (receive_message[0] | (receive_message[1] << 8)) // 4

        self.servo_props[channel].pos = pos
        
        return pos
    
    # ----------------------------------------------------------------------------------------

    def setDisabled (self, channel) -> None:
        """
            Disable the servo and store the last position
        """

        self.setPosition(channel, 0)
        self.servo_props[channel].disabled = True
    
    # ---------------------------------------------------------------------------------------

    def setEnabled (self, channel) -> None:
        """
            Enable the servo and set a position
        """

        self.setPosition (channel, self.servo_props[channel].pos)
        self.servo_props[channel].disabled = False
        self.setSpeed(channel, self.servo_props[channel].speed)

     # -------------------------------------------------------------------------------------

    def returnToHome (self, channel: int, sync = False):
        """
            Return to the defined neutral position
        """
                         
        pos = self.servo_props[channel].home  
        if sync: 
            self.setPositionSync(channel, pos)
        else:
            self.setPosition(channel, pos)

     