
from tabulate import tabulate

#my_table = {"Name": ['sai','Uday'], "Surname": ['Rathod','Chavan']}
my_table = [['First Name','LastName','EmpId'], ['SaiKrishna','Rathod','1432331'],['Indal','Chavan','45234']]
print(tabulate(my_table, headers='firstrow'))
