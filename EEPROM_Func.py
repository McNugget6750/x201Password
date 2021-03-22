#   24RF08 EEPROM library, specifically for reading and writing EEPROMs of old Thinkpads
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

# (Hopefully) Complete mapping between Lenovo encoded characters and the ASCII table
# Technically, the characters aren't needed because chr(hexcode) will give you the same but this is more debuggable and human readable
encryptionMap = [[' ', 0x00, 0x00], ['0', 0x30, 0x0b], ['1', 0x31, 0x02], ['2', 0x32, 0x03], ['3', 0x33, 0x04], ['4', 0x34, 0x05], ['5', 0x35, 0x06], ['6', 0x36, 0x07], ['7', 0x37, 0x08], ['8', 0x38, 0x09], ['9', 0x39, 0x0a], [';', 0x3b, 0x27], ['a', 0x61, 0x1e], ['b', 0x62, 0x30], ['c', 0x63, 0x2e], ['d', 0x64, 0x20], ['e', 0x65, 0x12], ['f', 0x66, 0x21], ['g', 0x67, 0x22], ['h', 0x68, 0x23], ['i', 0x69, 0x17], ['j', 0x6a, 0x24], ['k', 0x6b, 0x25], ['l', 0x6c, 0x26], ['m', 0x6d, 0x32], ['n', 0x6e, 0x31], ['o', 0x6f, 0x18], ['p', 0x70, 0x19], ['q', 0x71, 0x10], ['r', 0x72, 0x13], ['s', 0x73, 0x1f], ['t', 0x74, 0x14], ['u', 0x75, 0x16], ['v', 0x76, 0x2f], ['w', 0x77, 0x11], ['x', 0x78, 0x2d], ['y', 0x79, 0x15], ['z', 0x7a, 0x2c]]

# takes an input value and encodes it into Lenovo speak if encodeDecode == 0
# and decodes it into ascii if encodeDecode == 1
# Granted, this is extremely inefficient but I'm not in a hurry. You?
def convert_value(input, encodeDecode = 0):
    if encodeDecode == 0:
        for r in encryptionMap: # look at every entry in our map to check for a match
            if input == r[1]:
                return r[2]
        print(hex(input), " not found while encoding.")
        return -1 # something went wrong, symbol not found in map
    elif encodeDecode == 1:
        for r in encryptionMap: # look at every entry in our map to check for a match
            if input == r[2]:
                return r[1]
        print(hex(input), " not found while decoding.")
        return -1 # something went wrong, symbol not found in map
    else:
        print("convert_value(input, encodeDecode = 0) needs either 0 or 1 as input for the encoding direction. You provided: ", encodeDecode)
        return -1 # something went wrong, function called incorrectly

# Reset all bytes in EEPROM back to 0x00!
################################################################################
# EXTREMELY DANGEROUS! DO NOT USE ON LIVE HARDWARE AND ESPECIALLY LAPTOPS!!!   #
################################################################################
def erase_eeprom_8(bus, address, size=256, bs=8):

    block = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    # Run through the blocks and send each block individually until all blocks sent
    for i in range(int(size / bs)):
        start = i * bs # Calculate start address for each block
        # Send 9 bytes total. 1 byte row address and 8 bytes of data
        # bus.write_i2c_block_data(address, start, block)
        
        # apparently, we have to wait a bit to not overload the bus.
        # I f-ing wonder why this is not a blocking write!!??
        sleep(0.01)

# Write data to eeprom. Again, extremely danger!
################################################################################
# EXTREMELY DANGEROUS! DO NOT USE ON LIVE HARDWARE AND ESPECIALLY LAPTOPS!!!   #
################################################################################
def write_to_eeprom_8(bus, address, data, bs=8):
    print("Writing binary file back into EEPROM, length:", len(data))
    # Check number of bytes in the data field
    b_l = len(data)
    # split data into blocks of 8 bytes
    b_c = int(ceil(b_l / float(bs))) 
    
    # Create a list or something from the data to make 8 byte chunks
    blocks = [data[bs * x:][:bs] for x in range(b_c)]
    
    printProgressBar(0, len(blocks), prefix = 'Writing EEPROM:', suffix = 'Complete', length = 50)
    # Run through the blocks and send each block individually until all blocks sent
    for i, block in enumerate(blocks):
        # Calculate start address for each block
        start = i * bs
        
        # Send 9 bytes total. 1 byte row address and 8 bytes of data
        # DO NOT USE write_block_data() - very unreliable! Bit errors en mass!
        bus.write_i2c_block_data(address, start, block)
        # print(bytes(block).hex(), end = " ")
        # print(round((b_c/10*i), 1), end = "%\n")
        
        printProgressBar(i + 1, len(blocks), prefix = 'Writing EEPROM:', suffix = 'Complete', length = 50)
        # Wait a bit to not overload the eeprom.
        sleep(0.01)
    
# Read consecutive bytes from the eeprom
def read_from_eeprom_8(bus, address, size=256):
    binary = [0] * size
    
    printProgressBar(0, size, prefix = 'Reading EEPROM:', suffix = 'Complete', length = 50)
    
    for i in range(int(size)):
        # To ensure we can actually read all 256 bytes from the EEPROM,
        # some memories like the 24RF08 require setting multiple page addresses.
        # The 24RF08 is organized in 128 byte pages that must be accessed individually 
        # or the page will simply loop.
        if i % 0x80 == 0:
            # print("setting new page at ", i)
            bus.write_byte(address, i) # write the new page address to the address counter
            sleep(0.01) # wait a bit to let the new address settle
            
        result = bus.read_byte(address)
        binary[i] = result
        printProgressBar(i + 1, size, prefix = 'Reading EEPROM:', suffix = 'Complete', length = 50)
    return binary
    
def verify_eeprom_8(data1, data2):
    newLineCounter = 0
    byteMismatch = False
    
    printProgressBar(0, len(data1), prefix = 'Verifing EEPROM:', suffix = 'Complete', length = 50)
    for i in range(len(data1)):
        if data1[i] != data2[i]:
            byteMismatch = True
            print("Mismatch at byte: " + str(i))
        
        printProgressBar(i + 1, len(data1), prefix = 'Verifing EEPROM:', suffix = 'Complete', length = 50)
    if byteMismatch == True:
        print("Verification failed!!! DO NOT POWER-CYCLE YOUR COMPUTER!!!")
    else:
        print("Verification completed. EEPROM seems good. No guarantees!")
    
def write_binary_to_file(data, filename = "binary.bin", append = 0):
    if append == 0:
        print("Writing binary to file... ", filename)
    elif append == 1:
        print("Appending binary to file... ", filename)
    # Open file to dump the EEPROM data into
    if append == 0:
        file = open(filename, "wb")
    elif append == 1:
        file = open(filename, "ab")
        
    for i in data:
        file.write(i.to_bytes(1, 'big'))
    file.close()
    
def read_binary_from_file(filename = "binary.bin", size = 256):
    binary = [0] * size
    file = open(filename, "rb")
    binary = file.read()
    file.close()
    print("Bytes read from file: " + str(len(binary)))
    return list(binary)
    
def read_pwd_from_binary(data):
    print("Extracting and translating password:", end = " ")
    for i in range(7):
        print(chr(convert_value(data[0x38 + i], 1)), end = "")
    print("")
    print("Checksum of password as read from eeprom: ", hex(data[0x38 + 7]))
    
    print("Confirmation passcode (should be the same):", end = " ")
    for i in range(7):
        print(chr(convert_value(data[0x40 + i], 1)), end = "")
    print("")
    print("Checksum of re-entered password as read from eeprom: ", hex(data[0x40 + 7]))
    
    print("Calculating own checksum:", end = " ")
    print(hex(calculate_checksum(data[0x38:(0x38 + 7)])))
    
# Given a 7 byte password, calculate the checksum for it
def calculate_checksum(password):
    value = 0
    for i in range(7):
        value += password[i]
    return value & 0xff    
    
# Create byte array from password string
def convert_password_to_byte_array(password):
    binary = [0] * 7
    for i in range(7):
        if i < len(password):
            binary[i] = ord(password[i])
        else:
            binary[i] = 0
    return binary

def write_new_password_to_binary(data, password = [0, 0, 0, 0, 0, 0, 0]):
    print("Writing and encoding new password:", end = " ")
    convertedPassword = [0] * 7
    
    for i in range(7):
        data[0x38 + i] = convert_value(password[i], 0)
        convertedPassword[i] = data[0x38 + i]
        print(chr(password[i]), end = "")
        
    checksum = calculate_checksum(convertedPassword)
    data[0x38 + 7] = checksum
    print("")
    print("Checksum added to eeprom: ", hex(data[0x38 + 7]))

    print("Writing confirmation password (must be the same):", end = " ")
    for i in range(7):
        data[0x40 + i] = convert_value(password[i], 0)
        print(chr(password[i]), end = "")
    checksum = calculate_checksum(convertedPassword)
    print("")
    print("Adding checksum to confirmation password: ", hex(checksum))
    data[0x40 + 7] = checksum
    
    return data
    
# Function to write 8 bit values to EEPROM with ############ 16 bit addresses ############
# !!!! UNTESTED !!!!
def write_to_eeprom_16(bus, address, data, size=2048, bs=8):
    # Check number of bytes in the data field
    b_l = size
    # split data into blocks of 8 bytes
    b_c = int(ceil(b_l / float(bs))) 
    
    # Create a list or something from the data to make 8 byte chunks
    blocks = [data[bs * x:][:bs] for x in range(b_c)]
    
    # Run through the blocks and send each block individually until all blocks sent
    for i, block in enumerate(blocks):
        # Calculate start address for each block
        start = i * bs
        
        # Send 9 bytes total. 1 byte row address and 8 bytes of data
        # unfortunately, SMBus doesn't seem to be able to write more than 8 bytes at a time and only to eeproms with an 8 bit address register which
        # makes it impossible to write 16 bit register addresses. The only way I can see right now is to
        # use the console commands to 
        # i2cset -y 2 ChipAddress UpperRegAddress LowerRegAddress ByteToSave_0 ByteToSave_1 ByteToSave_2 ByteToSave_3 ByteToSave_4  ByteToSave_5 ByteToSave_6 ByteToSave_7 i
        # The i indicates block data and allows writing of multiple bytes in one go.
        conCommand = "i2cset -y 2 " + hex(address) + " " + hex(((start >> 8) & 0xFF)) + " " + hex(start & 0xFF) + " " + hex(block[0]) + " " + hex(block[1]) + " " + hex(block[2]) + " " + hex(block[3]) + " " + hex(block[4]) + " " + hex(block[5]) + " " + hex(block[6]) + " " + hex(block[7])
        print(conCommand)
        
        # stream = os.popen(conCommand)
        # output = stream.read()
        # print(output)
        
        # apparently, we have to wait a bit to not overload the bus.
        # I f-ing wonder why this is not a blocking write!!??
        sleep(0.01)
    print()
    
    
    # Print iterations progress: Source https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()