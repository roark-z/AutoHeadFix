 #! /usr/bin/python3
#-*-coding: utf-8 -*-

from time import time, localtime,timezone, sleep
from datetime import datetime
from AHF_Stimulator import AHF_Stimulator

class AHF_Stimulator_Rewards(AHF_Stimulator):
    defaultRewards = 5
    defaultInterval = 3


    @staticmethod
    def about():
        return 'Rewards stimulator gives periodic rewards, no interaction from mouse required.'


    @staticmethod
    def config_user_get(starterDict = {}):
        return AHF_Stimulator.config_user_get(starterDict)

    def config_user_subject_get(self,starterDict = {}):
        nRewards = starterDict.get('nRewards', AHF_Stimulator_Rewards.defaultRewards)
        response = input('Enter the number of rewards you want to give per head fixing session(currently %d): ' % nRewards)
        if response != '':
            nRewards = int(response)
        rewardInterval = starterDict.get('rewardInterval', AHF_Stimulator_Rewards.defaultInterval)
        response = input('Enter the time interval between rewards(currently %.2f seconds): ' % rewardInterval)
        if response != '':
            rewardInterval = float(response)
        starterDict.update({'nRewards' : nRewards, 'rewardInterval' : rewardInterval})
        return starterDict

    def config_subject_get(self, starterDict={}):
        nRewards = starterDict.get('nRewards', AHF_Stimulator_Rewards.defaultRewards)
        rewardInterval = starterDict.get('rewardInterval', AHF_Stimulator_Rewards.defaultInterval)
        starterDict.update({'nRewards' : nRewards, 'rewardInterval' : rewardInterval})
        return starterDict


    def setup(self):
        self.rewarder = self.task.Rewarder
        super().setup()


    def setdown(self):
        print('Rewards stimulator set down')


    def run(self, level = 0, resultsDict = {}, settingsDict = {}):
        super().run()
        if hasattr(self.task, 'Camera'):
            super().startVideo()
        self.rewardTimes = []
        tag = self.task.tag
        if tag <= 0:
            return
        for reward in range(self.task.Subjects.get(tag).get("Stimulator").get("nRewards")):
            if not self.running:
                break
            self.rewardTimes.append(time())
            self.rewarder.giveReward('task')
            if tag > 0:
                sleep(self.task.Subjects.get(tag).get("Stimulator").get("rewardInterval"))
            else:
                sleep(AHF_Stimulator_Rewards.defaultInterval)
        if hasattr(self.task, 'Camera'):
            super().stopVideo()


    def nextDay(self):
        """
            Called when the next day starts. The stimulator is given the new log file pointer. Can do other things as needed
            :param newFP: the file pointer for the new day's log file
        """


    def quitting(self):
        """
            Called before AutoHEadFix exits. Gives stimulator chance to do any needed cleanup

            A stimulator may, e.g., open files and wish to close them before exiting, or use hardware that needs to be cleaned up
        """
        # if hasattr(self.task, 'Camera'):
        #     self.task.Camera.stop_recording()
        pass


    def hardwareTest(self):
        # TODO: Test this
        pass


"""
if __name__ == '__main__':
    import RPi.GPIO as GPIO
    try:
        GPIO.setmode(GPIO.BCM)
        rewarder = AHF_Rewarder(30e-03, 24)
        rewarder.addToDict('task', 50e-03)
        thisMouse = Mouse(2525, 0,0,0,0)
        #stimFile = AHF_Stimulator.get_stimulator()
        #stimulator = AHF_Stimulator.get_class(stimFile)(stimdict, rewarder, None)
        stimdict = {'nRewards' : 5, 'rewardInterval' : .25}
        #stimdict = AHF_Stimulator.configure({})
        #print('stimdict:')
        #for key in sorted(stimdict.keys()):
        #   print(key + ' = ' + str(stimdict[key]))
        stimulator = AHF_Stimulator_Rewards(stimdict, rewarder, None)
        print(stimulator.configStim(thisMouse))
        stimulator.run()
        stimulator.logfile()
        thisMouse.show()
    except FileNotFoundError:
        print('File not found')
    finally:
        GPIO.cleanup()
"""
