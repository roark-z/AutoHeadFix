#! /usr/bin/python
# -*-coding: utf-8 -*

from abc import ABCMeta, abstractmethod
from time import time, sleep
from AHF_Base import AHF_Base
from os import chown
from pwd import getpwnam
from grp import getgrnam


class AHF_Stimulator(AHF_Base, metaclass = ABCMeta):
    """
    Stimulator does all stimulation and reward during a head fix task.
    All events and their timings in a head fix, including camera control and rewards, are controlled by a Stimulator.
    """
    @staticmethod
    def config_user_get(starterDict = {}):
        return starterDict
 
    @abstractmethod
    def run(self, level = 0, resultsDict = {}, settingsDict = {}):
        """
        Called at start of each head fix. Does whatever
        """
        self.running = True
        pass

    @abstractmethod
    def quitting(self):
        self.running = False

    def stop(self):
        self.running = False

    def startVideo(self):
        if not self.task.Stimulus.__class__.__name__ == 'AHF_Stimulus_Laser':
            try:
                thisTag = self.task.tag
                self.videoTag = thisTag
                camera = self.task.Camera
                #TODO IMPROVE
                if camera.AHFvideoFormat == 'rgb':
                    extension = 'raw'
                else:
                    extension = 'h264'
                self.lastTime =  time()
                print(hex(id(self)), 'start')
                print(self.lastTime)
                self.video_name=str(thisTag)+'_'+str(int(self.lastTime))+'.'+extension
                video_name_path = "M" + self.video_name
                #writeToLogFile(expSettings.logFP, thisMouse, "video:" + video_name)
                # send socket message to start behavioural camera
                self.task.DataLogger.writeToLogFile(thisTag, 'VideoStart', {'name': self.video_name}, time())
                if hasattr(self.task, 'Trigger'):
                    #MESSAGE = str(thisMouse.tag) + "_" + stimStr + "_" + '%d' % headFixTime
                    MESSAGE = str(thisTag) + "_" +  "_" + '%d' % self.task.lastFixedTime
                    self.task.Trigger.doTrigger(MESSAGE)
                    # start recording and Turn on the blue led
                    camera.start_recording(video_name_path)
                    sleep(self.task.Trigger.cameraStartDelay) # wait a bit so camera has time to start before light turns on, for synchrony accross cameras
                    self.task.BrainLight.onForStim()
                    self.task.DataLogger.writeToLogFile(thisTag, 'BrainLEDON', None, time())
                else: # turn on the blue light and start the movie
                    self.task.BrainLight.onForStim()
                    self.task.DataLogger.writeToLogFile(thisTag, 'BrainLEDON', None, time())
                    camera.start_recording(video_name_path)
            except Exception as anError:
                camera.stop_recording()
                print('Error in running trial:' + str(anError))
                raise anError
        else:
            print('Camera used by laser stimulus, no recording')

    def stopVideo(self):
        if self.task.Stimulus.__class__.__name__ == 'AHF_Stimulous_Laser':
            return
        if hasattr(self, 'videoTag'):
            thisTag = self.videoTag
        else:
            thisTag = self.task.tag
        camera = self.task.Camera
        #TODO IMPROVE
        if camera.AHFvideoFormat == 'rgb':
            extension = 'raw'
        else:
            extension = 'h264'
        print(hex(id(self)), 'stop')
        if self.lastTime is None:
            print("no last")
            return 
        video_name_path = "M" + self.video_name
        if hasattr(self.task, 'Trigger'):
            self.task.BrainLight.offForStim() # turn off the blue LED
            self.task.DataLogger.writeToLogFile(thisTag, 'BrainLEDOFF', None, time())
            sleep(self.task.Trigger.cameraStartDelay) #wait again after turning off LED before stopping camera, for synchronization
            self.task.Trigger.doTrigger("Stop") # stop
            camera.stop_recording()
        else:
            camera.stop_recording()
            self.task.BrainLight.offForStim() # turn off the blue LED
            self.task.DataLogger.writeToLogFile(thisTag, 'BrainLEDOFF', None, time())
        print("turned off")
        self.task.DataLogger.writeToLogFile(thisTag, 'VideoEnd', None, time())
        uid = getpwnam('pi').pw_uid
        gid = getgrnam('pi').gr_gid
        self.lastTime = None
        #chown(video_name_path, uid, gid) # we run AutoheadFix as root if using pi PWM, so we expicitly set ownership to pi
