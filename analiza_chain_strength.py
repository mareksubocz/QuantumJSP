import csv
import matplotlib.pyplot as plt
import pandas as pd

def srednie():
    with open('posortowane.csv') as file:
        reader = csv.reader(file, delimiter=',')
        xs = []
        ys = []
        current = 0
        suma = 0
        quantity = 0
        mini = 9999999
        maxi = -1
        for row in reader:
            if float(row[0]) == current:
                suma += int(row[4])
                mini = min(mini, int(row[4]))
                maxi = max(maxi, int(row[4]))
                quantity += 1
            else:
                if quantity > 0:
                    ys.append(suma / quantity)
                    xs.append(current)
                quantity = 1
                current = float(row[0])
                suma = int(row[4])
            if float(row[0]) > 100:
                break

        plt.plot(xs, ys)
        plt.show()

def use_pandas(path):
    # chain strength, not found, incorrect, num of reads, 5, 6, 7, 8, 9 
    df = pd.read_csv(path)
    grupa = df.groupby('chain strength')
    print(grupa.mean())
    grupa.mean().to_csv('mean.csv')

def plot_with_pandas(path):
    fig, ax = plt.subplots()
    df = pd.read_csv(path)
    grupa = df.groupby('chain strength').mean()
    print(grupa.iloc[:-8])
    # ax = grupa.iloc[:-8].plot(y=5, kind='line', legend=None)
    grupa.iloc[:-8].plot(ax=ax)
    ax.set_ylabel("number of solutions of length")
    plt.show()

if __name__ == "__main__":
    # use_pandas('wyniki.csv')
    plot_with_pandas('wyniki.csv')
