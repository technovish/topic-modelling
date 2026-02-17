import os
import pandas as pd


data = pd.read_excel('data/tmo_comments.xlsx')
data = data[data['Customer Feedback Filtered'] != 'Na']
data = data[data['Customer Feedback Filtered'] != 'N/a']
print(data.info())
