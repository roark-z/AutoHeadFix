#! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Rewarder import AHF_Rewarder
from time import sleep

class AHF_Rewarder_solenoid (AHF_Rewarder,metaclass = ABCMeta):
    """
    An abstract base class to use a solenoid to deliver water rewards using 1 GPIO pin, subclasses use different timing methods
    """
    rewardUnits = 'Seconds'
    testAmount = 1.0
    defaultPin = 13
    defaultEntry = 0.2
    defaultTask = 0.4

    gTask = none
    
    @staticmethod
    def config_user_get(starterDict = {}):
        rewardPin = starterDict.get ('rewardPin', AHF_Rewarder_solenoid.defaultPin)
        response = input('Enter the GPIO pin used by the water delivery solenoid (currently %d): ' % rewardPin)
        if response != '':
            rewardPin = int (response)
        rewards = starterDict.get ('rewards', {})
        entry = rewards.get ('entry', AHF_Rewarder_solenoid.defaultEntry)
        response = input ('Enter solenoid opening duration, in seconds, for entry rewards, (currently %.2f): ' % AHF_Rewarder_solenoid.defaultEntry)
        if response != '':
            entry = float (response)
        task = rewards.get ('task', AHF_Rewarder_solenoid.defaultTask)
        response = input ('Enter solenoid opening duration, in seconds, for task rewards, (currently %.2f): ' % AHF_Rewarder_solenoid.defaultTask)
        if response != '':
            task = float (response)
                maxEntryRewards = starterDict.get ('maxEntryRewards', AHF_Rewarder_solenoid.maxEntryRewardsDefault)
        response = input('Enter the maximum number of entry reards given per day (currently %d): ' % maxEntryRewards)
        if response != '':
            maxEntryRewards = int (response)
        entryRewardDelay = starterDict.get ('entryRewardDelay', AHF_Rewarder_solenoid.entryRewardDelayDefault)
        response = input('Enter the delay between entering and getting a reward (currently %.2f): ' % defaultEntryRewardDelay)
        if response != '':
            entryRewardDelay = float (response)
        rewards.update({'entry' : entry, 'task' : task, 'test' : AHF_Rewarder_solenoid.testAmount})
        starterDict.update ({'rewardPin': rewardPin, 'rewards' : rewards})
        starterDict.update ({'maxEntryRewards' : maxEntryRewards, 'entryRewardDelay' : entryRewardDelay})
        return AHF_Rewarder.config_user_get (starterDict)


    @abstractmethod
    def setup (self):
        self.rewardPin = self.settingsDict.get('rewardPin')
        self.rewards = self.settingsDict.get ('rewards')
        self.countermandTime = self.settingsDict.get ('entryRewardDelay')
        self.maxEntryRewards = self.settingsDict.get ('maxEntryRewards')
        self.countermanded = ''
        gTask = self.task

    def newResultsDict (self):
        """
        Return a dictionary of keys = rewardNames, values = number of rewards given, each mouse will get one of these for reward monitoring each day
        """
        rDict = {}
        for key in self.settingsDict.get ('rewards').items():
            if key != 'test':
                rDict.update({key : 0})
        return rDict

    def clearResultsDict(self, resultsDict):
        """
        Clears results for daily totals of reward types
        """
        for key in resultsDict.items():
            resultsDict.update({key : 0})

    
    def giveReward(self, rewardName, resultsDict={}, settingsDict = {}):
        """
        Gives reward, if reward name is in dictionary. If an entry reward, must be less than number of max entry rewards per day
        """
        if rewardName is 'entry' and resultsDict.get ('entry', 0) > settingsDict.get ('maxEntryRewards', self.maxEntryRewards):
            return 0
        else:
            sleepTime =settingsDict.get(rewardName, self.rewards.get (rewardName, 0))
            if sleepTime ==0:
                return 0
            else:                     
                resultsDict.update {rewardName, resultsDict.get (rewardName, 0) + 1})
                self.task.DataLogger.writeToLogFile(self.task.tag, 'Reward', {'kind' : rewardName, 'size' : sleepTime}, time())
                self.threadReward (sleepTime)
                return sleepTime
                

    def giveRewardCM(self, rewardName, resultsDict={}, settingsDict = {}):
        """
        Gives a reward that can be countermanded, i.e. cancelled if occurring before a timeour
        """
        if rewardName is 'entry' and resultsDict.get ('entry', 0) > settingsDict.get ('maxEntryRewards', self.maxEntryRewards):
            return 0
        else:
            sleepTime =settingsDict.get(rewardName, self.rewards.get (rewardName, 0))
            if sleepTime ==0:
                return 0
            else:                     
                resultsDict.update {rewardName, resultsDict.get (rewardName, 0) + 1})
                self.countermanded = rewardName
                self.threadCMReward (sleepTime)
                return sleepTime

    def countermandReward(self,resultsDict={}, settingsDict = {}):
        """
        Countermands the previously given reward
        """
        if self.threadCountermand ():
            resultsDict.update {self.countermanded, resultsDict.get (self.countermanded, 0) - 1})
             
        return 0
    
    @abstractmethod
    def threadReward (self, sleepTime):
        pass

    @abstractmethod
    def threadCMReward (self, sleepTime):
        pass

    @abstractmethod
    def threadCountermand (self):
        pass
    
    
    def hardwareTest (self):
        print ('\nReward Solenoid opening for %.2f %s' % (self.testAmount, self.rewardUnits))
        self.giveReward('test')
        sleep (self.testAmount)
        inputStr= input('Reward Solenoid closed.\nDo you want to change the Reward Solenoid Pin (currently %d)? ' % self.rewardPin)
        if inputStr[0] == 'y' or inputStr[0] == "Y":
            self.setdown ()
            self.settingsDict = self.config_user_get (self.settingsDict)
            self.setup() 
                    
        
