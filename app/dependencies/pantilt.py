import logging, time
from typing import Dict
from app.dependencies.usbservocontroller import USBServoController

logger = logging.getLogger()

class PanTilt (USBServoController):
    """
    Simple class that encapsolates use of the compact protocal to control servo's serially
    """

    PAN = 0
    TILT = 1
    ALL = 2
    VALID_SERVOS = [0, 1, 2]
    SERVO_COUNT = 2

    def __init__(self, pan = 4, tilt = 5):
        """
        """

        max_servo = USBServoController.MAX_SERVOS -1

        if pan < 0 or pan > max_servo or tilt < 0 or tilt > max_servo:
            raise Exception(f'Valid servo values are between 0 and {max_servo}')
        
        super().__init__()
        self.pan = pan
        self.tilt = tilt
        self.servos: int = [pan, tilt]

    # -------------------------------------------------------------------------

    def open (self, port: str, rate: int = 115200, panProps: Dict = {}, tiltProps: Dict = {}):
        """
        """

        # Attempt to open the port
        super().open(port, rate)

        if panProps:
            self.setServoProperties(self.servos[PanTilt.PAN], panProps)

        if tiltProps:
            self.setServoProperties(self.servos[PanTilt.TILT], tiltProps)
        
    # -------------------------------------------------------------------------

    def initialize (self):
        """
            Sets the list of active servos and runs through a short initialization
            of each active servo
        """
        
        if not self.port.is_open:
            raise Exception ("Initialize call on unopen serial port")
        

        speeds = [self.getSpeed(self.pan), self.getSpeed(self.tilt)]
        props = [self.getServoProperties(self.pan), self.getServoProperties(self.tilt)]

        # Set to a slower speed
        self.setSpeed(self.pan, 30)
        self.setSpeed(self.tilt, 30)

        # Return to home
        self.setPositionSync(self.pan, props[0].home)
        self.setPositionSync(self.tilt, props[1].home)

        # Simultaneously drive each to the min position
        self.setPosition(self.pan, props[0].min)
        self.setPosition(self.tilt, props[1].min)
        time.sleep(1.5)

        # Likewise to the max position
        self.setPosition(self.pan, props[0].max)
        self.setPosition(self.tilt, props[1].max)
        time.sleep(1.5)

        # Return to home
        self.setPosition(self.pan, props[0].home)
        self.setPosition(self.tilt, props[1].home)
        time.sleep(1.5)

        # Reset the speed to the original value
        self.setSpeed(self.pan, speeds[0])
        self.setSpeed(self.tilt, speeds[1])

        

        """
        # For each channel, enable the servo and move to the min, max and home positions
        for i, channel in enumerate(self.servos):

            speed = self.controller_props["speed"]
           
            # Set a slow speed to run through the min and max
            self.setSpeed(channel, 40)
            
            if self.servo_attrs["disabled"]:
                self.setEnabled(channel)
            
            # Go to the min, max and home positions
            self.setPositionSync(channel, self.controller_props["min"])
            self.setPositionSync(channel, self.controller_props["max"])
            self.returnToHome(channel)

            # Set the speed to the correct property value
            self.setSpeed(channel, speed)      
    
        """
    # -------------------------------------------------------------------------------------

    def returnToHome (self, servo: int):
        """
            Return to the defined neutral position
        """

        if servo not in PanTilt.VALID_SERVOS:
            raise Exception (f'{servo} is not a valid servo. Only {PanTilt.VALID_SERVOS} allowed')
          
        servo_list = [PanTilt.PAN, PanTilt.TILT] if servo == PanTilt.ALL \
            else [servo]
          
        for i, which_servo in enumerate(servo_list):
            super().returnToHome(which_servo)
            
     

    # ---------------------------------------------------------------------------------------


    def disable (self, servo):

        if servo not in PanTilt.VALID_SERVOS:
            raise Exception (f'{servo} is not a valid servo. Only {PanTilt.VALID_SERVOS} allowed')

        servo_list = [PanTilt.PAN, PanTilt.TILT] if servo == PanTilt.ALL \
            else [servo]

        for i, which_servo in enumerate(servo_list):
            super().setDisabled(self.servos[which_servo])

    # ---------------------------------------------------------------------------------------

    def enable (self, servo):
        """
            Enable the designated servo's
        """

        if servo not in PanTilt.VALID_SERVOS:
            raise Exception (f'{servo} is not a valid servo. Only {PanTilt.VALID_SERVOS} allowed')
        
        servo_list = [PanTilt.PAN, PanTilt.TILT] if servo == PanTilt.ALL \
            else [servo]

        for i, which_servo in enumerate(servo_list):
            super().setEnabled(self.servos[which_servo])
