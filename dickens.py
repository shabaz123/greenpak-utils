# dickens.py
# shabaz - rev 1 - august 2024
# this program is used to retrieve bytes of text from a book dickens.txt

import random

# only return content from these line ranges
startline = 178
endline = 3471

def get_linenum():
    return random.randint(startline, endline)

def get_dickens(num_bytes):
    linenum = get_linenum()
    buf_len = 0
    buf = []
    finished = 0
    # open the file
    f = open("dickens.txt", encoding="utf8")
    # read the file
    i = 1
    for i in range(1, endline):
        line = f.readline()
        if i >= linenum:
            # read the line
            for c in line:
                buf.append(ord(c))
                buf_len += 1
                if buf_len == num_bytes:
                    finished = 1
                    break
            if finished == 1:
                break
            if i == endline:
                # close the file and reopn it
                f.close()
                f = open("dickens.txt", "r")
                linenum = startline
                i = 0
        i += 1
    f.close()
    return buf



