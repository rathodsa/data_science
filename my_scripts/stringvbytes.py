


def main():
    b = bytes([0x41,0x42,0x43])
    print(b)
    s = "This is my advanced string"
    print(s)
    print(b.decode('utf-8')+s)
    s1 = s.encode('utf-8')
    print(b+s1)
if __name__ == '__main__':
    main()    