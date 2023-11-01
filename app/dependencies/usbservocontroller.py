import timeit
from typing import Dict, List, Tuple, Union
import json, logging, math, os, serial, time
from collections.abc import Iterable
from threading import Thread
from jproperties import Properties
from app.dependencies.utils import importProperties

logger = logging.getLogger()


class ServoProperties:
    """
        Class used the hold the properties for each servo
    """

    def __init__(self, rangeDegrees = 120):
        """
            Class which holds the property values for a single servo
        """
        self.min = 992
        self.max = 2000
        self.home = 1500
        self.pos = 1500
        self.speed = 200
        self.acceleration = 0
        self.range_degrees = rangeDegrees
        
        self.disabled = True
        self.microseconds_per_degree = (self.max - self.min) / rangeDegrees
        self.microseconds_per_radian =  self.microseconds_per_degree * (180 / math.pi)
        self.calibration = None

    # --------------------------------------------------------------

    def setFromDict (self, propertyDict: Dict) -> None:
        """
            Sets the individual variables from a full or partial dictionary
        """

        for key, val in propertyDict.items():
            if key in self.__dict__:
                setattr(self, key, val)
            else:
                logger.warning(f'Attempt to set unknown property {key} in {self.__class__.__name__}')

        self.microseconds_per_degree = (self.max - self.min) / self.range_degrees
        self.microseconds_per_radian =  self.microseconds_per_degree * (180 / math.pi)

 # ================================================================

class USBServoController:
    """
        Class which controls each of the servos in a controller via USB
    """

    MAX_SERVOS = 6
    RATE = 115200
    MICROSECONDS = 0
    RADIANS = 1
    DEGREES = 2


    # -------------------------------------------------------------
    #  
    def __init__(self):
        """
            Create placeholders for the vars and set the default servo properties
        """

        self.port = None
        self.servo_props: dict = []
        self.is_thread_running = False
    
        # Set the default servo properties
        for i in range(USBServoController.MAX_SERVOS):
            self.servo_props.append(ServoProperties())     
    
    # -------------------------------------------------------------------------

    def __del__(self):
        """
            When the class goes out of scope, perform cleanup.
        """
        self.close() 
    
    # ------------------------------------------------------------------------

    def calibrate (self, channel:int, calibrationFile:Union[str, None] = None) -> None:
        """
            Builds a list of servo times to accomplish a move in x degrees (0-45).
            Stored as a list where index is degrees and value is seconds.
            If calibrationFile is supplied attempts to find an entry in the given
            property file. If file or entry is not found build/modifies the file.

        """

 
        # No calibration file is given so do the calibration and store to servo props
        if calibrationFile is None:
            logger.info(f'Calibrating servo: {channel} ....')
            self.calibrateServo(channel=channel)
            return

        # To get here a calibration property filename is supplied
        props = self.servo_props[channel]
        propertyName = f"{channel}-{props.speed}-{props.acceleration}"
        cal_props = Properties()

        # if we find the file
        if os.path.isfile(calibrationFile):
            
            with open (calibrationFile, 'rb') as f:
                cal_props.load(f, encoding='utf-8')
            
            # We found the needed property so load in the servo props and return
            if propertyName in cal_props.keys():
                props.calibration = json.loads(cal_props.get(propertyName).data)
                logger.info(f"Using stored calibration values for channel: {channel}") 
                return
        else:
            logger.info(f'Calibration file: {calibrationFile} not found. Building....') 

        # To get here either the property file does not exist or the entry was not found      
        logger.info(f'Calibrating servo: {channel} ....')
        cal_props[propertyName] = json.dumps(self.calibrateServo(channel))
        with open (calibrationFile, 'wb') as f:
            cal_props.store(f, encoding='utf-8')


    # --------------------------------------------------------------------------------------------

    def calibrateServo (self, channel: int) -> List[float]:
        """
            Run through a calibration stage moving the servo from 0 to 45 degrees. 
            Record the time for each move and store it in the servo properties
        """
        
        props = self.servo_props[channel]
        props.calibration = []
        # Store the original position of the servo so we can set it back
        original_pos = props.pos

        for i in range(0,46):
            start = timeit.default_timer()
            USBServoController.setRelativePos(self, channel, i if i % 2 == 0 else -abs(i), sync=True)
            props.calibration.append(timeit.default_timer() - start)

        # Restore the original position
        self.setPositionSync(channel, original_pos)
        return props.calibration
    
   
    #--------------------------------------------------------------------------------------

    def calculateMovementTime (self, channel: int, degrees: float, fps: int = 30) -> Tuple[float, int]:
        """
            Retreive the stored time and number of frames needed to move each servo the specified degrees
        """
        degrees = abs(degrees) if abs(degrees) < 45 else 45
        seconds = self.servo_props[channel].calibration[math.ceil(degrees)]
        frames_to_skip = math.ceil(fps * seconds)

        return (seconds, frames_to_skip)

    # -------------------------------------------------------------

    def getServoProperties (self, channel) -> ServoProperties:
        """
            Return all of the properties for a particular servo
        """
        return self.servo_props[channel]

    # ------------------------------------------------------------


    def setServoProperties (self, channel: int, props: dict = {}) -> None:
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
                USBServoController.setEnabled(self, channel=channel)
            elif not is_disabled and  self.servo_props[channel].disabled:
                USBServoController.setDisabled(self, channel=channel)   

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
        if hasattr(self, "port") and self.port is not None and self.port.is_open:
            for i in range(USBServoController.MAX_SERVOS):
                if not self.servo_props[i].disabled:
                    USBServoController.setDisabled(self, channel=i)

            self.port.close()
            self.port = None

    # -------------------------------------------------------------------------

    def writeCommand (self, message: bytearray, commandName: str) -> None:
        """
            Writes the bytearray command structure and checks for bytes written. Flushes the port
        """
        bytes_written = self.port.write(message)
        self.port.flush()
        if bytes_written != len(message):
            raise Exception (f"Expected {len(message)} bytes to be sent for {commandName} command")

    # --------------------------------------------------------------------------------------
    
    def getAcceleration (self, channel) -> int:
        """
            Returns the set acceleration for a channel/servo.
        """
        return self.servo_props[channel].acceleration
      
    # ---------------------------------------------------------------------------------------
    
    def setAcceleration(self, channel: int, val: int) -> int:
        """
            Set the acceleration to get smooth transitions
        """

        message = bytearray([0x89, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setAcceleration")
        self.servo_props[channel].acceleration = val
        return val

    # ---------------------------------------------------------------------------------------

    def getSpeed(self, channel: int) -> int:
        """
            Gets the speed stored in the properties
        """
        return self.servo_props[channel].speed
    
    # --------------------------------------------------------------------------------------

    def setSpeed(self, channel: int, val: int) -> None:
        """
            Set the speed of the servo
        """

        message = bytearray([0x87, channel, val & 0x7F, (val >> 7) & 0x7F])
        self.writeCommand(message, "setSpeed")
        self.servo_props[channel].speed = val

     # ---------------------------------------------------------------------------------------

    def setSpeedMulti (self, infoList: List[Union[Tuple[int, int], None]], sync = False) -> None:
        """
            Sets the speed of multiple servos. 
            If sync is set to true, also sets the position to the current positions
        """
        for info in infoList:
            if info:
                USBServoController.setSpeed(self, channel=info[0], val=info[1])
                # If sync is true, call setPositionSync on the current pos to make sure the speed takes
                if sync:    
                    USBServoController.setPositionSync(self, channel=info[0], val=self.servo_props[info[0]].pos)

    # ---------------------------------------------------------------------------------------

    def setPosition (self, channel: int, val: int, units = 0) -> int:
        """
            Sets the microseconds for the designated channel 
        """

        new_pos = val

        # if the desired position is less than min or greater than max, use those values instead.     
        if new_pos != 0:
            if new_pos < self.servo_props[channel].min:
                new_pos = self.servo_props[channel].min
            elif new_pos > self.servo_props[channel].max:
                new_pos = self.servo_props[channel].max 
 

        # Calculate the quarter microseconds and generate the message
        quarter_ms = new_pos * 4
        message = bytearray([0x84, channel, quarter_ms & 0x7F, (quarter_ms >> 7) & 0x7F])
        
        self.writeCommand(message, "setPosition")
        
        # Store the new position if we are not disabling the servo
        if new_pos > 0:
            self.servo_props[channel].pos = new_pos
            return new_pos
        
        return 0

    # --------------------------------------------------------------------------------------

    def setPositionSync (self, channel: int, val: int, timeout:int = 3) -> None:
        """
            Sets the position but doesn't return until the position is acheived or a timeout occurs
        """
        
        start = time.monotonic()
        # Get the position returned from setPosition. If we ask for a pos < min or > max
        # then the actual position will be different
        pos = USBServoController.setPosition(self, channel=channel, val=val)
        while USBServoController.getPositionFromController(self, channel=channel) != pos:
            time.sleep(0.001)
            if (time.monotonic() - start) > timeout:
                logger.warning("Timeout occured before setPositionSync() function completed")
                break
    
    # -----------------------------------------------------------------------------------

    def setPositionMulti (self, infoList: List[Union[Tuple[int, int], None]]) -> List[Union[int, None]]:
        """
            Sets the position of multiple servos. Returns a list of positions. 
            Note that the inputs are Tuples or None and the output is the same
            number of inputs (int or None)
        """

        if not isinstance(infoList, Iterable):
            return USBServoController.setPosition(self, channel=infoList[0], val=infoList[1])
        
        ret_pos_list = []
        for info in infoList:
            if info:
                ret_pos_list.append(USBServoController.setPosition(self, channel=info[0], val=info[1]))
            else:
                ret_pos_list.append(None)

        return ret_pos_list
    
    # ----------------------------------------------------------------------------------------

    def setPositionMultiSync (self, infoList: List[Union[Tuple[int, int], None]], timeout:int = 2, is_threaded=False) -> List[Union[int, None]]:
        """
            Sets the position of multiple servos, waiting until the positions are achieved or 
            the timeout occurs before returning.
        """
        input_len = len(infoList)

        if is_threaded and self.is_thread_running:
            logger.error("Attempt to start new thread before prior thread completed")
            return [None] * input_len
        
        
        completed_list = [False] * input_len
        ret_pos_list = [None] * input_len

        # Set the positions for all of the provided inputs
        # Any list elements that are passed as None are already complete
        for i, info in enumerate(infoList):
            if not info:
                completed_list[i] = True
            else:
                USBServoController.setPosition(self, channel=info[0], val=info[1])    

        # Set up a timer start
        start = time.monotonic()
        # Check the positions until the timeout   
        while not all(completed_list) and (time.monotonic() - start) < timeout:
            
            for i, info in enumerate(infoList):
                # If the position change has not already completed, check the position
                if not completed_list[i]:
                    ret_pos_list[i] = USBServoController.getPositionFromController(self, channel=info[0])
                    # if it's now complete, set the list value to True
                    if ret_pos_list[i] == info[1]:
                        completed_list[i] = True

        if (time.monotonic() - start) > timeout:
                logger.warning("Timeout occured before setPositionMultiSync() function completed")

        if is_threaded:
            self.is_thread_running = False

        return ret_pos_list


    # ------------------------------------------------------------------------------------------------
    
    def setRelativePos (self, channel: int, val: float, units = 2, sync=False):
        """
        """

        new_pos = self.calculateRelativePosition(channel=channel, val=val, units=units)

        if sync:
            USBServoController.setPositionSync(self, channel, new_pos)  
        else:
            USBServoController.setPosition(self, channel, new_pos)   

    
    def setRelativePosMulti (self, infoList: List[Union[Tuple[int, int], None]], units : int = 2, timeout : int = 2, is_threaded = False):
        """
        """

        input_len = len(infoList)
        relative_tuple_list = [None] * input_len

        # For each servo pos combo, calculate the new position and create a replacement tuple
        for i, info in enumerate(infoList):
            channel = info[0]
            pos = self.calculateRelativePosition(channel, info[1], units)
            relative_tuple_list[i] = (channel, pos)

        self.setPositionMultiSync(relative_tuple_list, timeout, is_threaded=is_threaded)

    
    def setRelativePosMultiThreaded (self, infoList:List[Union[Tuple[int, int], None]], units:int = 2, timeout:int = 2):
        """
        """

        if self.is_thread_running:
            logger.error("Attempt to start new thread before prior completion")
            return
        
        thread = Thread(target=self.setRelativePosMulti, 
                        kwargs={"infoList": infoList, "units": units, "timeout": timeout, "is_threaded": True})
        thread.start()
    
    
    # -------------------------------------------------------------------------------    

    def getPosition (self, channel: int) -> int:
        """
            Return the servo position stored in the properties
        """

        return self.servo_props[channel].pos
    
    # -------------------------------------------------------------------------------

    def getPositionFromController(self, channel: int) -> int:
        """
            Get the designated channel's position in microseconds from the controller
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

    def setDisabled (self, channel: int) -> None:
        """
            Disable the servo and store the last position
        """
        
        USBServoController.setPosition(self, channel=channel, val=0)
        self.servo_props[channel].disabled = True
    
    # ---------------------------------------------------------------------------------------

    def setEnabled (self, channel: int) -> None:
        """
            Enable the servo and set a position
        """
        USBServoController.setSpeed(self, channel=channel, val=self.servo_props[channel].speed)
        USBServoController.setPosition (self, channel=channel, val=self.servo_props[channel].pos)
        self.servo_props[channel].disabled = False
        

     # -------------------------------------------------------------------------------------

    def returnToHome (self, channel: int, sync = False, timeout = 2) -> int:
        """
            Return to the defined neutral position
        """
                         
        pos = self.servo_props[channel].home  
        if sync: 
            return USBServoController.setPositionSync(self, channel=channel, val=pos, timeout=timeout)
        else:
            return USBServoController.setPosition(self, channel=channel, val=pos)

    # --------------------------------------------------------------------------------------
    
    def returnToHomeMulti (self, channelList: List[Union[int, None]], timeout = 2, sync = False) -> List[Union[int, None]]:
        """
            Return to the defined Nuetral position for multiple servos
        """
    
        info_list = [None] * len(channelList)

        # Build the parameter list for the call to setPositionMulti
        for i, channel in enumerate(channelList):
            # Set the (channel, pos) Tuple
            if channel is not None:
                info_list[i] = (channel, self.servo_props[channel].home)

        if sync:
            return USBServoController.setPositionMultiSync(self, infoList=info_list, timeout=timeout)
        
        return USBServoController.setPositionMulti(self, infoList=info_list)

    
    # ---------------------------------------------------------------------------------
    
    def calculateRelativePosition (self, channel: int, val: float, units: int) -> int:
        """
            Calculates the new position in microseconds given the desired offset in any unit
        """

        if units == USBServoController.MICROSECONDS:
            diff_ms = int(val)
        elif units == USBServoController.RADIANS:
            diff_ms = int(val * self.servo_props[channel].microseconds_per_radian)
        else:
            diff_ms = int(val * self.servo_props[channel].microseconds_per_degree)

        return self.servo_props[channel].pos + diff_ms  