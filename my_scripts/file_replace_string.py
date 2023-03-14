# search_string = 'Sai'
# replace_string = 'Uday'
# with open('/Users/sairatho/my_HR_scripts/myname.txt', 'r') as fhand:
#     data = fhand.read()
#     print(data)
#     data = data.replace(search_string, replace_string)
# with open('/Users/sairatho/my_HR_scripts/myname.txt', 'w') as fhand:
#     fhand.write(data)
#     # print(data)
search_string = "cache"
my_req_result = []
with open('/Users/sairatho/my_HR_scripts/myname.txt', 'r') as fhand:
    my_required_lines = fhand.readlines()
    for line in my_required_lines:
        if search_string in line:
            my_req_result.append(line)
print(len(my_req_result))


