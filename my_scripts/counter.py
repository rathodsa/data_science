test_string = "aaaabbbbccccdddddeeeee"
counts = dict()
for letter in test_string:
    if letter in counts:
        counts[letter] += 1
    else:
        counts[letter] = 1
print(counts)
counts.get(a, default)
my_new = ""
for i,j in counts.items():
    my_new += str(i)
    my_new += str(j)
print(my_new)

