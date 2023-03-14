# if __name__ == '__main__':
#     all_names = []
#     all_scores = []
#     for i in range(int(input())):
#         names = input()
#         scores = float(input())
#         all_names.append(names)
#         all_scores.append([names,scores])
#         sorted_scores = sorted(list(set([x[1] for x in all_scores])))
all_scores = [['Sai', 12.0], ['krish', 23.0], ['vinod', 45.0], ['ud', 23.0], ['van', 56.0]]
# for x in all_scores:
#     print(x[1])
#     print(sorted(list(set(x[1]))))
print(sorted(set([x[1] for x in all_scores])))
sorted_score = sorted(set([x[1] for x in all_scores]))
second_lowest = sorted_score[1]
print(second_lowest)

low_initial_list = []
for student in all_scores:
   if second_lowest == student[1]:
      low_initial_list.append(student[0])
print(low_initial_list)

for item in sorted(low_initial_list):
   print(item)



