
if __name__ == '__main__':
    n = int(input())
    student_marks = {}
    for _ in range(n):
        name, *line = input().split()
        print(name, line)
        scores = list(map(float, line))
        student_marks[name] = scores
student_averages = {}
for name, score in student_marks.items():
    average_marks = sum(score) / len(score)
    student_averages[name] = ("%.2f" % average_marks)
query_name = input()
print(student_averages.get(query_name))


