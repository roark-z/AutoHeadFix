#AHF-specific moudules
from AHF_Stimulator.AHF_Stimulator import AHF_Stimulator

#Closed loop stimulator modules
import numpy as np
import sys
import matplotlib.pyplot as plt
from PTPWM import PTPWM
from array import array
from queue import Queue as queue
from threading import Thread
from multiprocessing import Process, Queue
from time import sleep, time
from random import random
from datetime import datetime
from itertools import combinations,product
import warnings

import cv2
import imutils
import wiringpi as wpi
import os
import tables
import csv


class AHF_Stimulator_ClosedLoop(AHF_Stimulator):
    """

    """
    self.defaultSummaryFile = 'expt_summary.csv'
    self.defaultAudioPin = -1
    self.defaultNumTones = 10
    self.defaultRewardThreshold = 50
    self.defaultSessionDuration = 2
    self.defaultMOGHistory = 15
    self.defaultVarThreshold = 3


    @staticmethod
    def about():
        return 'Closed loop experiment. Rewards given based if brain activity goes above threshold in ROI'


    @staticmethod
    def config_user_get(starterDict = {}):
        # Summary file name
        summary_file_name = starterDict.get('summary_file_name', self.defaultSummaryFile)
        temp = input('Enter the name of the summary csv file, currently %d: ', % summary_file_name)
        if temp != '':
            summary_file_name = temp
        starterDict.update({'summary_file_name' : summary_file_name})
        # Audio pin
        audio_pin = starterDict.get('audio_pin', self.defaultAudioPin)
        temp = input('Enter the pin for audio tone generation, -1 for output to terminal only, currently %d: ', % audio_pin)
        if temp != '':
            audio_pin = int(temp)
        started.update({'audio_pin', audio_pin})
        # Number of tones
        num_tones = starterDict.get('num_tones', self.defaultNumTones)
        temp = input('Enter the number of tones for audio tone generation, currently %d', % num_tones)
        if temp != '':
            num_tones = int(temp) 
        starterDict.update({'num_tones', num_tones})
        # More configs here

        return AHF_Stimulator.config_user_get(starterDict)


    def setup(self):
        # super() sets up all the laser stuff plus self.headFixTime plus # rewards(not used here)
        super().setup()
        self.summary_file_name = starterDict.get('summary_file_name', self.defaultSummaryFile)
        self.audio_pin=int(self.settingsDict.get('audio_pin', self.defaultAudioPin))
        self.num_tones=int(self.settingsDict.get('num_tones', self.defaultNumTones))
        self.moghistory = self.defaultMOGHistory
        self.var_threshold = self.defaultVarThreshold

        # Closed-loop specific settings
        # Starting audio pin
        wpi.wiringPiSetupGpio()
        wpi.softToneCreate(self.audio_pin)
        # Compute frequency
        self.freq_dict = _get_freqs(self.num_tones)

        # General AHF attributes
        self.rewarder = self.task.Rewarder
        self.camera = self.task.Camera
        self.task.DataLogger.startTracking("Outcome", "code", "buffer", 200)


    def quitting(self):
        """
            Called before AutoHEadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        self.task.Camera.stop_recording()
        pass

    #=================Main functions called from outside===========================
    def run(self, level = -1, resultsDict = {}, settingsDict = {}, tag = 0):
        super().run()
        super().startVideo()
        self.tag = self.task.tag
        print('tag number...')
        print(str(self.tag))

        if not tag == 0:
            print('dummy tag used')
            self.tag = tag
        else: 
            if self.tag <= 0:
                print(str(self.tag))
                super().stopVideo()
                return
        
        run_threads = True
        runSession = True
        runPreview = True
        runRecording = True

        fgbg = cv2.createBackgroundSubtractorMOG2(mogHistory, varThreshold, False)
        cvui.init('closed_loop ROI selection')


    def setdown(self):
        print('Withhold stimulator set down')


    def hardwareTest(self):
        # TODO: Test this
        self.setup()
        while(True):
            inputStr = input('q= quit: ')
            if inputStr == 'q':
                break
        pass


    def _get_freqs(nTones):
        # quarter-octave increment factor
        qo = 2 ** (1 / 4)
        # initial audio frequency
        freqs = [1000]
        freqDict = {}
        
        #import pdb; pdb.set_trace()
        for i in range(1, nTones):
            binSize = int(100 / nTones)
            freq = freqs[-1] * qo

            freqDict.update({i: freq for i in range(binSize * (i - 1), 101)})
            freqs.append(freq)

        return freqDict