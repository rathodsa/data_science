import openpyxl
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.chart import BarChart, Reference
import string

excel_file = pd.read_excel('/Users/sairatho/OKVM/Superstore.xls')
my_data = excel_file[['City','Country','State','Region']]
#print(type(my_data))
report_table = excel_file.pivot_table(index='City',columns='Region', values='Sales',aggfunc='sum').round(0)
print(report_table)


print("")
