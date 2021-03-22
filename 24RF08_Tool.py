#   24RF08 Reader / Writer
#   Tool to access the bios EEPROM of a laptop using a 24RF08 chip. This is typically where the supervisor password is stored.
#   The tool dumps the EEPROM, reads out the password and presents it to the user. It also allows writing a new password or removing it altogether.
#
#   Author: Timo Birnschein
#   email: timo.birnschein@microforge.de

from smbus import SMBus
from math import ceil
from time import sleep
from array import *
import numpy as np
import os
import json
import EEPROM_Func as eeprom
import GPIO as gpio
import time

menuState = "start"

while(True):
    
    if menuState == "start":
        print("Thinkpad 24RF08 EEPROM Tool (Crack your favorite laptop - hopefully without breaking it...)")
        print("-------------------------------------------------------------------------------------------")
        print("DISCLAIMER: ABSOLUTELY NO WARRANTY WILL BE PROVIDED WITH THIS SOFTWARE.")
        print("USE AT YOUR OWN RISK!! I AM NOT AND CANNOT BE MADE RESPONSIBLE FOR ANY")
        print("AND ALL DAMAGE TO YOUR SYSTEM CAUSED BY THE USE OF THIS SOFTWARE!\n")
        print("This software only works with Thinkpads that use the 24RF08 EEPROM to store bios security data.")
        print("This software has ONLY been developed and tested ONLY on my personal Lenovo Thinkpad X201 Tablet.")
        print("Chances are VERY HIGH it will not work on your machine or even break your machine! Again: USE AT YOUR OWN RISK. Enjoy :)\n")
        print("Author: Timo Birnschein - Copyright 2021\n\n")
        menuState = "restoreOrDownload"
        
    elif menuState == "restoreOrDownload":
        response = input("Please select task: restore EEPROM from file: type <restore>, or read, modify and write system EEPROM: type <modify> (default is <modify>)\n")
        if response == "restore":
            menuState = "restore"
        elif response == "modify":
            menuState = "download"
        elif response == "":
            menuState = "download"
        else:
            print("Command does not exist.")
    
    elif menuState == "restore":
        response = input("Binary file to restore / write to EEPROM (default is <eeprom.bin>)\n")
        if response == "":
            response = "eeprom.bin"
        print("Looking for file: " + response)
        if os.path.isfile(response) == True:
            print("File found. Reading binary file...")
            eepromDump = eeprom.read_binary_from_file(response)
            
            smBusNumber = input("What i2c bus / SMBus would you like to use? Default is <2>:\n")
            if smBusNumber == "":
                smBusNumber = 2
            print("Selecting I2C bus " + str(smBusNumber) + "\n")
            bus = SMBus(int(smBusNumber))
            
            menuState = "witeToEEPROM"
        else:
            print("File not found!")
    elif menuState == "download":
        smBusNumber = input("What i2c bus / SMBus would you like to use? Default is <2>:\n")
        if smBusNumber == "":
            smBusNumber = 2
        print("Selecting I2C bus " + str(smBusNumber) + "\n")
        bus = SMBus(int(smBusNumber))
        menuState = "readEEPROM"
        
    elif menuState == "readEEPROM":
        input("Press Enter to read EEPROM contents...")
        print("Reading from EEPROM...")
        # eepromDump = eeprom.read_from_eeprom_8(bus, 0x54, 256)
        # eeprom.write_binary_to_file(eepromDump, "eeprom.bin", 0)
        # eepromDump = eeprom.read_from_eeprom_8(bus, 0x55, 256)
        # eeprom.write_binary_to_file(eepromDump, "eeprom.bin", 1)
        # eepromDump = eeprom.read_from_eeprom_8(bus, 0x56, 256)
        # eeprom.write_binary_to_file(eepromDump, "eeprom.bin", 1)
        # eepromDump = eeprom.read_from_eeprom_8(bus, 0x57, 256)
        # eeprom.write_binary_to_file(eepromDump, "eeprom.bin", 1)
        eepromDump = eeprom.read_from_eeprom_8(bus, 0x57, 256)
        eeprom.write_binary_to_file(eepromDump, "eeprom.bin", 0)
        menuState = "readPasswordFromEEPROM"
        
    elif menuState == "readPasswordFromEEPROM":
        # # look at the last readout as this should contain the pass phrase
        eeprom.read_pwd_from_binary(eepromDump)
        
        print("\nThe above password might not be correct as your system might use a different encryption scheme!")
        print("If the password does not work, writing a new password also won't work! Only removing it altogether will work.")
        menuState = "createNewPassword"
        
    elif menuState == "createNewPassword":
        print("\nChoices are: remove existing password from EEPROM or write a new password to the EEPROM")
        response = input("Type <remove> or <new> without brackets and hit enter. If you just hit enter, the program will exit.\n")
            
        if response == "new":
            # Create a new password and put it back into the binary
            newPassword = input("Type a new password with a maximum of 7 (seven) symbols and use only <a-z>, <0-9>, and <;>. Do not use anything else!\nPassword: ")
            newPasswordConfirmation = input("Confirm : ")
            
            if newPasswordConfirmation != newPassword:
                print("ERROR: Both passwords do not match.")
            elif len(newPassword) > 7:
                print("you entered more than 7 symbols: " + newPassword + "\n")
                print("!!!!!!!!!!!!!!!\nOnly 7 characters will be used. This will be your new password: " + newPassword[0:7] + "\n!!!!!!!!!!!!!!!\n")
                newPassword = newPassword[0:7]
                encodedPassword = eeprom.convert_password_to_byte_array(newPassword)
                eepromDump = eeprom.write_new_password_to_binary(eepromDump, encodedPassword)
                eeprom.write_binary_to_file(eepromDump, "eeprom_mod.bin", 0)
                menuState = "witeToEEPROM"
            else:
                encodedPassword = eeprom.convert_password_to_byte_array(newPassword)
                eepromDump = eeprom.write_new_password_to_binary(eepromDump, encodedPassword)
                eeprom.write_binary_to_file(eepromDump, "eeprom_mod.bin", 0)
                menuState = "witeToEEPROM"

        elif response == "remove":
            # Alternatively, we simply delete the password from the EEPROM
            eepromDump = eeprom.write_new_password_to_binary(eepromDump)
            eeprom.write_binary_to_file(eepromDump, "eeprom_mod.bin", 0)
            menuState = "witeToEEPROM"
        else:
            print("Good bye! Come back, soon.")
            quit()
        
    elif menuState == "witeToEEPROM":
        response = input("\n\nDo you really want to write to the EEPROM of your computer?\n************** THIS MIGHT BRICK YOUR LAPTOP!!! **************\nType: <Yes I want to> and hit enter (case sensitive, no brackets!)...\n")
        # Writing to the eeprom
        if response == "Yes I want to":
            eeprom.write_to_eeprom_8(bus, 0x57, eepromDump)
            print("Reading EEPROM back for verification...")
            eepromDumpVerify = eeprom.read_from_eeprom_8(bus, 0x57, 256)
            eeprom.write_binary_to_file(eepromDumpVerify, "eeprom_verify.bin", 0)
            eeprom.verify_eeprom_8(eepromDump, eepromDumpVerify)
        else:
            print("Okey, I won't write anything...\n")
            
        menuState = "done"
        
    elif menuState == "done":
        print("\nDone. Bye.")
        quit()




# Some GPIO handling examples using my lib


# for i in range(255):
#     stream = os.popen("echo 0 > /sys/class/gpio/gpio45/value")
#     output = stream.read()
#     print(output)
#     stream = os.popen("echo 1 > /sys/class/gpio/gpio45/value")
#     output = stream.read()
#     print(output)

# print("blinking an LED")

# gpio45 = gpio.pinMode(45, "out")
# if gpio45 == -1:
#     print("Could not get GPIO configured:", str(45))
#     quit()
    
# returnVal = 0

# input("Press Enter to start...")

# for i in range(255):
#     gpio.digitalWrite(gpio45, 1)
#     returnVal = gpio.digitalRead(gpio45)
#     gpio.digitalWrite(gpio45, 0)
#     returnVal = gpio.digitalRead(gpio45)
    
# gpio.pinCleanUp(45)

# input("Press Enter to continue...")
# quit()