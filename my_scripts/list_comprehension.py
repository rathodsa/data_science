n_list = [1,2,3,[4,5,6],[9,5,6],6,7]
flatten_list = []
for item in n_list:
	if type(item) == 'list':
		for i in item:
			print(item)
	else:
		print(item)