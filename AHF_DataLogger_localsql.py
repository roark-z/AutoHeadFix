#! /usr/bin/python
# -*-coding: utf-8 -*-
from time import time
from datetime import datetime
import pymysql
from ast import literal_eval
from AHF_Task import Task
from threading import Thread
import AHF_ClassAndDictUtils as CAD
from AHF_DataLogger import AHF_DataLogger
import json
import os
import pwd
import grp

class AHF_DataLogger_localsql(AHF_DataLogger):
    """
    Data logger that uses the local mysql database. Used in case of unstable remote connections.

    Mouse data is stored in a specified folder as text files, one text file per mouse
    containing JSON formatted configuration and performance data. These files will opened and
    updated after each exit from the experimental tube, in case the program needs to be restarted
    The file name for each mouse contains RFID tag 0-padded to 13 spaces: AHF_mouse_1234567890123.jsn

    REQUESTED VALUES:
    "exit" for exits as event
    "lever_pull" as event for lever data
    "positions" as key for the lever positions in the event_dictionary of "lever_pull"

    """
    PSEUDO_MUTEX = 0
    """
    The class field PSEUDO_MUTEX helps prevent print statements from different places in the code(main vs
    callbacks) from executing at the same time, which leads to garbled output. Unlike a real mutex, execution
    of the thread is not halted while waiting on the PSEUDO_MUTEX, hence the loops with calls to sleep to
    allow the other threads of execution to continue while waiting for the mutex to be free. Also, read/write
    to the PSEUDO_MUTEX is not atomic; one thread may read PSEUDO_MUTEX as 0, and set it to 1, but in the
    interval between reading and writing to PSEUDO_MUTEX,another thread may have read PSEUDO_MUTEX as 0 and
    both threads think they have the mutex
    """
    defaultCage = 'cage1'
    localHost = 'localhost'
    localUser = 'pi'
    localDatabase = 'raw_data'
    localPassword = '*********************'


    @staticmethod
    def about():
        return 'Data logger that prints mouse id, time, event type, and event dictionary to the shell and local mysql database.'

    @staticmethod
    def config_user_get(starterDict={}):
        cageID = starterDict.get('cageID', AHF_DataLogger_localsql.defaultCage)
        response = input('Enter a name for the cage ID(currently {}): '.format(cageID))
        if response != '':
            cageID = response
        localUser =starterDict.get('localUser', AHF_DataLogger_localsql.localUser)
        response = input('Enter your local user name for the database(currently {}): '.format(localUser))
        if response != '':
            localUser = response
        # database
        localDatabase = starterDict.get('localDatabase', AHF_DataLogger_localsql.localDatabase)
        response = input('Enter the local database you want to connect to(currently {}): '.format(localDatabase))
        if response != '':
            localDatabase = response
        # password
        localPassword = starterDict.get('localPassword', AHF_DataLogger_localsql.localPassword)
        response = input('Enter your local user password(currently {}): '.format(localPassword))
        if response != '':
            localPassword = response
        starterDict.update({'cageID': cageID, 'localUser': localUser,'localDatabase': localDatabase, 'localPassword': localPassword })

        return starterDict


    def saveToDatabase(self,query, values):
        db1 = pymysql.connect(host=self.localHost, user=self.localUser, db=self.localDatabase, password=self.localPassword)
        cur1 = db1.cursor()
        try:
            cur1.executemany(query, values)
            db1.commit()
        except pymysql.Error as e:
            try:
                print("MySQL Error [%d]: %s" %(e.args[0], e.args[1]))
                return False
            except IndexError:
                print("MySQL Error: %s" % str(e))
                return False
        except TypeError as e:
            print("MySQL Error: TypeError: %s" % str(e))
            return False
        except ValueError as e:
            print("MySQL Error: ValueError: %s" % str(e))
            return False
        db1.close()
        return True

    def getFromDatabase(self,query,values):
        db2 = pymysql.connect(host=self.localHost, user=self.localUser, db=self.localDatabase, password=self.localPassword)
        cur2 = db2.cursor()
        try:
            cur2.execute(query,values)
            rows = cur2.fetchall()
        except pymysql.Error as e:
            try:
                print("MySQL Error [%d]: %s" %(e.args[0], e.args[1]))
                return None
            except IndexError:
                print("MySQL Error: %s" % str(e))
                return None
        except TypeError as e:
            print("MySQL Error: TypeError: %s" % str(e))
            return None
        except ValueError as e:
            print("MySQL Error: ValueError: %s" % str(e))
            return None
        db2.close()
        return rows


    def makeLogFile(self):
        """
        Initiating database creation
        """
        print("setting up... ")
        raw_data_table_generation = """CREATE TABLE IF NOT EXISTS `raw_data`(`ID` int(11) NOT NULL AUTO_INCREMENT,`Tag` varchar(18) NOT NULL,`Event` varchar(50) NOT NULL,
                                    `Event_dict` varchar(2000) DEFAULT NULL,`Timestamp` timestamp(2) NULL DEFAULT NULL,`Cage` varchar(20) NOT NULL,
                                     `positions` blob, PRIMARY KEY(`ID`), UNIQUE KEY `Tag`(`Tag`,`Event`,`Timestamp`,`Cage`))
                                      ENGINE=InnoDB DEFAULT CHARSET=latin1"""

        config_data_table_generation = """CREATE TABLE IF NOT EXISTS `configs`(`ID` int(11) NOT NULL AUTO_INCREMENT,`Tag` varchar(18) NOT NULL,
                                        `Config` varchar(2000) NOT NULL,`Timestamp` timestamp(2) NULL DEFAULT NULL,`Cage` varchar(20) NOT NULL,
                                        `Dictionary_source` varchar(50) NOT NULL,
                                        PRIMARY KEY(`ID`),UNIQUE KEY `Tag`(`Tag`,`Timestamp`,`Cage`,`Dictionary_source`))
                                         ENGINE=InnoDB DEFAULT CHARSET=latin1"""
        hardwaretest_table_generation = """CREATE TABLE IF NOT EXISTS `hardwaretest`(`ID` int(11) NOT NULL AUTO_INCREMENT,
                                        `Timestamp` timestamp(2) NULL DEFAULT NULL,PRIMARY KEY(`ID`)) ENGINE=InnoDB DEFAULT CHARSET=latin1"""
        mice_table_generation = """CREATE TABLE IF NOT EXISTS `mice`(`ID` int(11) NOT NULL AUTO_INCREMENT,
                                    `Timestamp` timestamp(2) NULL DEFAULT NULL,`Cage` varchar(20) NOT NULL,`Tag` varchar(18) NOT NULL,`Note` varchar(100) NULL DEFAULT NULL,
                                    PRIMARY KEY(`ID`),UNIQUE KEY `Tag`(`Tag`,`Cage`)) ENGINE=InnoDB DEFAULT CHARSET=latin1"""
        try:
            self.saveToDatabase(raw_data_table_generation, [[]]) # create table on local DB
            self.saveToDatabase(config_data_table_generation, [[]]) # create config data table local
            self.saveToDatabase(hardwaretest_table_generation, [[]]) # create hardware test table in local DB
            self.saveToDatabase(mice_table_generation, [[]])  # create hardware test table in local DB
        except Exception as e:
                print("Tables could not be created. Error: ", str(e))


    def setup(self):
        self.cageID = self.settingsDict.get('cageID')
        self.localUser = self.settingsDict.get('localUser')
        self.localDatabase= self.settingsDict.get('localDatabase')
        self.localPassword = self.settingsDict.get('localPassword')
        self.makeLogFile()
        self.raw_save_query = """INSERT INTO `raw_data`(`Tag`,`Event`,`Event_dict`,`Timestamp`,`Cage`,`positions`)
        VALUES(%s,%s,%s,FROM_UNIXTIME(%s),%s,%s)"""
        self.config_save_query = """INSERT INTO `configs`(`Tag`,`Config`,`Timestamp`,`Cage`,`Dictionary_source`) VALUES(%s,%s,FROM_UNIXTIME(%s),%s,%s)"""
        self.add_mouse_query = """INSERT INTO `mice`(`Timestamp`,`Cage`,`Tag`,`Note`) VALUES(FROM_UNIXTIME(%s),%s,%s,%s)"""
        self.events = []
        self.water_available = False
        #showDict = self.task.Show_testable_objects()

        self.events.append([0, 'SeshStart', None, time(),self.cageID,None])
        if self.saveToDatabase(self.raw_save_query, self.events):
            self.events = []

    def setdown(self):
        """
        Writes session end and closes log file
        """
        self.events.append([0, 'SeshEnd', None, time(),self.cageID,None])
        if self.saveToDatabase(self.raw_save_query,self.events):
            self.events = []

#####################################################################################
    def configGenerator(self,settings):
        """
        Each configuration file has config data for a single subject. This function loads data
        from all of them in turn, and returning each as a a tuple of(tagID, dictionary)
        """
        # get the mice first, therefore we need them in the `mice` table, at least their tag number and their cage
        # we will call the mice by their cage which is a class variable
        query_sources = """SELECT DISTINCT `Dictionary_source` FROM `configs` WHERE `Cage` = %s AND `Tag` = %s"""
        sources_list = [i[0] for i in list(self.getFromDatabase(query_sources, [str(self.cageID), str(settings)]))]
        query_config = """SELECT `Tag`,`Dictionary_source`,`Config` FROM `configs` WHERE `Tag` = %s
                                            AND `Dictionary_source` = %s ORDER BY `Timestamp` DESC LIMIT 1"""
        if settings == "changed_subjects":
            mice_list = self.getMice()
            for mice in mice_list:
                for sources in sources_list:
                    try:
                        mouse, source, dictio = self.getFromDatabase(query_config, [str(mice), str(sources)])[0]
                    except:
                        mouse, source, dictio = self.getFromDatabase(query_config, ["default_subjects", str(sources)])[0]
                        mouse = mice
                    sources.update({str(source): literal_eval("{}".format(dictio))})
                data = {int(mouse): sources}
                yield(data)
        if settings == "default_subjects":
            for sources in sources_list:
                mouse, source, dictio = self.getFromDatabase(query_config, ["default_subjects", str(sources)])[0]
                data = {str(source): literal_eval("{}".format(dictio))}
                yield(data)
        if settings == "default_hardware":
            for sources in sources_list:
                print(sources)
                mouse, source, dictio = self.getFromDatabase(query_config, ["default_hardware", str(sources)])[0]
                if "Class" in str(source):
                    data = {str(source): str(dictio)}
                else:
                    data = {str(source): literal_eval("{}".format(dictio))}
                yield(data)
        if settings == "changed_hardware":
            for sources in sources_list:
                mouse, source, dictio = self.getFromDatabase(query_config, ["changed_hardware", str(sources)])[0]
                if "Class" in str(source):
                    data = {str(source): str(dictio)}
                else:
                    data = {str(source): literal_eval("{}".format(dictio))}
                yield(data)

    def getMice(self):
        query_mice = """SELECT `Tag` FROM `mice` WHERE `Cage` = %s"""
        mice_list = [i[0] for i in list(self.getFromDatabase(query_mice, [str(self.cageID)]))]
        return mice_list

    def getConfigData(self, tag,source):
        configs_get = """SELECT `Config` FROM `configs` WHERE `Tag` = %s AND `Dictionary_source` = %s  ORDER BY `Timestamp` DESC LIMIT 1"""
        values=[str(tag),str(source)]
        config_data = self.getFromDatabase(configs_get,values)[0][0]
        config_data = literal_eval("{}".format(config_data))
        return config_data

    def storeConfig(self, tag, configDict,source):
        # store in raw data
        self.events.append([tag, "config_{}".format(source), str(configDict), time(), self.cageID,None])
        if self.saveToDatabase(self.raw_save_query, self.events):
            self.events = []
        # store in the config table
        self.saveToDatabase(self.config_save_query, [[tag, str(configDict), time(), self.cageID, str(source)]])

    def saveNewMouse(self,tag,note, dictionary = {}):
        # store new mouse `Timestamp`,`Cage`,`Tag`,`Note`
        self.events.append([tag, 'added_to_cage', str(dict([("Notes",note)])), time(), self.cageID, None])
        if self.saveToDatabase(self.raw_save_query, self.events):
            self.events = []
        self.saveToDatabase(self.add_mouse_query, [[time(), self.cageID, tag,str(note)]])

    def retireMouse(self,tag,reason):
        # update information about a mouse `Timestamp`,`Cage`,`Tag`,`Activity`
        self.events.append([tag, 'retired', str(dict([("reason", reason)])), time(), self.cageID, None])
        if self.saveToDatabase(self.raw_save_query, self.events):
            self.events = []
        delete_mouse_query = """DELETE FROM `mice` WHERE `Tag`=%s"""
        self.saveToDatabase(delete_mouse_query, [[tag]])

#######################################################################################
    def newDay(self):
        self.events.append([0, 'NewDay', None, time(),self.cageID,None])
        if self.saveToDatabase(self.raw_save_query, self.events):
            self.events = []

    def readFromLogFile(self, index):
        eventQuery = """SELECT `Event` from `raw_data` WHERE 1 ORDER BY `raw_data`.`Timestamp` LIMIT %s-1, 1"""
        eventDictQuery = """SELECT `Event_dict` from `raw_data` WHERE 1 ORDER BY `raw_data`.`Timestamp` LIMIT %s-1, 1"""
        event = self.getFromDatabase(eventQuery, [index])
        eventDict = self.getFromDatabase(eventDictQuery, [index])
        return(event, eventDict)

    def writeToLogFile(self, tag, eventKind, eventDict, timeStamp, toShellOrFile=3):
        super().writeToLogFile(tag, eventKind, eventDict, timeStamp, toShellOrFile)
        if(toShellOrFile & self.TO_FILE) > 0:
            if eventKind == "lever_pull":
                lever_positions = eventDict.get("positions")
                lever_positions = list(map(lambda x: str(x), lever_positions))
                lever_positions = ",".join(lever_positions)
                del eventDict["positions"]
                self.events.append([tag, eventKind, str(eventDict), timeStamp, self.cageID, lever_positions])
            else:
                self.events.append([tag, eventKind, str(eventDict), timeStamp, self.cageID, None])
        if eventKind == "exit" and toShellOrFile & self.TO_FILE:
            Thread(target=self.saveToDatabase, args=(self.raw_save_query, self.events)).start()
            self.events = []
        if(toShellOrFile & self.TO_SHELL) > 0:
            print('{:013}\t{:s}\t{:s}\t{:s}\t{:s}\n'.format(tag, eventKind, str(eventDict), datetime.fromtimestamp(int(timeStamp)).isoformat(' '), self.cageID))

    def pingServers(self):
        query_save = """INSERT INTO `hardwaretest`(`Timestamp`)
                                VALUES(FROM_UNIXTIME(%s))"""
        values = [[time()]]
        query_get = """SELECT `Timestamp` FROM `hardwaretest` WHERE 1 ORDER BY `hardwaretest`.`Timestamp` DESC LIMIT 1"""
        try:
            self.saveToDatabase(query_save, values)
            response = str(self.getFromDatabase(query_get, [])[0][0])
            print("last test entry local DB: ", response)
        except:
            print("no connection to localhost")


    def hardwareTest(self):
        while True:
            inputStr = '\n************** Mouse Configuration ********************\nEnter:\n'
            inputStr += 'T to Test database connections\n'
            inputStr += 'J to generate a Json file of hardware settings from database\n'
            inputStr += 'Q to quit\n'
            event = input(inputStr)
            if event == 'T' or event == 't': # send timestamps to servers and then request the last timestamp
                self.pingServers()
            elif event == 'j' or event == 'J':
                response = input('generate json file from Database.\n D for default settings,\n L for last settings,\n type nothing to abort')
                if response != '':
                    jsonDict = {}
                    if response[0] == 'D' or response[0] == 'd':
                        settings = "default_hardware"
                        for config in self.configGenerator(settings):
                            jsonDict.update(config)
                    elif response[0] == 'L' or response[0] == 'l':
                        settings = "changed_hardware"
                        for config in self.configGenerator(settings):
                            jsonDict.update(config)
                    if len(jsonDict) > 0:
                        nameStr = input('please enter the filename. your file will be automatically named: AHF_filename_hardware.json')
                        configFile = 'AHF_' + nameStr + '_hardware.json'
                        with open(configFile, 'w') as fp:
                            fp.write(json.dumps(jsonDict, separators=('\n', '='), sort_keys=True, skipkeys=True))
                            fp.close()
                            uid = pwd.getpwnam('pi').pw_uid
                            gid = grp.getgrnam('pi').gr_gid
                            os.chown(configFile, uid, gid)  # we may run as root for pi PWM, so we need to explicitly set ownership
    # TODO settingsdict????
            elif event == 'Q' or event == 'q':
                break
                

    def __del__(self):
        self.events.append([0, 'SeshEnd', None, time(),self.cageID,None])
        self.saveToDatabase(self.raw_save_query, self.events)
        self.events = []
        self.setdown()
