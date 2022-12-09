
#! /usr/bin/python3
#-*-coding: utf-8 -*-

from time import time, localtime,timezone, sleep
from datetime import datetime, timedelta
from sys import argv
import faulthandler
import pymysql
from ast import literal_eval
import inspect
from abc import ABCMeta
import RPi.GPIO as GPIO
# Task configures and controls sub-tasks for hardware and stimulators
from AHF_Task import Task
# hardware tester can be called from menu pulled up by keyboard interrupt
from AHF_HardwareTester import hardwareTester

"""
when we start a new day, in 24 hr format, so 7 is 7 AM and 19 is 7 PM. We close the text files
and open new ones for the day.
"""
kDAYSTARTHOUR =19

"""
constant for time outs when waiting on an event - instead of waiting for ever, and missing, e.g., keyboard event,
or callling sleep and maybe missing the thing we were waiting for, we loop using wait_for_edge with a timeout
"""
kTIMEOUTSECS = 50e-03


def main():
    """
    The main function for the AutoHeadFix program.

    It initializes or loads settings and configurations, then endlessly loops running entries and head fix trials
    Ctrl-C is used to enter a menu-driven mode where settings can be altered.
    """
    faulthandler.enable()
    try:
        configFile = ''
        if argv.__len__() > 1 and argv[1] == "--temp":
            jsonDict = {}
            cageID, user, pwd, db = '', '', '', ''
            with open("/home/pi/config.txt", "r") as file:
                configs = file.readlines()
                print(configs)
                for config in configs:
                    config = config.split("=")
                    if config[0] == "cageID":
                        cageID = config[1].rstrip("\n")
                    if config[0] == "user":
                        user = config[1].rstrip("\n")
                    if config[0] == "pwd":
                        pwd = config[1].rstrip("\n")
                    if config[0] == "db":
                        db = config[1].rstrip("\n")
            print(cageID, user, pwd, db)
            db = pymysql.connect(host="localhost", user=user, db=db, password=pwd)
            query_sources = """SELECT DISTINCT `Dictionary_source` FROM `configs` WHERE `Cage` = %s AND `Tag` = %s"""
            cur  = db.cursor()
            if argv.__len__() > 2:
                cageID = argv[2]
            cur.execute(query_sources, [cageID, "changed_hardware"])

            sources_list =  [i[0] for i in cur.fetchall()]
            query_config = """SELECT `Tag`,`Dictionary_source`,`Config` FROM `configs` WHERE `Tag` = %s
                                            AND `Dictionary_source` = %s ORDER BY `Timestamp` DESC LIMIT 1"""
            cur.execute(query_config, ["cage1", "changed_hardware"])
            for sources in sources_list:
                cur.execute(query_config, ["changed_hardware", str(sources)])
                mouse, source, dictio = cur.fetchall()[0]
                if "Class" in str(source):
                    data = {str(source): str(dictio)}
                else:
                    data = {str(source): literal_eval("{}".format(dictio))}
                jsonDict.update(data)
            jsonDict.update({"filename": "temp"})
            print(jsonDict)
            task = Task(object = jsonDict)
            db.close()
        elif argv.__len__() > 1 and argv[1] == "--noedit":
            task = Task('')
        else:
            task = Task('')
            task.editSettings()
        task.setup()
    except Exception as e:
        print('Error initializing hardware' + str(e))
        raise e
    assert(hasattr(task, 'BrainLight')) # quick debug check that task got loaded and setup ran
    # calculate time for saving files for each day
    now = datetime.fromtimestamp(int(time()))
    nextDay = datetime(now.year, now.month, now.day, kDAYSTARTHOUR,0,0)
    if now >= nextDay:
        nextDay = nextDay + timedelta(hours=24)
    # start TagReader and Lick Detector, the two background task things, logging
    task.Reader.startLogging()
    if hasattr(task, 'LickDetector'):
        task.LickDetector.startLogging()
     # Top level infinite Loop running mouse entries
    try:
        resultsDict = {"HeadFixer": {}, "Rewarder": {}, "Stimulator": {}}
        while True:
            try:

                print('Waiting for a mouse....')
                task.ContactCheck.startLogging()
                # loop with a brief sleep, waiting for a tag to be read, or a new day to dawn
                while True:
                    if task.tag != 0:
                        break
                    else:
                        if datetime.fromtimestamp(int(time())) > nextDay:
                            task.DataLogger.newDay()
                            now = datetime.fromtimestamp(int(time()))
                            nextDay = datetime(now.year, now.month, now.day, kDAYSTARTHOUR,0,0) + timedelta(hours=24)
                            resultsDict = {"HeadFixer": {}, "Rewarder": {}, "Stimulator": {}}
                        else:
                            sleep(kTIMEOUTSECS)
                # a Tag has been read, get a reference to the dictionaries for this subject
                thisTag = task.tag
                settingsDict = task.Subjects.miceDict.get(str(thisTag))
                #temp
                # queue up an entrance reward, that can be countermanded if a) mouse leaves early, or b) fixes right away
                task.Rewarder.giveRewardCM('entry', resultsDict.get('Rewarder'), settingsDict.get('Rewarder'))
                doCountermand = True
                # loop through as many trials as this mouse wants to do before leaving chamber
                while task.tag == thisTag:
                    # Fix mouse - returns True if 'fixed', though that may just be a True contact check if a no-fix trial
                    task.fixed = task.HeadFixer.fixMouse(thisTag, resultsDict.get('HeadFixer'), settingsDict.get('HeadFixer'))
                    if task.fixed:
                        if doCountermand:
                            task.Rewarder.countermandReward(resultsDict.get('Rewarder'), settingsDict.get('Rewarder'))
                            doCountermand = False
                                            #temporary
                        task.Stimulator.run(-1, resultsDict.get('Stimulator'), settingsDict.get('Stimulator'))
                        task.HeadFixer.releaseMouse(thisTag)
                if doCountermand:
                    task.Rewarder.countermandReward(resultsDict.get('Rewarder'), settingsDict.get('Rewarder'))

            except KeyboardInterrupt:
                    # tag, eventKind, eventDict, timeStamp, toShellOrFile
                    task.Stimulator.quitting()
                    task.HeadFixer.releaseMouse(task.tag)
                    task.DataLogger.setdown()
                    task.ContactCheck.stopLogging()
                    if hasattr(task, 'LickDetector'):
                        task.LickDetector.stopLogging()
                    inputStr = '\n************** Auto Head Fix Manager ********************\nEnter:\n'
                    inputStr += 'V to run rewarder(valve) control\n'
                    inputStr += 'H for hardware tester\n'
                    inputStr += 'A to edit Animals\' individualized settings\n'
                    inputStr += 'S to edit Stimulator settings\n'
                    inputStr += 'T to edit Task configuration\n'
                    inputStr += 'L to log a note\n'
                    inputStr += 'R to Return to head fix trials\n'
                    inputStr += 'Q to quit\n:'
                    while True:
                        event = input(inputStr)
                        if event == 'r' or event == "R":
                            GPIO.setmode(GPIO.BCM)
                            if hasattr(task, 'LickDetector'):
                                task.LickDetector.startLogging()
                            break
                        elif event == 'q' or event == 'Q':
                            return
                        elif event == 'v' or event == 'V':
                            task.Rewarder.rewardControl()
                        elif event == 'a' or event == 'A':
                            task.Subjects.subjectSettings()
                        elif event == 'h' or event == 'H':
                            task.hardwareTester()
                        elif event == 'L' or event == 'l':
                            logEvent = {"logMsg":input('Enter your log message\n: ')}
                            task.DataLogger.writeToLogFile(0, 'logMsg', logEvent, time(),2)
                        elif event == 'T' or event == 't':
                            if hasattr(task, "Camera"):
                                task.Camera.setdown()
                                task.BrainLight.setdown()
                            if hasattr(task, 'LickDetector'):
                                task.LickDetector.setdown()
                            task.editSettings()
                            #response = input('Save edited settings to file?')
                            #if response [0] == 'Y' or response [0] == 'y':
                             #   task.saveSettings()
                            task.setup()
                            print("hello")
                        elif event == 'S' or event == 's':
                            task.Stimulator.settingsDict = task.Stimulator.config_user_get(task.Stimulator.settingsDict)
                            task.Stimulator.setup()
    except Exception as anError:
        print('Auto Head Fix error:' + str(anError))
        raise anError
    finally:
        task.Stimulator.quitting()
        task.HeadFixer.releaseMouse(task.tag)
        # task.HeadFixer.setPWM(0)
        for name, object in task.__dict__.items():
            if name[-5:] != "Class" and name[-4:] != "Dict" and hasattr(object, 'setdown'):
                object.setdown()
        #GPIO.output(task.ledPin, GPIO.LOW)
        #GPIO.output(task.rewardPin, GPIO.LOW)
        GPIO.cleanup()
        print('AutoHeadFix Stopped')

if __name__ == '__main__':
    main()
