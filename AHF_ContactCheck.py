#! /usr/bin/python3
#-*-coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from AHF_Base import AHF_Base

class AHF_ContactCheck(AHF_Base, metaclass = ABCMeta):

    '''
    Base class for ContactCheck. This class handles the detection of mice entering/exiting the trial area.
    '''

    @abstractmethod
    def checkContact(self):
        '''
        Checks for contact.

        :returns: :code:`bool` whether contact is made.
        '''
        return False

    @abstractmethod
    def waitForContact(self, timeoutSecs):
        '''
        Blocks execution until contact or timeout.

        Note: do not call while logging via startLogging, as it could lead to deadlocks.
        '''
        return False

    @abstractmethod
    def waitForNoContact(self, timeoutSecs):
        '''
        Blocks execution until no contact or timeout.

        Note: do not call while logging via startLogging, as it could lead to deadlocks.
        '''
        return False

    def turnOn (self):
        pass

    def turnOff (self):
        pass

    @abstractmethod
    def startLogging(self):
        """
        Starts running background task, checking for contact.

        Constantly updates gTask.contact variable in AHF_Task.
        
        Note: do not use waitForContact or waitForNoContact while logging
        """
        pass

    @abstractmethod
    def stopLogging(self):
        """
        Stops contactChecker running background task.
        """

    def hardwareTest(self):
        print('To pass test, start with no contact. Make contact within 10 seconds, then hold contact for less than 10 seconds')
        passed = False
        if self.checkContact():
            print('Contact is already made. F')
        else:
            print('Waiting for contact ....')
            if not self.waitForContact(10):
                print('No contact after waiting for 10 seconds. F')
            else:
                print('Contact Made!  -  Waiting for contact to be broken....')
                if not self.waitForNoContact(10):
                    print('Contact maintained for more than 10 seconds. F')
                else:
                    print('Contact Broken! test passed')
                    passed = True
        self.stopLogging()
        if not passed:
            result = input('Would you like to edit settings for contact check, Y or N?')
            if result[0] == 'Y' or result [0] == 'y':
                self.setdown()
                self.settingsDict = self.config_user_get(self.settingsDict)
                self.setup()
