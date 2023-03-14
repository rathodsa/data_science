X = [ 1, 2, 3]
print(type(X))
Y = [ 3, 5, 6 ]
Z = []
for x in X:
     for y in Y:
          Z[x][y] = X[x][y] + Y[x][y]

for s in Z:
     print(s)
     

