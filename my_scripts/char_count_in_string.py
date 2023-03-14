my_string = "aaaabbbccccdddd"
x = list(my_string)
counts = dict()
for key in x:
    if key in counts:
        counts[key] += 1
    else:
        counts[key] = 1

x = counts.keys()
y = counts.values()
z = map(x,y)
print(type(z))
count = 0
for i in range(0,len(my_string)):
    if my_string[i] != "":
        count = count + 1

print("The total number of the characters in the string are :" + ' ' + str(count))



