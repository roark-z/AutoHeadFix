   #! /usr/bin/python3
#-*-coding: utf-8 -*-

"""
> Last modified:
2022/10/17 by Roark Zhang - update to new adafruit library

> uses PCA9685 code from AdaFruit, install as follows

sudo pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py

sudo pip3 install adafruit-circuitpython-busdevice
sudo pip3 install adafruit-circuitpython-register
sudo pip3 install adafruit-circuitpython-pca9685

"""

# Import the PCA9685 module.
from board import SCL, SDA
import busio
import adafruit_pca9685
from adafruit_motor import servo
from AHF_HeadFixer_PWM import AHF_HeadFixer_PWM

class AHF_HeadFixer_PWM_PCA9685(AHF_HeadFixer_PWM):
    """
    inherits from AHF_HeadFixer_PWM
    """
    defaultAddress = 0x40
    
    @staticmethod
    def about():
        return 'PCA9685 servo driver over i2c controls a servo motor to push head bar'


    @staticmethod
    def config_user_get(starterDict = {}):
        starterDict.update(AHF_HeadFixer_PWM.config_user_get(starterDict))
        servoAddress = starterDict.get('servoAddress', AHF_HeadFixer_PWM_PCA9685.defaultAddress)
        response = input('Enter Servo I2C Address, in Hexadecimal, currently 0x%x: ' % servoAddress)
        if response != '':
            servoAddress = int(response, 16)
        starterDict.update({'servoAddress' : servoAddress})
        return starterDict


    def setup(self):
        super().setup()
        self.servoAddress = self.settingsDict.get('servoAddress')
        i2c_bus = busio.I2C(SCL, SDA)
        hasFixer = True
        try:
            self.PCA9685 = adafruit_pca9685.PCA9685(i2c_bus, address=self.servoAddress)
            # self.PCA9685.set_pwm_freq(90) # 40-1000Hz
            self.PCA9685.frequency = 90
            self._servo = servo.Servo(self.PCA9685.channels[0])
            self.setPWM(self.servoReleasedPosition)
        except Exception as e:
            print(str(e))
            hasFixer = False
        return hasFixer

    def setdown(self):
        self.PCA9685.deinit()

    def setPWM(self, servoPosition):
        clipped = np.clip(servoPosition,0, 180)
        self._servo.angle = clipped
        # self.PCA9685.set_pwm(0, 0, servoPosition)


