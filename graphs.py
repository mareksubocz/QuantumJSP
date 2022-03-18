import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

df = pd.read_csv('./JSP_data_2.csv', index_col=[0])
df_pyqubo = df[df['version'] == 'pyqubo']
# px.bar(df.groupby('max_task_time')['num_feasible'].mean(),
#        title='Number of feasible solutions depending on max task time').show()
px.histogram(df.groupby('num_feasible')['mean_task_time'].mean(),
       title='Number of feasible solutions depending on mean task time').show()
# sns.barplot(df.groupby('mean_task_time')['num_feasible'].mean())
# plt.title('Number of feasible solutions depending on mean task time')
# plt.show()
