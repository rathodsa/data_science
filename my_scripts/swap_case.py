
my_str = "hi hello how are you sai why do you think you are great"
new_atring = my_str.split(" ")
cap_string = []
for word in new_atring:
 print(word)
 x = word.capitalize()
 cap_string.append(x)
y = " ".join(cap_string)
print(y)
