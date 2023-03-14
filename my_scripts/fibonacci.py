#
# num = int(input())
# series = [0,1]
# for i in range(num+1):
#     x = series[i] + series[i+1]
#     series.append(x)
# print(series)

def get_word_count(my_string):
    words = my_string.split(" ")
    word_counts = {}
    letter_counts = {}
    for word in words:
        if word in word_counts:
            word_counts[word] += 1
            for letter in word:
                if letter in letter_counts:
                    letter_counts[letter] += 1
                else:
                    letter_counts[letter] = 1
        else:
            word_counts[word] = 1
            for letter in word:
                if letter in letter_counts:
                    letter_counts[letter] += 1
                else:
                    letter_counts[letter] = 1
    return letter_counts

target_string = "Hi sai ow are you sai how the hell and hell"
my_count = get_word_count(target_string)
print(my_count)




