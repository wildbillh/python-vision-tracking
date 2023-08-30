
import cv2
import numpy as np
from typing import Tuple
from app.dependencies.videoshow import SelectionVideoShow
from app.dependencies.utils import removeROIs

# Exercise the SelectionVideoShow class 

def main():
    
	props = {"windowName": "frame"}
	vs = SelectionVideoShow(props = props, interimProcessFunc = removeROIs)
	#vs = SelectionVideoShow(props=props)
	
	image = cv2.imread("selection-tool/81.jpg")
	print("returns", vs.show(image, processFunc=removeROIs)[1], flush=True)
	cv2.destroyWindow(props["windowName"])


main()