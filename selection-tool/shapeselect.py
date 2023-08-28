# Write Python code here
# import the necessary packages
import cv2
import argparse
import numpy as np

# now let's initialize the list of reference point
ref_point = []
crop = False

def shape_selection(event, x, y, flags, param):
	# grab references to the global variables
	global ref_point, crop

	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates and indicate that cropping is being performed
	if event == cv2.EVENT_LBUTTONDOWN:
		ref_point = [(x, y)]

	# check to see if the left mouse button was released
	elif event == cv2.EVENT_LBUTTONUP:
		# record the ending (x, y) coordinates and indicate that
		# the cropping operation is finished
		ref_point.append((x, y))

		# draw a rectangle around the region of interest
		#cv2.rectangle(image, ref_point[0], ref_point[1], (0, 255, 0), 2)
		print (ref_point[0], ref_point[1], flush=True)
		cv2.imshow("image", removeROI(image, (ref_point[0], ref_point[1])))


def removeROI (frame: np.ndarray, rectangle):

	((x1, y1), (x2, y2)) = rectangle
	print(x1,y1,x2,y2, flush=True)
	xdiff = x2-x1
	frame_copy = frame.copy()
	frame_copy[y1:y2, x1:x2, 0:3] = frame[y1:y2, x1-xdiff:x1, 0:3]
	return frame_copy


# load the image, clone it, and setup the mouse callback function
image = cv2.imread("81.jpg")
print(image.shape, image.dtype, flush=True)
clone = image.copy()
cv2.namedWindow("image")
cv2.setMouseCallback("image", shape_selection)




# keep looping until the 'q' key is pressed
while True:
	
	# display the image and wait for a keypress
	cv2.imshow("image", image)
	key = cv2.waitKey(0) & 0xFF

	# press 'r' to reset the window
	if key == ord("r"):
		image = clone.copy()

	# if the 'c' key is pressed, break from the loop
	elif key == ord("q"):
		break



# close all open windows
cv2.destroyAllWindows()
