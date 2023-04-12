#! /usr/bin/python
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from AHF_Rewarder import AHF_Rewarder
from time import sleep, time
from collections import deque

class AHF_Rewarder_solenoid(AHF_Rewarder,metaclass = ABCMeta):
    """
    An abstract base class to use a solenoid to deliver water rewards using 1 GPIO pin, subclasses use different timing methods
    """
    rewardUnits = 'Seconds'
    testAmount = 1.0
    defaultPin = 13
    defaultEntry = 0.2
    defaultBreakBeam = 0.1
    defaultWait = 15*60
    defaultBBWait = 1
    defaultTask = 0.4


    @staticmethod
    def config_user_get(starterDict = {}):
        rewardPin = starterDict.get('rewardPin', AHF_Rewarder_solenoid.defaultPin)
        response = input('Enter the GPIO pin used by the water delivery solenoid(currently %d): ' % rewardPin)
        if response != '':
            rewardPin = int(response)
        rewards = starterDict.get('rewards', {})
        entry = rewards.get('entry', AHF_Rewarder_solenoid.defaultEntry)
        response = input('Enter solenoid opening duration, in seconds, for entry rewards,(currently %.2f): ' % AHF_Rewarder_solenoid.defaultEntry)
        if response != '':
            entry = float(response)
        task = rewards.get('task', AHF_Rewarder_solenoid.defaultTask)
        response = input('Enter solenoid opening duration, in seconds, for task rewards,(currently %.2f): ' % AHF_Rewarder_solenoid.defaultTask)
        if response != '':
            task = float(response)
        maxEntryRewards = starterDict.get('maxEntryRewards', AHF_Rewarder_solenoid.maxEntryRewardsDefault)
        response = input('Enter the maximum number of entry rewards given per day(currently %d): ' % maxEntryRewards)
        if response != '':
            maxEntryRewards = int(response)
        entryRewardDelay = starterDict.get('entryRewardDelay', AHF_Rewarder_solenoid.entryRewardDelayDefault)
        response = input('Enter the delay between entering and getting a reward(currently %.2f): ' % entryRewardDelay)
        if response != '':
            entryRewardDelay = float(response)
        rewards.update({'entry' : entry, 'task' : task, 'test' : AHF_Rewarder_solenoid.testAmount})
        starterDict.update({'rewardPin': rewardPin, 'rewards' : rewards})
        starterDict.update({'maxEntryRewards' : maxEntryRewards, 'entryRewardDelay' : entryRewardDelay})
        return AHF_Rewarder.config_user_get(starterDict)


    def config_user_subject_get(self,starterDict = {}):
        starterDict.update({'totalEntryRewardsToday' : 0})
        starterDict.update({'totalBreakBeamRewardsToday' : 0})
        entrySize = starterDict.get('entrySize', AHF_Rewarder_solenoid.defaultEntry)
        response = input(
            'Enter the valve opening duration, in seconds, for entry rewards. Currently {:.2f}: '.format(entrySize))
        if response != '':
            entrySize = float(response)
        starterDict.update({'entrySize': entrySize})
        entryDelay = starterDict.get('entryDelay', AHF_Rewarder_solenoid.defaultWait)
        response = input(
            'Enter the delay between successive entry rewards, in seconds. Currently {:.2f}: '.format(entryDelay))
        if response != '':
            entryDelay = float(response)
        starterDict.update({'entryDelay': entryDelay})
        starterDict.update({'lastEntryTime': 0})
        starterDict.update({'lastBreakBeamTime': 0})
        taskSize = starterDict.get('taskSize', AHF_Rewarder_solenoid.defaultTask)
        response = input(
            'Enter the valve opening duration, in seconds, for task rewards. Currently {:.2f}: '.format(taskSize))
        if response != '':
            taskSize = float(response)
        starterDict.update({'taskSize': taskSize})
        maxEntryRewards = starterDict.get('maxEntryRewards', AHF_Rewarder_solenoid.maxEntryRewardsDefault)
        response = input('Enter the maximum number of entry reards given per day')
        if response != '':
            maxEntryRewards = int(response)
        starterDict.update({'maxEntryRewards' : maxEntryRewards})
        breakBeamSize = starterDict.get('breakBeamSize', AHF_Rewarder_solenoid.defaultBreakBeam)
        response = input(
            'Enter the valve opening duration, in seconds, for break beam rewards. Currently {:.2f}: '.format(breakBeamSize))
        if response != '':
            breakBeamSize = float(response)
        starterDict.update({'breakBeamSize': breakBeamSize})
        breakBeamDelay = starterDict.get('breakBeamDelay', AHF_Rewarder_solenoid.defaultBBWait)
        response = input(
            'Enter the delay between successive breakBeam rewards, in seconds. Currently {:.2f}: '.format(breakBeamDelay))
        if response != '':
            breakBeamDelay = float(response)
        starterDict.update({'breakBeamDelay': breakBeamDelay})
        maxBreakBeamRewards = starterDict.get('maxBreakBeamRewards', AHF_Rewarder_solenoid.maxBreakBeamRewardsDefault)
        response = input('Enter the maximum number of break beam reards given per day')
        if response != '':
            maxBreakBeamRewards = int(response)
        starterDict.update({'maxBreakBeamRewards' : maxBreakBeamRewards})
        return starterDict

    def config_subject_get(self, starterDict={}):
        entrySize = starterDict.get('entrySize', AHF_Rewarder_solenoid.defaultEntry)
        starterDict.update({'entrySize': entrySize})
        entryDelay = starterDict.get('entryDelay', AHF_Rewarder_solenoid.defaultWait)
        starterDict.update({'entryDelay': entryDelay})
        starterDict.update({'lastEntryTime': 0})
        starterDict.update({'lastBreakBeamTime': 0})
        taskSize = starterDict.get('taskSize', AHF_Rewarder_solenoid.defaultTask)
        starterDict.update({'taskSize': taskSize})
        maxEntryRewards = starterDict.get('maxEntryRewards', AHF_Rewarder_solenoid.maxEntryRewardsDefault)
        starterDict.update({'maxEntryRewards' : maxEntryRewards})
        breakBeamSize = starterDict.get('breakBeamSize', AHF_Rewarder_solenoid.defaultBreakBeam)
        starterDict.update({'breakBeamSize': breakBeamSize})
        breakBeamDelay = starterDict.get('breakBeamDelay', AHF_Rewarder_solenoid.defaultBBWait)
        starterDict.update({'breakBeamDelay': breakBeamDelay})
        maxBreakBeamRewards = starterDict.get('maxBreakBeamRewards', AHF_Rewarder_solenoid.maxBreakBeamRewardsDefault)
        starterDict.update({'maxBreakBeamRewards' : maxBreakBeamRewards})
        starterDict.update({'totalEntryRewardsToday' : 0})
        starterDict.update({'totalBreakBeamRewardsToday' : 0})
        return starterDict

    def results_subject_get(self):
        return self.results

    @abstractmethod
    def setup(self):
        self.rewardPin = self.settingsDict.get('rewardPin')
        self.rewards = self.settingsDict.get('rewards')
        self.countermandTime = self.settingsDict.get('entryRewardDelay')
        self.maxEntryRewards = self.settingsDict.get('maxEntryRewards')
        self.countermanded = ''
        self.results = deque(maxlen=25)
        self.task.DataLogger.startTracking("Reward", "consumed", "buffer", size=200)

    def newResultsDict(self):
        """
        Return a dictionary of keys = rewardNames, values = number of rewards given, each mouse will get one of these for reward monitoring each day
        """
        rDict = {}
        for item in self.settingsDict.get('rewards').items():
            itemKey = item [0]
            #itemVal = item [1]
            if itemKey != 'test':
                rDict.update({itemKey : 0})
        return rDict

    def clearResultsDict(self, resultsDict):
        """
        Clears results for daily totals of reward types
        """
        for item in resultsDict.items():
            itemKey = item [0]
            resultsDict.update({itemKey : 0})


    def giveReward(self, rewardName, resultsDict={}, settingsDict = {}):
        """
        Gives reward, if reward name is in dictionary. If an entry reward, must be less than number of max entry rewards per day
        """
        self.countermandReward()
        if rewardName is 'test':
            self.threadReward(1)
            return 1
        if rewardName is 'entry':
            if self.entryHandling() == 0:
                return 0
        if rewardName is 'breakBeam':
            if self.breakBeamHandling() == 0:
                return 0
        if self.task.Subjects.get(self.task.tag) is None:
            sleepTime = 0.4
        else:
            sleepTime =settingsDict.get(rewardName, self.task.Subjects.get(self.task.tag).get("Rewarder").get(rewardName + "Size"))
        if sleepTime ==0:
            return 0
        else:
            resultsDict.update({rewardName: resultsDict.get(rewardName, 0) + 1})
            self.task.DataLogger.writeToLogFile(self.task.tag, 'Reward', {'kind' : rewardName, 'size' : sleepTime, 'consumed': False}, time())
            print("Rewards so far: ", self.task.DataLogger.getTrackedEvent(self.task.tag, "Reward", "consumed"))
            self.threadReward(sleepTime)
            return sleepTime

    def entryHandling(self):
        mouseDict = self.task.Subjects.get(self.task.tag)
        if mouseDict is not None:
            if mouseDict.get("Rewarder").get("totalEntryRewardsToday") >= mouseDict.get('Rewarder').get('maxEntryRewards'):
                return 0
            lastTime = mouseDict.get("Rewarder").get("lastEntryTime")
            if time() - lastTime < mouseDict.get("Rewarder").get('entryDelay'):
                return 0
            self.task.Subjects.get(self.task.tag).get("Rewarder").update({"lastEntryTime": time()})
            mouseDict.get('Rewarder').update({'totalEntryRewardsToday': mouseDict.get('Rewarder').get("totalEntryRewardsToday") + 1})
            return 1
        return 0

    def breakBeamHandling(self):
        mouseDict = self.task.Subjects.get(self.task.tag)
        if mouseDict is not None:
            if mouseDict.get("Rewarder").get("totalBreakBeamRewardsToday") >= mouseDict.get('Rewarder').get('maxBreakBeamRewards'):
                return 0
            lastTime = mouseDict.get("Rewarder").get("lastBreakBeamTime")
            if time() - lastTime < mouseDict.get("Rewarder").get('breakBeamDelay'):
                return 0
            mouseDict.get('Rewarder').update({'totalBreakBeamRewardsToday': mouseDict.get('Rewarder').get("totalBreakBeamRewardsToday") + 1})
            return 1
        return 0

    def giveRewardCM(self, rewardName, resultsDict={}, settingsDict = {}):
        """
        Gives a reward that can be countermanded, i.e. cancelled if occurring before a timeour
        """
        if rewardName is 'entry':
            if self.entryHandling() == 0:
                return 0
        if rewardName is 'breakBeam':
            if self.breakBeamHandling() == 0:
                return 0
        if self.task.Subjects.get(self.task.tag) is None:
            sleepTime = 0.4
        else:
            sleepTime =settingsDict.get(rewardName, self.task.Subjects.get(self.task.tag).get("Rewarder").get(rewardName + "Size"))
        if sleepTime ==0:
            return 0
        else:
            resultsDict.update({rewardName: resultsDict.get(rewardName, 0) + 1})
            self.task.DataLogger.writeToLogFile(self.task.tag, 'Reward', {'kind' : rewardName, 'size' : sleepTime, 'consumed': False}, time())
            self.countermanded = rewardName
            self.threadCMReward(sleepTime)
            return sleepTime

    def countermandReward(self,resultsDict={}, settingsDict = {}):
        """
        Countermands the previously given reward
        """
        if self.threadCountermand():
            resultsDict.update({self.countermanded: resultsDict.get(self.countermanded, 0) - 1})

        return 0

    @abstractmethod
    def threadReward(self, sleepTime):
        pass

    @abstractmethod
    def threadCMReward(self, sleepTime):
        pass

    @abstractmethod
    def threadCountermand(self):
        pass
