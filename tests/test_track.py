import array, copy, numpy as np, unittest
from app.dependencies.roitracking import TrackData, Track, ROITracking

class TrackDataTest (unittest.TestCase):

    def test_constructor_and_euality(self):

        # Test the empty track
        trackData = TrackData()
        self.assertTrue(trackData.isEmpty())
        self.assertEqual(trackData.gray_hist.all(), TrackData.generateEmptyHistogram().all())
        self.assertEqual(trackData.hsv_hist.all(), TrackData.generateEmptyHistogram(isGrayScale=False).all())
        self.assertEqual(trackData.level, np.float32(0.0))
        self.assertIsNone(trackData.pos)

        # Test the == operator
        self.assertNotEqual(trackData, 1)
        
        # Get a class that differs by pos only
        trackDataFull = TrackData(pos=(2,2))
        self.assertNotEqual(trackData, trackDataFull)

        # Make the 2 equal
        trackData.pos = (2,2)
        self.assertEqual(trackData, trackDataFull)

        # only gray_hist is different
        trackDataFull.gray_hist = np.full((256,1), 2.5, dtype = np.float32)
        self.assertNotEqual(trackData, trackDataFull)

        # Set where only hsv_hist is different
        trackDataFull.gray_hist = TrackData.generateEmptyHistogram()
        trackDataFull.hsv_hist = np.full((128,256), 2, dtype = np.float32)
        self.assertNotEqual(trackData, trackDataFull)

        # change level
        trackDataFull.hsv_hist = TrackData.generateEmptyHistogram(isGrayScale=False)
        trackDataFull.level = np.float32(1.115)
        self.assertNotEqual(trackData, trackDataFull)

# ==================================================================================

class TrackTest (unittest.TestCase):

    def test_constructor (self):

        track = Track(historyCount=15)
        self.assertEqual(len(track.history), 15)
        first_track: TrackData = track.history[0]
        self.assertEqual(first_track.gray_hist.shape, (256, 1))
        self.assertEqual(first_track.hsv_hist.shape, (180, 256))
        self.assertEqual(first_track.level, np.float32(0.0))
        self.assertIsNone(first_track.pos)
        
    
    # -----------------------------------------------------------------
    
    def test_add_tracks (self):

        track = Track(historyCount=1)
        # addTrack with no parms should add empty track
        track.addTrack()
        np.array_equal(track.history[0].gray_hist, TrackData.generateEmptyHistogram())
        self.assertTrue(track.isEmpty())

        gray_hist_1 = np.full((256, 1), 4.0, dtype=np.float32)
        gray_hist_2 = np.full((256, 1), 8.0, dtype=np.float32)

        hsv_hist_1 = np.full((180, 256), 4.0, dtype=np.float32)
        hsv_hist_2 = np.full((180, 256), 8.0, dtype=np.float32)

        # Create track record and test that it's empty
        track = Track(historyCount=2) 
        self.assertTrue(track.isEmpty()) 

        data1 = TrackData(grayHist=gray_hist_1, hsvHist=hsv_hist_1, 
                                 level=np.float32(3.45), pos=(0,0))
        
        # Add a non empty hist and level and test
        track.addTrack(copy.copy(data1))
        track_item: TrackData = track.getByIndex(0) 
        self.assertEqual(track_item, data1)  
        
        
        # Add an empty track and test 
        track.addTrack(TrackData())
        track_item: TrackData = track.getByIndex(0) 
        self.assertTrue(track_item.isEmpty())
        
        # Test that the latest histogram returned is index 1
        self.assertEqual(track.getLatestHistogram()[0], 1)
        
        # Add a nonempty record
        data2 = TrackData(grayHist=gray_hist_2, hsvHist=hsv_hist_2, level=8.0, pos=(1,1))
        track.addTrack (copy.copy(data2))

        # Now the first record should be 8.0's and the second record shoud be empty
        track_item = track.getByIndex(0)
        self.assertEqual(track_item, data2)
        self.assertEqual(track.getLatestHistogram()[0], 0)

        track_item = track.getByIndex(1)
        self.assertTrue(track_item.isEmpty())

    # --------------------------------------------------------------------------------
    
    def test_get_level_sums (self):


        track = Track(historyCount=2)
        track.addTrack(TrackData(level=2.0))
        track.addTrack(TrackData(level=2.5))
        self.assertEqual(track.getLevelSums(), np.float32(4.5))

        