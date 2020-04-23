#! /usr/bin/python3
#-*-coding: utf-8 -*-

from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import cv2
import imutils
from imutils.video import FPS
import time
from datetime import datetime
import wiringpi as wpi
import os
import tables
import csv
import io
from AHF_Camera.AHF_Camera import AHF_Camera
from picamera import PiCamera
from time import sleep

class AHF_Camera_PiStream(AHF_Camera):

    @staticmethod
    def about():
        return 'uses picamera.PiCamera to run the standard Raspberry Pi camera, recording by frame'

    @staticmethod
    def config_user_get(starterDict = {}):
        defaultFormat = 'hdf5'
        defaultRes =(640,480)
        defaultQuality = 20
        defaultSensorMode = 4
        defaultFrameRate = 30
        defaultISO = 200
        defaultShutterSpeed = 30000
        defaultPath = '/home/Pi/Videos/closed_loop/'
        
        # video path
        video_path = starterDict.get('video_path', defaultPath)
        tempInput = input('Set Video path for recording movies(currently ' + video_path + ') to :')
        if tempInput != '':
            video_path = tempInput
        starterDict.update({'video_path' : video_path})
        # videoFormat
        videoFormat = starterDict.get('format', defaultFormat)
        tempInput = input('Set Video format for recording movies(currently ' + videoFormat + ') to :')
        if tempInput != '':
            videoFormat = tempInput
        starterDict.update({'format' : videoFormat})
        # quality
        quality = starterDict.get('quality', defaultQuality)
        tempInput = input('Set Video quality for h264 movies, best=1, worst =40,0 for auto(currently ' + str(quality) + ') to :')
        if tempInput != '':
            quality = int(tempInput)
        starterDict.update({'quality' : quality})
        # resolution
        resolution = starterDict.get('resolution', defaultRes)
        tempInput = input('set X,Y resolution(currently {0}): '.format(resolution))
        if tempInput != '':
            resolution = tuple(int(x) for x in tempInput.split(','))
        starterDict.update({'resolution' : resolution})
        # framerate
        frameRate = starterDict.get('framerate', defaultFrameRate)
        tempInput = input('Set Frame rate in Hz of recorded movie(currently  {0}): '.format(frameRate))
        if tempInput != '':
            frameRate = float(tempInput)
        starterDict.update({'framerate' : frameRate})
        # ISO
        iso = starterDict.get('iso', defaultISO)
        tempInput = input('Set ISO for video, or 0 to auto set gains(currently ' + str(iso) + ') to :')
        if tempInput != '':
            iso = int(tempInput)
        starterDict.update({'iso' : iso})
        # shutter speed
        shutter_speed = starterDict.get('shutter_speed', defaultShutterSpeed)
        tempInput = input('Set Shutter speed(in microseconds) for recorded video(currently ' + str(shutter_speed) + ') to :')
        if tempInput != '':
            shutter_speed= int(tempInput)
        starterDict.update({'shutter_speed' : shutter_speed})
        # Sensor mode
        sensor_mode = starterDict.get('sensor_mode', defaultSensorMode)
        tempInput = input('Set sensor mode for recording (currently ' + str(sensor_mode) + ') to :')
        if tempInput != '':
            sensor_mode= int(tempInput)
        starterDict.update({'sensor_mode' : sensor_mode})
        # preview window
        previewWin = starterDict.get('previewWin',(0,0,640,480))
        tempInput = input('Set video preview window, left, top, right, bottom,(currently ' + str(previewWin) + ') to :')
        if tempInput != '':
            previewWin = tuple(int(x) for x in tempInput.split(','))
        starterDict.update({'previewWin' : previewWin})
        # white balance
        whiteBalance = starterDict.get('whiteBalance', False)
        tempInput = input('Set white balancing for video, 1 for True, or 0 for False(currently ' + str(whiteBalance) + ') to :')
        if tempInput !='':
            tempInput = bool(int(tempInput))
        starterDict.update({'whiteBalance' : whiteBalance})
        # return already modified dictionary, needed when making a new dictionary
        return starterDict


    def setup(self):
        # Set up text file and paths
        self.data_path = self.settingsDict.get('data_path', '/home/Pi/Videos/closed_loop/')
        # Create pi camera objecy
        try:
            self.piCam = PiCamera()
        except Exception as anError:
            print("Error initializing camera.." + str(anError))
            raise anError
        # set fields in Picamera
        self.piCam.resolution = self.settingsDict.get('resolution',(640, 480))
        self.piCam.framerate = self.settingsDict.get('framerate', 30)
        self.piCam.iso = self.settingsDict.get('iso', 0)
        self.piCam.shutter_speed = self.settingsDict.get('shutter_speed', 30000)
        self.piCam.sensor_mode = self.settingsDict.get('sensor_mode', 4)
        # turn off LED on camera
        self.piCam.led = False

        # set fields that are in AHF_Camera class
        self.AHFvideoFormat = self.settingsDict.get('format', 'hdf5')
        self.AHFvideoQuality = self.settingsDict.get('quality', 20)
        self.AHFframerate= self.settingsDict.get('framerate', 30)
        self.AHFpreview = self.settingsDict.get('previewWin',(0,0,640,480))
        whiteBalance = self.settingsDict.get('whiteBalance', False)
        
        # set gain
        self.cfgDict = self.settingsDict.get('cfgDict', '')
        if 'dff_history' in cfgDict:
            while True:
                if(self.piCam.analopiCg_gain>=7.0 and
                self.piCam.analog_gain<=8.0 and
                self.piCam.digital_gain>=1 and
                self.piCam.digital_gain<=1.5):
                    self.piCam.exposure_mode='off'
                    print("ok")
                    break
                else:
                    print('analog gain: ' + str(eval(str(self.piCam.analog_gain))))
                    print('digital gain: ' + str(eval(str(self.piCam.digital_gain))))


        self.is_recording = False
        self.stopped = False
        self.rawCapture = PiRGBArray(self.piCam, size=self.resolution())

        # Allow the camera to warmup
        time.sleep(0.1)
        print("done initializing!")
        return

    def resolution(self):
        return self.piCam.resolution

    def setdown(self):
        """
        Writes session end and closes log file
        """
        self.piCam.close()
        pass


    def update(self, path, type, video_port =False):
        if self.data_path:
            self.camera.start_recording(self.data_path, format='rgb')
        for f in self.stream:
            start = time.time()
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.seek(0)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                if self.data_path:
                    self.camera.stop_recording()
                self.rawCapture.close()
                self.piCam.close()
                return
            time.sleep(max(0.5/(self.piCam.framerate) - (time.time() - start), 0.0))
        

    def start_recording(self, video_name_path):
        """
        """
        self.start_preview()
        self.is_recording = True
        self.frame = None
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def start_preview(self):
        self.piCam.start_preview(fullscreen = False, window= self.AHFpreview)

    def stop_preview(self):
        self.piCam.stop_preview()

    def stop_recording(self):
        """
        Stops a video recording previously started with start_recording.
        """
        if self.is_recording:
            self.stopped = False
        return

    def hardwareTest(self):
        """
        Tests functionality, gives user a chance to change settings
        """
        self.setup()
        while(True):
            inputStr = input('p=display preview, r=record for 10 seconds, t= edit task settings, q= quit: ')
            if inputStr == 'p':
                print('Now displaying current output')
                self.piCam.start_preview(fullscreen = False, window=self.AHFpreview)
                result = input('Press any key to stop')
                self.piCam.stop_preview()
            elif inputStr == 'r':
                print("Starting recording for 10 seconds")
                self.start_recording(video_name_path = '')
                time.sleep(10)
                self.stop_recording()
                print("Video is saved in current directory")
            elif inputStr == 't':
                self.setdown()
                self.settingsDict = self.config_user_get(self.settingsDict)
                self.setup()
            elif inputStr == 'q':
                break
        pass


