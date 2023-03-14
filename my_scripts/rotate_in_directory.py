my_test_lst = [['Harry', 37.21], ['Berry', 37.21], ['Tina', 37.2], ['Akriti', 41], ['Harsh', 39]]
i = 0
j = 1
my_new_list = list()
for i in range(0, len(my_test_lst)):
    add_content = my_test_lst[i][j]
    my_new_list.append(add_content)
print(my_new_list)
for i in range(0,len(my_new_list)):
    if my_new_list[i] > my_new_list[1]:
        print(f"{my_new_list[0]} is bigger")




