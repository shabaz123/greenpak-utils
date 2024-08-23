# gp_prog.py
# rev 1 - shabaz - August 2024
# This program is used to communicate with the Renesas SLG47004V GreenPAK device
# To use, program a Pi Pico with the easy_i2c_adapter.uf2 firmware
# (you can hold down the BOOTSEL button on the Pico, insert the USB cable to the PC,
# and then drag and drop the uf2 file), and then connect the Pico to the GreenPAK
# device using the I2C pins (SDA = GPIO14, SCL = GPIO15) GND, and also 3.3V if required).
# Then, this program will detect the Pico and communicate with the GreenPAK device.

import easy_interface as adapter
from easy_interface import print_data
import dickens
import sys

# the I2C address is 7 bits, of which the 4 most significant bits are
# 0001 by default, unless the GreenPAK device has been programmed otherwise.
# That means the base address is 0001000 = 0x08. The three least significant
# bits define the type of memory.
base_addr = 0x08
eeprom_space = base_addr | 0x03
nvm_space = base_addr | 0x02
config_space = base_addr | 0x00

data_buf=[]
fname_provided = False

fname = "blinky.txt"
if len(sys.argv) > 1:
    fname = sys.argv[1]
    fname_provided = True
1
# initialize the USB-to-I2C adapter
result = adapter.init()
if result is False:
    print("Error initializing adapter, is it plugged in? Exiting.")
    exit()

# read the GreenPAK bit file with name fname, and return the data as a list of bytes
def read_gp_file(fname):
    # check if the file exists
    try:
        f = open(fname, "r")
        f.close()
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found!")
        exit()
    f = open(fname, "r")
    buf = []
    bit_count = 0
    byte_val = 0
    for line in f:
        if bit_count == 0:
            byte_val = 0
        if line[0].isdigit():  # every interesting line starts with a digit
            words = line.split("\t\t")  # columns are separated by two tabs
            byte_val >>= 1
            if words[1] == "1":
                byte_val |= 0x80
            else:
                byte_val &= 0x7f
            bit_count += 1
            if bit_count == 8:
                buf.append(byte_val)
                bit_count = 0
    f.close()
    if len(buf) != 256:
        print(f"Error: File '{fname}' does not contain 256 bytes!")
        exit()
    print(f"Data from file '{fname}' in hex format:")
    print_data(buf)
    return buf

# this function can be used to scan the I2C bus and
# returns the address of the first device found
def find_address():
    print("Finding I2C devices...")
    for addr in range(1, 128):
        retval = adapter.i2c_try_address(addr)
        if retval is True:
            print(f"Found an I2C device at address 0x{addr:02x}")
            return addr
    print("No I2C devices found!")
    exit()


# read the entire GreenPAK EEPROM, returns a list of 256 bytes
def read_eeprom():
    print("Reading EEPROM...")
    buf = []
    bar_seq = ['|', '/', '-', '\\']
    for i in range(0, 256, 16):
        print(f"\r{bar_seq[i//16 % 4]}", end='')
        retval = adapter.i2c_write(eeprom_space, i, [], hold=1)
        pagebuf = adapter.i2c_read(eeprom_space, 16)
        if pagebuf is None:
            print("Error reading I2C data")
            exit()
        else:
            buf += pagebuf
    print("\r", end='')
    print_data(buf)
    return buf

# write the GreenPAK EEPROM (256 bytes)
def write_eeprom(data):
    print("Writing 256 bytes to the eeprom...")
    bar_seq = ['|', '/', '-', '\\']
    # we write 16 bytes (i.e. a page) at a time, total 256 bytes
    for i in range(0, 256, 16):
        print(f"\r{bar_seq[i // 16 % 4]}", end='')
        retval = adapter.i2c_write(eeprom_space, i, data[i:i+16])
        if retval is False:
            print("\r", end='')
            print("Error writing I2C data")
            exit()
    print("\r", end='')

# Write a buffer of bytes to a file as raw bytes
def write_raw_file(data, fname):
    f = open(fname, "wb")
    for b in data:
        f.write(bytes([b]))
    f.close()

# Read a file of raw bytes and return the data as a list of bytes
def read_raw_file(fname):
    try:
        f = open(fname, "r")
        f.close()
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found!")
        exit()
    f = open(fname, "rb")
    buf = []
    bytecount = 0
    while True:
        byte = f.read(1)
        if not byte:
            break
        bytecount += 1
        buf.append(byte[0])
    f.close()
    if bytecount != 256:
        print(f"Error: File '{fname}' does not contain exactly 256 bytes!")
    else:
        print(f"Data from file '{fname}' in hex format:")
        print_data(buf)
    return buf

# write a buffer of bytes to a file in GreenPAK bit format
def write_gp_file(data, fname):
    f = open(fname, "w")
    f.write("index\t\tvalue\t\tcomment\n")
    for i in range(256):
        byte_val = data[i]
        for j in range(8):
            # write LSB first
            bit = (byte_val >> j) & 1
            f.write(f"{i*8+j}\t\t{bit}\t\t//\n")
    f.close()

# erase one page (16 bytes) of the GreenPAK EEPROM
def erase_eeprom_page(page):
    ersr_reg = 0xe3
    ersr_byte = 0xc0 | page | 0x10
    retval = adapter.i2c_write(config_space, ersr_reg, [ersr_byte])

# erase the entire GreenPAK EEPROM
def erase_eeprom():
    print("Erasing entire eeprom...")
    for i in range(16):
        erase_eeprom_page(i)

# read the entire GreenPAK NVM, returns a list of 256 bytes
def read_nvm():
    print("Reading NVM...")
    buf = []
    bar_seq = ['|', '/', '-', '\\']
    for i in range(0, 256, 16):
        print(f"\r{bar_seq[i//16 % 4]}", end='')
        retval = adapter.i2c_write(nvm_space, i, [], hold=1)
        pagebuf = adapter.i2c_read(nvm_space, 16)
        if pagebuf is None:
            print("Error reading I2C data")
            exit()
        else:
            buf += pagebuf
    print("\r", end='')
    print_data(buf)
    return buf

# write the GreenPAK NVM (256 bytes)
def write_nvm(data):
    print("Writing 256 bytes to the NVM...")
    bar_seq = ['|', '/', '-', '\\']
    # we write 16 bytes (i.e. a page) at a time, total 256 bytes
    for i in range(0, 256, 16):
        print(f"\r{bar_seq[i // 16 % 4]}", end='')
        retval = adapter.i2c_write(nvm_space, i, data[i:i+16])
        if retval is False:
            print("\r", end='')
            print("Error writing I2C data")
            exit()
    print("\r", end='')

# erase one page (16 bytes) of the GreenPAK NVM
def erase_nvm_page(page):
    ersr_reg = 0xe3
    ersr_byte = 0xc0 | page
    retval = adapter.i2c_write(config_space, ersr_reg, [ersr_byte])

# erase the entire GreenPAK NVM
def erase_nvm():
    print("Erasing NVM...")
    for i in range(16):
        erase_nvm_page(i)


def print_menu():
    print("*** Menu ***")
    print("GreenPAK<->Local Buffer device operations:")
    print("1. Read EEPROM into buffer")
    print("2. Write buffer to EEPROM")
    print("3. Read NVM into buffer")
    print("4. Write buffer to NVM")
    print("File<->Local Buffer operations:")
    print("5. Retrieve GreenPAK bit file into buffer")
    print("6. Store buffer to GreenPAK bit file")
    print("7. Retrieve Raw Bytes File into buffer")
    print("8. Store buffer to Raw Bytes File")
    print("9. Retrieve Dickens content into buffer")
    print("Enter choice (1-9)")

def get_choice_and_execute():
    global data_buf
    print(">", end='')
    choice = input()
    if choice == '1':  # read EEPROM
        data_buf = read_eeprom()
    elif choice == '2':  # write EEPROM
        print("Are you sure you want to write to the EEPROM? (y/n)")
        choice = input()
        if choice == 'y':
            erase_eeprom()
            write_eeprom(data_buf)
        else:
            print("Aborted.")
    elif choice == '3':  # read NVM
        data_buf = read_nvm()
    elif choice == '4':  # write NVM
        print("Are you sure you want to write to the NVM? (y/n)")
        choice = input()
        if choice == 'y':
            erase_nvm()
            write_nvm(data_buf)
        else:
            print("Aborted.")
    elif choice == '5':  # read GreenPAK bit file
        # get file name if no file name is provided
        if not fname_provided:
            print("Enter the GreenPAK bit file name to read (e.g. blinky.txt):")
            fname = input()
        data_buf = read_gp_file(fname)
    elif choice == '6':  # store to GreenPAK bit file
        print("Enter the GreenPAK bit file name to create:")
        outfname = input()
        write_gp_file(data_buf, outfname)
    elif choice == '7':  # read raw bytes file
        print("Enter the raw bytes file name to read (e.g. rawbytes.bin):")
        rawfname = input()
        data_buf = read_raw_file(rawfname)
    elif choice == '8':  # store to raw bytes file
        print("Enter the raw bytes file name to create:")
        outfname = input()
        write_raw_file(data_buf, outfname)
    elif choice == '9':
        data_buf = dickens.get_dickens(256)
        print("Random Dickens content:")
        print_data(data_buf)
    else:
        print("Invalid choice, try again.")

def print_banner():
    print("  _____ _____  ______ ______ _   _ _____        _  __")
    print(" / ____|  __ \|  ____|  ____| \ | |  __ \ /\   | |/ /")
    print("| |  __| |__) | |__  | |__  |  \| | |__) /  \  | ' / ")
    print("| | |_ |  _  /|  __| |  __| | . ` |  ___/ /\ \ |  <  ")
    print("| |__| | | \ \| |____| |____| |\  | |  / ____ \| . \ ")
    print(" \_____|_|  \_\______|______|_| \_|_| /_/    \_\_|\_\ ")
    print(" ")

def main():
    print_banner()
    while True:
        print_menu()
        get_choice_and_execute()


if __name__ == "__main__":
    main()

