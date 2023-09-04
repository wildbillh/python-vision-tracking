#!/usr/bin/bash
#../bin/opencv_createsamples.exe -info pos.txt -w 24 -h 24 -num 1000 -vec pos.vec
#../bin/opencv_traincascade.exe -data cascade/ -vec pos.vec -bg neg.txt -w 24 -h 24 -numPos 260 -numNeg 400 -numStages 20 -maxFalseAlarmRate 0.3 -minHitRate 0.999 -mode ALL -bt LB -acceptanceRatioBreakValue 0.00002 -precalcValBufSize 2048 -precalcIdxBufSize 2048
# fr-trans2: 651 frames, 208 no hits, 467 total hits
# good-jump: 660 frames, 134 no hits, 826 total hits


# --------------------------------------------------------------------------------------------
# Increase w and h from 24 to 32
#../bin/opencv_createsamples.exe -info pos.txt -w 32 -h 32 -num 1000 -vec pos.vec
#../bin/opencv_traincascade.exe -data cascade/ -vec pos.vec -bg neg.txt -w 32 -h 32 -numPos 260 -numNeg 400 -numStages 20 -maxFalseAlarmRate 0.3 -minHitRate 0.999 -mode ALL -bt LB -acceptanceRatioBreakValue 0.00002 -precalcValBufSize 2048 -precalcIdxBufSize 2048
#fr-trans2 76 no hits, 910 total
# good-jump: 660 frames, 11 no hits, 1705 total hits
#Training until now has taken 0 days 1 hours 1 minutes 32 seconds.

# --------------------------------------------------------------------------------------------
# Increase w and h from 32 to 48
#../bin/opencv_createsamples.exe -info pos.txt -w 48 -h 48 -num 1000 -vec pos.vec
../bin/opencv_traincascade.exe -data cascade/ -vec pos.vec -bg neg.txt -w 48 -h 48 -numPos 260 -numNeg 400 -numStages 11 -maxFalseAlarmRate 0.3 -minHitRate 0.999 -mode ALL -bt LB -acceptanceRatioBreakValue 0.00002 -precalcValBufSize 2048 -precalcIdxBufSize 2048
# 
