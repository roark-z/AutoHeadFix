#AHF-specific moudules

from AHF_Stimulator_Rewards import AHF_Stimulator_Rewards
from AHF_Stimulator import AHF_Stimulator
from PTSimpleGPIO import PTSimpleGPIO, Infinite_train, Train
from random import random
import RPi.GPIO as GPIO

#Laser-stimulator modules
import numpy as np
import sys
# import matplotlib.pyplot as plt
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


class AHF_Stimulator_LickWithhold(AHF_Stimulator):
    """
    | AHF_Stimulator_LickWithhold gives mice rewards based on their "level"
    | within the program. These rewards are given based on the mouse's response
    | to a defined stimulus. Levels are as follows:

    | Level 0: Mouse gets periodic rewards paired with a stimulus. No input
    | required from the mouse at this stage.
    | Level 1: Mouse gets periodic rewards, again paired with a stimulus. The
    | mouse must refrain from licking for a defined withhold time before another
    | reward is given. If they lick within the withhold time, a buzzer sounds.
    | Level 2: Mouse must lick after a given delay time from the stimulus, and
    | within a defined response time, in order to receive a reward. In brief,
    | this is the "GO" task.
    | Level 3: Mouse must differentiate between two stimuluses, either one pulse
    | for "GO" or two successive pulses for "NO-GO". In either case, they must
    | wait for the delay time before responding, and then within the response
    | time decide to either lick or not lick. "NO-GO" trials can be rewarded
    | with water or not if desired.
    | For levels 2 and 3, the outcome of the task is recorded as follows:
    | "GO":
    | -4: licked within delay time, failure
    | -2: did not lick, failure
    | +2: waited until response time to lick and then licked, success
    | "NO-GO":
    | -3: licked within delay time, failure
    | -1: waited until response time to lick and then licked, failure
    | +1: did not lick, success
    """

    #### default definitions for stimulator configuration that are not defined in superclass
    lickWithholdTime_def = 1  # how long mouse has to go for without licking before getting rewarded
    delayTime_def = 0.5     # laser pulse is this may seconds before reward is given
    responseTime_def = 2.5
    ##### speaker feedback GPIO definitions #######
    speakerPin_def = 25      # GPIO pin used to drive piezo speaker for negative feedback
    speakerFreq_def = 300    # frequency to drive the speaker
    speakerDuty_def = 0.8    # duty cycle to drive speaker, unbalanced duty cycle gives nasty harmonics
    speakerOffForReward_def = 1.5   #time for consuming reward without getting buzzed at
    lickWrongTimeout_def = 5
    rewardNoGo_def = True
    goLikelihood_def = 0.5

    @staticmethod
    def about():
        return 'LickWithhold provides stimuli, and mouse must interact depending upon level.'


    @staticmethod
    def config_user_get(starterDict = {}):
        speakerPin = starterDict.get('speakerPin', AHF_Stimulator_LickWithhold.speakerPin_def)
        tempInput = input('Set speaker pin(currently {0}): '.format(speakerPin))
        if tempInput != '':
            speakerPin = int(tempInput)
        starterDict.update({'speakerPin' : speakerPin})
        speakerFreq = starterDict.get('speakerFreq', AHF_Stimulator_LickWithhold.speakerFreq_def)
        tempInput = input('Set speaker frequency(currently {0}): '.format(speakerFreq))
        if tempInput != '':
            speakerFreq = int(tempInput)
        starterDict.update({'speakerFreq' : speakerFreq})
        speakerDuty = starterDict.get('speakerDuty', AHF_Stimulator_LickWithhold.speakerDuty_def)
        tempInput = input('Set speaker duty cycle(currently {0}): '.format(speakerDuty))
        if tempInput != '':
            speakerDuty = float(tempInput)
        starterDict.update({'speakerDuty' : speakerDuty})
        speakerOffForReward = starterDict.get('speakerOffForReward', AHF_Stimulator_LickWithhold.speakerOffForReward_def)
        tempInput = input('Set time to have speaker off while rewarding(currently {0}): '.format(speakerOffForReward))
        if tempInput != '':
            speakerOffForReward = int(tempInput)
        starterDict.update({'speakerOffForReward' : speakerOffForReward})
        lickWrongTimeout = starterDict.get('lickWrongTimeout', AHF_Stimulator_LickWithhold.lickWrongTimeout_def)
        tempInput = input('Set timeout for wrong answer(currently {0}): '.format(lickWrongTimeout))
        if tempInput != '':
            lickWrongTimeout = int(tempInput)
        starterDict.update({'lickWrongTimeout' : lickWrongTimeout})
        defaultLevel = starterDict.get('defaultLevel', 0)
        tempInput = input('Set default level for mouse(currently {0}): '.format(defaultLevel))
        if tempInput != '':
            defaultLevel = int(tempInput)
        starterDict.update({'defaultLevel' : defaultLevel})

        return AHF_Stimulator_Rewards.config_user_get(starterDict)

    def config_user_subject_get(self,starterDict = {}):
        mouseLevel = starterDict.get('mouseLevel', 0)
        tempInput = input('Set default level for mouse(currently {0}): '.format(mouseLevel))
        if tempInput != '':
            mouseLevel = int(tempInput)
        starterDict.update({'mouseLevel' : mouseLevel})
        lickWithholdTime = starterDict.get('lickWithholdTime', AHF_Stimulator_LickWithhold.lickWithholdTime_def)
        tempInput = input('Set lick withhold time(currently {0}): '.format(lickWithholdTime))
        if tempInput != '':
            lickWithholdTime = float(tempInput)
        starterDict.update({'lickWithholdTime' : lickWithholdTime})
        delayTime = starterDict.get('delayTime',AHF_Stimulator_LickWithhold.delayTime_def)
        tempInput = input('Set delay time, currently {0}: '.format(delayTime))
        if tempInput != '':
            delayTime = float(tempInput)
        starterDict.update({'delayTime' : delayTime})
        responseTime = starterDict.get('responseTime',AHF_Stimulator_LickWithhold.responseTime_def)
        tempInput = input('Set response time,  currently {0}: '.format(responseTime))
        if tempInput != '':
            responseTime = float(tempInput)
        starterDict.update({'responseTime' : responseTime})
        rewardNoGo = starterDict.get('rewardNoGo',AHF_Stimulator_LickWithhold.rewardNoGo_def)
        tempInput = input('Reward No-Go Trials?(Y/N), currently {0}): '.format(rewardNoGo))
        if str(tempInput).lower() != 'y':
            rewardNoGo = False
        starterDict.update({'rewardNoGo' : rewardNoGo})
        goLikelihood = starterDict.get('goLikelihood',AHF_Stimulator_LickWithhold.goLikelihood_def)
        tempInput = input('Set Go/No-Go ratio between 0 and 1 (0 is full No-Go) currently {0}): '.format(goLikelihood))
        if tempInput != '':
            goLikelihood = float(tempInput)
        starterDict.update({'goLikelihood' : goLikelihood})
        return AHF_Stimulator_Rewards.config_user_subject_get(self, starterDict)

    def config_subject_get(self, starterDict={}):
        mouseLevel = starterDict.get('mouseLevel', 0)
        starterDict.update({'mouseLevel' : mouseLevel})
        lickWithholdTime = starterDict.get('lickWithholdTime', AHF_Stimulator_LickWithhold.lickWithholdTime_def)
        starterDict.update({'lickWithholdTime' : lickWithholdTime})
        delayTime = starterDict.get('delayTime',AHF_Stimulator_LickWithhold.delayTime_def)
        starterDict.update({'delayTime' : delayTime})
        responseTime = starterDict.get('responseTime',AHF_Stimulator_LickWithhold.responseTime_def)
        starterDict.update({'responseTime' : responseTime})
        rewardNoGo = starterDict.get('rewardNoGo',AHF_Stimulator_LickWithhold.rewardNoGo_def)
        starterDict.update({'rewardNoGo' : rewardNoGo})
        goLikelihood = starterDict.get('goLikelihood',AHF_Stimulator_LickWithhold.goLikelihood_def)
        starterDict.update({'goLikelihood' : goLikelihood})
        return AHF_Stimulator_Rewards.config_subject_get(self, starterDict)

    def setup(self):
        # super() sets up all the laser stuff plus self.headFixTime plus # rewards(not used here)
        super().setup()
        #Lick-withhold settings
        # setting up speaker for negative feedback for licking
        self.speakerPin=int(self.settingsDict.get('speakerPin', self.speakerPin_def))
        self.speakerFreq=float(self.settingsDict.get('speakerFreq', self.speakerFreq_def))
        self.speakerDuty = float(self.settingsDict.get('speakerDuty', self.speakerDuty_def))
        self.speakerOffForReward = float(self.settingsDict.get('speakerOffForReward', self.speakerOffForReward_def))
        self.lickWrongTimeout = float(self.settingsDict.get('lickWrongTimeout', self.lickWrongTimeout_def))
        self.defaultLevel = int(self.settingsDict.get('defaultLevel', 0))
        self.speaker=Infinite_train(PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
        self.nRewards = self.settingsDict.get('nRewards')
        self.rewardInterval = self.settingsDict.get('rewardInterval')
        self.rewarder = self.task.Rewarder
        self.camera = self.task.Camera
        #Mouse scores
        self.lickWithholdTimes = []
        self.rewardTimes = []
        self.laserTimes = []
        self.task.DataLogger.startTracking("Outcome", "code", "buffer", 200)

    def quitting(self):
        """
            Called before AutoHEadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        # self.task.Camera.stop_recording()
        pass

    def rewardTask(self):
        self.task.Stimulus.stimulate()
        self.task.DataLogger.writeToLogFile(self.tag, 'Stimulus', None, time())
        # sleep for lead time, then give reward
        sleep(self.mouse.get("Stimulator").get("delayTime"))
        self.rewardTimes.append(time())
        self.rewarder.giveReward('task')
        if self.speakerIsOn == True:
            print("turn off")
            self.speaker.stop_train()
            self.speakerIsOn = False


    def withholdWait(self, endTime):
        # self.lickWithholdRandom = self.mouse.get("Stimulator").get("lickWithholdTime") +(0.5 - random())
        self.lickWithholdRandom = self.mouse.get("Stimulator").get("lickWithholdTime")
        lickWithholdEnd = time() + self.lickWithholdRandom
        self.task.LickDetector.startLickCount()
        anyLicks = 0

        print("starting withhold time:", self.lickWithholdRandom, "seconds")

        while time() < lickWithholdEnd and time() < endTime:
            sleep(0.2)
            for x in self.task.LickDetector.getLickCount():
                anyLicks += x[1]
            if anyLicks == 0:
                if self.speakerIsOn == True:
                    self.speaker.stop_train()
                    self.speakerIsOn = False
            else: # there were licks in withholding period
                if(self.speakerIsOn == False) and(time() > self.OffForRewardEnd):
                    print("Speaker on (licked during withhold time)")
                    self.speaker.start_train()
                    self.speakerIsOn = True
                # self.lickWithholdRandom = self.mouse.get("Stimulator").get("lickWithholdTime") +(0.5 - random())
                self.lickWithholdRandom = self.mouse.get("Stimulator").get("lickWithholdTime")
                lickWithholdEnd = time() + self.lickWithholdRandom
                print("incrementing withhold time:", self.lickWithholdRandom, "seconds")
                self.task.LickDetector.startLickCount()
                anyLicks = 0
                
        print("withhold time finished")
        return anyLicks

    def goTask(self):
        """
        A GO trial. Mouse must lick before getting a reward.
        """
        print("Starting GO task")
        self.task.Stimulus.stimulate(400) # default freq 300
        sleep(0.001)
        self.task.Stimulus.stimulate(400)
        self.task.DataLogger.writeToLogFile(self.tag, 'Stimulus', {'trial': "GO"}, time())
        delayEnd = time() + self.mouse.get("Stimulator").get("delayTime")
        self.task.LickDetector.startLickCount()
        anyLicks = 0
        badLickFlag = 0

        print("starting delay time:", self.mouse.get("Stimulator").get("delayTime"), "seconds")
        
        #Mouse is not supposed to lick during withhold period
        while time() < delayEnd:
            sleep(0.2)
            for x in self.task.LickDetector.getLickCount():
                anyLicks += x[1]
            if anyLicks > 0:
                badLickFlag = 1
                print("Speaker on (licked during withhold period)")
                self.speaker=Infinite_train(PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
                self.speaker.start_train()
                self.speakerIsOn = True
                self.task.DataLogger.writeToLogFile(self.tag, 'Outcome', {'code': -4, 'withholdTime': self.lickWithholdRandom}, time())
                # The mouse is kept in withhold loop if it licked
                # print("incrementing delay time time:", self.mouse.get("Stimulator").get("delayTime"), "seconds")
                # delayEnd = time() + self.mouse.get("Stimulator").get("delayTime")
                # self.task.LickDetector.startLickCount()
                # anyLicks = 0
                return
            elif self.speakerIsOn:
                self.speaker.stop_train()
                self.speakerIsOn = False

        # If mouse licked during waiting period, the action does not count
        if badLickFlag > 0:
            print("Mouse licked during delayTime period, returning")
            return
        
        print("delayTime period ended, mouse should GO now")

        # Detect mouse licking after withhold period is over
        responseEnd = self.mouse.get("Stimulator").get("responseTime") + time()
        self.task.LickDetector.startLickCount()
        anyLicks = 0
        lastLicks = 0
        while time() < responseEnd:
            sleep(0.2)
            for x in self.task.LickDetector.getLickCount():
                anyLicks += x[1]
            if anyLicks > 0:
                print("Mouse licked during GO task YAY")
                self.task.DataLogger.writeToLogFile(self.tag, 'Outcome', {'code': 2, 'withholdTime': self.lickWithholdRandom}, time())
                #sleep(max(0, responseEnd - time()))
                lastLicks = anyLicks
                anyLicks = 0
                self.task.LickDetector.startLickCount()

        # Give reward or timeout based on mouse behaviour
        if lastLicks is not 0:
            self.rewardTimes.append(time())
            self.rewarder.giveReward('task')
        else:
            # Wrong, mouse gets a timeout :(
            print("Mouse did not lick during GO task BAD")
            self.task.DataLogger.writeToLogFile(self.tag, 'Outcome', {'code': -2, 'withholdTime': self.lickWithholdRandom}, time())
            sleep(self.lickWrongTimeout)


    def noGoTask(self):
        print("Starting NO GO task")
        # Double buzz indicates no-go task
        self.task.Stimulus.stimulate(100) # lower freq
        sleep(0.1)
        self.task.Stimulus.stimulate(100)
        self.task.DataLogger.writeToLogFile(self.tag, 'Stimulus', {'trial': "NO-GO"}, time())
        delayEnd = time() + self.mouse.get("Stimulator").get("delayTime")
        self.task.LickDetector.startLickCount()
        anyLicks = 0
        badLickFlag = 0

        # Mouse is not supposed to lick within withhold period
        while time() < delayEnd:
            sleep(0.2)
            for x in self.task.LickDetector.getLickCount():
                anyLicks += x[1]
            if anyLicks > 0:
                badLickFlag = 1
                print("Speaker on (licked during withhold period)")
                self.speaker=Infinite_train(PTSimpleGPIO.MODE_FREQ, self.speakerPin, self.speakerFreq+300, self.speakerDuty,  PTSimpleGPIO.ACC_MODE_SLEEPS_AND_SPINS)
                self.speaker.start_train()
                self.speakerIsOn = True
                self.task.DataLogger.writeToLogFile(self.tag, 'Outcome', {'code': -3, 'withholdTime': self.lickWithholdRandom}, time())
                # # The mouse is kept in withhold loop if it licked
                # delayEnd = time() + self.mouse.get("Stimulator").get("delayTime")
                # self.task.LickDetector.startLickCount()
                # anyLicks = 0
                return
            elif self.speakerIsOn:
                self.speaker.stop_train()
                # self.speakerIsOn = False

        if badLickFlag > 0:
            return

        # Mouse is not supposed to lick within response time either (no-go trial)
        responseEnd = self.mouse.get("Stimulator").get("responseTime") + time()
        self.task.LickDetector.startLickCount()
        anyLicks = 0
        lastLicks = 0
        while time() < responseEnd:
            sleep(0.2)
            for x in self.task.LickDetector.getLickCount():
                anyLicks += x[1]
            if anyLicks > 0:
                print("Speaker on (mouse not supposed to lick in NO GO task) BAD")
                self.task.DataLogger.writeToLogFile(self.tag, 'Outcome', {'code': -1, 'withholdTime': self.lickWithholdRandom}, time())
                lastLicks = anyLicks
                self.speaker.start_train()
                self.speakerIsOn = True
                self.task.LickDetector.startLickCount()
                anyLicks = 0
            elif self.speakerIsOn:
                self.speaker.stop_train()
                self.speakerIsOn = False

        # Mouse rewarded for NO GO task
        if lastLicks == 0:
            print("Mouse did not lick during NO GO trial YAY")
            if self.mouse.get("Stimulator").get("rewardNoGo"):
                self.rewardTimes.append(time())
                self.rewarder.giveReward('task')
            self.task.DataLogger.writeToLogFile(self.tag, 'Outcome', {'code': 1, 'withholdTime': self.lickWithholdRandom}, time())
        else:
            # Wrong, mouse gets a timeout :(
            sleep(self.lickWrongTimeout)
        pass



    def discrimTask(self):
        rand = random()
        print(str(rand))
        print("go likelihood:", self.mouse.get("Stimulator").get("goLikelihood"))

        if rand < self.mouse.get("Stimulator").get("goLikelihood"):
            #GO
            print('G/N: Mouse should perform GO task')
            self.goTask()
        else:
            #NO GO
            print('G/N: Mouse should perform NO GO task')
            self.noGoTask()
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

        self.mouse = self.task.Subjects.get(self.tag)
        if level < 0:
            level = self.mouse.get("Stimulator", {}).get("mouseLevel", 0)
        self.lickWithholdTimes = []
        self.rewardTimes = []
        self.laserTimes = []
        n = self.mouse.get('Stimulator', {}).get('nRewards', 5)
        print('ready to start trial')
        if not self.task.Stimulus.trialPrep(self.tag):
            self.task.Stimulus.trialEnd()
            return

        #every time lickWithholdtime passes with no licks, make a buzz then give a reward after buzz_lead time.
        self.lickWithholdTimes = []
        self.rewardTimes = []
        self.laserTimes = []
        endTime = time() + self.mouse.get("HeadFixer", {}).get('headFixTime')
        self.speakerIsOn = False
        self.OffForRewardEnd = 0.0
        print('ready for trial')
        while time() < endTime:
            if not self.running:
                break
            # setup to start a trial, withholding licking for lickWithholdRandom secs till buzzer
            # inner loop keeps resetting lickWithholdEnd time until  a succsful withhold
            if(level > 0):
                anyLicks = self.withholdWait(endTime)
                # inner while loop only exits if trial time is up or lick withholding time passed with no licking
                if anyLicks > 0:
                    continue
                # at this point, mouse has just witheld licking for lickWithholdTime
            levels = {
                0: self.rewardTask,
                1: self.rewardTask,
                2: self.goTask,
                3: self.discrimTask
            }
            if time()  >= endTime:
                break
            levels[level]()
            if level ==0:
                sleep(self.mouse.get("Stimulator").get("rewardInterval"))
                n = n -1
                if n == 0:
                    newRewards = resultsDict.get('rewards', 0) + len(self.rewardTimes)
                    resultsDict.update({'rewards': newRewards})
                    self.task.Stimulus.trialEnd()
                    super().stopVideo()
                    return
            #print('{:013}\t{:s}\treward'.format(self.mouse.tag, datetime.fromtimestamp(int(time())).isoformat(' ')))
            self.OffForRewardEnd = time() + self.speakerOffForReward
        # make sure to turn off buzzer at end of loop when we exit
        if self.speakerIsOn == True:
            self.speaker.stop_train()
        newRewards = resultsDict.get('rewards', 0) + len(self.rewardTimes)
        resultsDict.update({'rewards': newRewards})
        self.task.Stimulus.trialEnd()
        #self.camera.stop_preview()
        super().stopVideo()
        #else:
        #    timeInterval = self.mouse.get("Stimulator").get("rewardInterval") #- self.rewarder.rewardDict.get('task')
        #    self.rewardTimes = []
        #    self.camera.start_preview()
        #    for reward in range(self.mouse.get("Stimulator").get("nRewards")):
        #        if not self.running or self.task.tag == 0:
        #            print("break")
        #            break
        #        self.rewardTimes.append(time())
        #        self.rewarder.giveReward('task')
        #        sleep(timeInterval)
        #    newRewards = resultsDict.get('rewards', 0) + self.mouse.get("Stimulator").get("nRewards")
        #    resultsDict.update({'rewards': newRewards})
        #    #self.camera.stop_preview()
        #    super().stopVideo()

    def setdown(self):
        print('Withhold stimulator set down')

    def hardwareTest(self):
        # TODO: Test this
        self.setup()
        while(True):
            inputStr = input('Go and no go tasks will be tested with a dummy mouse\n'
                             's= test speaker, g= go task, n= go/no go task, t= change settings, q= quit: ')
            if inputStr == 's':
                print('testing speaker')
                self.speaker.start_train()
                sleep(1.0)
                self.speaker.stop_train()
            elif inputStr == 'g':
                print("Entering GO task tester")
                self.run(level=2, tag=111111111)
                print("Exiting GO task tester")
            elif inputStr == 'n':
                print("Entering GO/NO GO task tester")
                #start trial
                self.run(level=3, tag=111111111)
                print("Exiting GO/NO GO task tester")
            elif inputStr == 'q':
                break
        pass

#==== High-level Utility functions: Matching of coord systems, target selection and image registration ====
