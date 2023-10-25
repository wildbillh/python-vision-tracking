import logging, math, time
from typing import Dict, List, Tuple, Union
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
            Open the serial port and set the pan and tilt servo properties
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
        

        # Capture the speed of each servo so we can reset after the initialization
        speeds = [self.getSpeed(self.pan), self.getSpeed(self.tilt)]
        props = [self.getServoProperties(self.pan), self.getServoProperties(self.tilt)]
        
        # Set to a slower speed and enable the servos
        self.setSpeed(panSpeed=30, tiltSpeed=30, sync=True)
        self.enable(PanTilt.ALL)
        
        # Return to home
        self.returnToHome(servo=PanTilt.ALL, sync=True)

        # Simultaneously drive each to the min position
        super().setPositionMultiSync(infoList=[(self.pan, props[0].min), (self.tilt, props[1].min)])
        
        # Likewise to the max position
        super().setPositionMultiSync(infoList=[(self.pan, props[0].max), (self.tilt, props[1].max)])
        
        # Return to home
        self.returnToHome(servo=PanTilt.ALL, sync=True)

        # Reset the speed to the original value
        self.setSpeed(panSpeed=speeds[0], tiltSpeed=speeds[1])
        
        self.returnToHome(servo=PanTilt.ALL, sync=False)

    # -------------------------------------------------------------------------------------

    def calibrate (self, calibrationFile=None):
        """
            Calibrate the pan and tilt servos
        """

        super().calibrate (channel=self.pan, calibrationFile=calibrationFile)
        super().calibrate (channel=self.tilt, calibrationFile=calibrationFile)

    # ------------------------------------------------------------------------------------

    def calculateMovementTime (self, panDegrees = None, tiltDegrees = None, fps = 30) -> Tuple[float, int]:
        """
        """

        return_time = 0.0

        if panDegrees is not None:
            return_time = super().calculateMovementTime(channel=self.pan, degrees=panDegrees)[0]

        if tiltDegrees is not None:
            return_time += super().calculateMovementTime(channel=self.tilt, degrees=tiltDegrees)[0]
           

        return (return_time, math.ceil(return_time * fps))
    
    # ------------------------------------------------------------------------------------

    def setAcceleration (self, panAcceleration: Union[int, None] = None, tiltAcceleration: Union[int, None] = None) -> Tuple[int, int]: 
        """
            Sets the acceleration of the pan and tilt servos.
            Returns the current or new values
        """

        panReturn = super().getAcceleration(self.pan)
        tiltReturn = super().getAcceleration(self.tilt)


        if panAcceleration is None and tiltAcceleration is None:
            return (panReturn, tiltReturn)
     
        if panAcceleration is not None:
            panReturn = super().setAcceleration(self.pan, panAcceleration)

        if tiltAcceleration is not None:
            tiltReturn = super().setAcceleration(self.tilt, tiltAcceleration)   
     
        return (panReturn, tiltReturn)
    
    # -------------------------------------------------------------------------------------   

    def setPosition (self, panPos: Union[int, None] = None, tiltPos: Union[int, None] = None) -> List[Union[int, None]]:
        """
            Sets the position of the pan and tilt servos
        """

        if panPos is None and tiltPos is None:
            return [None, None]
        
        # Build the position parameters
        pos_parms = [(self.pan, panPos) if panPos else None, (self.tilt, tiltPos) if tiltPos else None]
        
        return super().setPositionMulti(infoList=pos_parms)

    
    
    def setRelativePos (self, panPos: float = None, tiltPos: float = None, units = 2, sync=False):
        """
            Sets the position of the specified servo to: (current position + val)
            Val can be positive or negative. 
        """
        if panPos is not None:
            super().setRelativePos(channel=self.pan, val=panPos, units=units, sync=sync)
        
        if tiltPos is not None:
            super().setRelativePos(channel=self.tilt, val=tiltPos, units=units, sync=sync)
    
    # -------------------------------------------------------------------------------------
    
    def setSpeed(self, panSpeed: Union[int, None] = None, tiltSpeed: Union[int, None] = None, sync = False) -> None:
        """
            Set the speed of the designated servo
        """
        if not panSpeed and not tiltSpeed:
            return
        
        speed_parms = [(self.pan, panSpeed) if panSpeed else None, (self.tilt, tiltSpeed) if tiltSpeed else None]
        super().setSpeedMulti(infoList=speed_parms, sync=sync)

    # -------------------------------------------------------------------------------------

    def returnToHome (self, servo: int, sync = False, timeout = 2):
        """
            Return to the defined neutral position
        """

        if servo not in PanTilt.VALID_SERVOS:
            raise Exception (f'{servo} is not a valid servo. Only {PanTilt.VALID_SERVOS} allowed')
        
        # Build the parameter list with the designated servos
        if servo == PanTilt.ALL:
            info_list = [self.pan, self.tilt] 
        elif servo == PanTilt.PAN:
            info_list = [self.pan, None]
        else:
            info_list = [None, self.tilt]

        if sync:
            super().returnToHomeMulti(channelList=info_list, sync=sync, timeout=timeout)

    # ---------------------------------------------------------------------------------------

    def disable (self, servo: int):
        """
            Disable the servo(s)
        """

        if servo not in PanTilt.VALID_SERVOS:
            raise Exception (f'{servo} is not a valid servo. Only {PanTilt.VALID_SERVOS} allowed')

        servo_list = [self.pan, self.tilt] if servo == PanTilt.ALL \
            else [servo]

        for channel in servo_list:
            super().setDisabled(channel=channel)

    # ---------------------------------------------------------------------------------------

    def enable (self, servo: int):
        """
            Enable the designated servo's
        """

        if servo not in PanTilt.VALID_SERVOS:
            raise Exception (f'{servo} is not a valid servo. Only {PanTilt.VALID_SERVOS} allowed')
        
        servo_list = [self.pan, self.tilt] if servo == PanTilt.ALL \
            else [self.servos[servo]]

        for channel in servo_list:
            super().setEnabled(channel=channel)

    # ----------------------------------------------------------------------------------------
    
    def setServoProperties (self, panProps: dict = {}, tiltProps: Dict = {}) -> None:
        """
            Sets the servo properties from one or more property dictionaries.
        """

        if panProps:
            super().setServoProperties(self.pan, panProps)
        if tiltProps:
            super().setServoProperties(self.tilt, tiltProps)