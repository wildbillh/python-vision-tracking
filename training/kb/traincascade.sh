#!/usr/bin/bash
#../bin/opencv_createsamples.exe -info pos.txt -w 24 -h 24 -num 1000 -vec pos.vec
../bin/opencv_traincascade.exe -data cascade/ -vec pos.vec -bg neg.txt -w 24 -h 24 -numPos 200 -numNeg 400 -numStages 20 -maxFalseAlarmRate 0.3 -minHitRate 0.999 -mode ALL -bt LB -acceptanceRatioBreakValue 0.00002 -precalcValBufSize 2048 -precalcIdxBufSize 2048