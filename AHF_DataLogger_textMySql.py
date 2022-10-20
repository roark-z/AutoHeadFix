 #! /usr/bin/python
#-*-coding: utf-8 -*-

from AHF_DataLogger_text import AHF_DataLogger_text
from AHF_DataLogger_mysql import AHF_DataLogger_mysql
from AHF_DataLogger_localsql import AHF_DataLogger_localsql
from AHF_DataLogger import AHF_DataLogger
class AHF_DataLogger_textMySql(AHF_DataLogger):

    """
    Combination of the text data logger and mySQL data logger. Simply does both.

    For Tim.
    """
    TO_SHELL =1
    TO_FILE = 2
    trackingDict = {}
    BUFFER_SIZE = 25

    useLocalSql = True

    @staticmethod
    def config_user_get(starterDict = {}):
        useLocalSql =starterDict.get('useLocalSql', AHF_DataLogger_textMySql.useLocalSql)
        response = input('Do you want to use the local database only? y/n (currently {}): '.format(useLocalSql))
        if response != '':
            if response == 'y' or response == 'Y':
                useLocalSql = True
            else:
                useLocalSql = False

        starterDict.update({'useLocalSql': useLocalSql})
        starterDict = AHF_DataLogger_text.config_user_get(starterDict)
        return AHF_DataLogger_mysql.config_user_get(starterDict)

    def setup(self):
        self.useLocalSql = self.settingsDict.get('useLocalSql')
        self.textLogger = AHF_DataLogger_text(self.task, self.settingsDict)
        self.textLogger.setup()
        self.textLogger.isChild = True
        # if self.useLocalSql:
        #     self.sqlLogger = AHF_DataLogger_localsql(self.task, self.settingsDict)
        #     print('local')
        # else:
        #     self.sqlLogger = AHF_DataLogger_mysql(self.task, self.settingsDict)
        # self.sqlLogger.setup()
        # self.sqlLogger.isChild = True
        pass


    def makeLogFile(self):
        """
        Makes or opens a text log file, or a datbase, or whatever else needs doing. Called once before
        entering main loop of program. DataLogger may make a new file every day in NewDay function, if desired
        """
        self.textLogger.makeLogFile()
        # self.sqlLogger.makeLogFile()
        pass


    def readFromLogFile(self, index):
        """
        Reads the log statement *index* lines prior to the current line.
        Returns the event and associated dictionary in a tuple.
        """
        self.textLogger.readFromLogFile(index)
        # self.sqlLogger.readFromLogFile(index)
        pass


    def writeToLogFile(self, tag, eventKind, eventDict, timeStamp, toShellOrFile = 3):
        """
        The original standard text file method was 4 tab-separated columns, mouse tag, or 0
        if no single tag was applicaple, unix time stamp, ISO formatted time, and event. Event
        could be anything. Now, every event has a kind, and every kind of event defines a
        dictionary. Main program calls writeToLogFile, as well as the Stimulator object
        For text based methods, event should be a dictionary for more complicated stimulator
        results, so an event can be more easily parsed during data analysis.
        """
        super().writeToLogFile(tag, eventKind, eventDict, timeStamp, toShellOrFile)
        self.textLogger.writeToLogFile(tag, eventKind, eventDict, timeStamp, toShellOrFile)
        # self.sqlLogger.writeToLogFile(tag, eventKind, eventDict, timeStamp, 2)

    @staticmethod
    def about():
        return "Combination of text and mysql"

    def setdown(self):
        self.textLogger.setdown()
        # self.sqlLogger.setdown()

    def hardwareTest(self):
        self.textLogger.hardwareTest()
        # self.sqlLogger.hardwareTest()

    def newDay(self):
        """
        At the start of a new day, it was customary for the text-based data logging to start new text files,
        and to make a precis of the day's results into a a separate text file for easy human reading.
        This "quickStats" file should contain info for each mouse with rewards, head fixes,
        or tasks, and other Stimulator specific data, which Stimulator object will provide for each mouse
        just call the Stimulator class functions for each mouse to get a dictionary of results
        """
        self.textLogger.newDay()
        # self.sqlLogger.newDay()
        pass


    def getMice(self):
        """
        returns a list of mice that are in the dictionary/database
        """
        self.textLogger.getMice()
        # self.sqlLogger.getMice()
        pass


    def configGenerator(self):
        """
        generates configuration data for each subject as(IDtag, dictionary) tuples from some kind of permanent storage
        such as a JSON file, or a database. Will be called when program is started, or restarted and settings
        need to be reloaded.
        """
        self.textLogger.configGenerator()
        # self.sqlLogger.configGenerator()
        pass


    def getConfigData(self, tag):
        """
        returns a dictionary of data that was saved for this reference tag, in some permanent storage such as a JSON file
        Will be called when program is started, or restarted and settings need to be reloaded
        """
        self.textLogger.getConfigData(tag)
        # self.sqlLogger.getConfigData(tag)
        pass


    def saveNewMouse(self, tag, note, dictionary):
        """
        store a new mouse entry in a referenced file
        """
        self.textLogger.saveNewMouse(tag, note, dictionary)
        # self.sqlLogger.saveNewMouse(tag, note, dictionary)
        pass


    def retireMouse(self, tag,reason):
        """
        store information about a mouse retirement in a referenced file
        """
        self.textLogger.retireMouse(tag, reason)
        # self.sqlLogger.retireMouse(tag, reason)
        pass


    def storeConfig(self, tag, dictionary, source = ""):
        """
        Stores configuration data, given as an IDtag, and dictionary for that tag, in some more permanent storage
        as a JSON text file, or a database or hd5 file, so it can be later retrieved by IDtag
        """
        self.textLogger.storeConfig(tag, dictionary, source)
        # self.sqlLogger.storeConfig(tag, dictionary, source)
        pass
