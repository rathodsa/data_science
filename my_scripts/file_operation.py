

with open("my.txt", "r") as fh:
        for line in fh.readlines():
                print(line[0])       