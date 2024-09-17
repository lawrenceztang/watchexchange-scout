import os
import random
from os import listdir
from torch.utils.data import Dataset, DataLoader, random_split
from torch import nn
import torch.nn.functional as F
import torch
import torch.optim as optim
import math
import numpy as np

def modify_line(line):
    return line.replace("]", " ").replace("[", " ").lower()

class WordsDataset(Dataset):

    def get_words(self, data):
        l = ((data == 1.).nonzero(as_tuple=True)[0])
        return [self.set[i] for i in l]

    def standardize(self, num):
        return (num - self.mean) / self.std

    def unstandardize(self, num):
        return num * self.std + self.mean

    def __init__(self, root_dir, transform=None):
        self.set = set()
        self.files = os.listdir(root_dir)
        self.files = [root_dir + file for file in self.files]
        self.max_price = 10000.
        self.outputs = []
        for file in self.files[:]:
            f = open(file)
            line = modify_line(f.readline())
            num = float(f.readline())
            if num > self.max_price:
                self.files.remove(file)
                continue
            self.outputs.append(num)
            f.close()
            for char in line.split(" "):
                if char not in self.set:
                    self.set.add(char)
        self.set = list(self.set)
        self.dict = {}
        for i, word in enumerate(self.set):
            self.dict[word] = i
        self.length = len(self.outputs)
        self.std = np.std(self.outputs)
        self.mean = np.mean(self.outputs)
        self.outputs = [torch.tensor([self.standardize(e)], dtype=torch.float) for e in self.outputs]

        self.inputs = []
        for file in self.files[:]:
            f = open(file)
            l = [0.] * len(self.set)
            line = modify_line(f.readline())
            chars = line.split(" ")
            for char in chars:
                if char in self.dict:
                    l[self.dict[char]] = 1.
            self.inputs.append(torch.tensor(l))

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        return [self.inputs[idx], self.outputs[idx]]

class Net(nn.Module):
    def __init__(self, len):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(len, 1000)
        self.fc2 = nn.Linear(1000, 1)

    def forward(self, x):
        x = self.fc1(x)
        m = nn.ReLU()
        x = m(x)
        x = self.fc2(x)
        return x

num_epochs = 10000
batch_size = 800

dataset = WordsDataset("simple_data/1/")
train_set, val_set = random_split(dataset, [int(len(dataset) * .9), int(math.ceil(len(dataset) * .1))])
dataloader = DataLoader(train_set, shuffle=True, batch_size=len(train_set))
val_loader = DataLoader(val_set, batch_size=len(val_set))
net = Net(len(dataset.dict))
criterion = nn.MSELoss()
optimizer = optim.SGD(net.parameters(), lr=.04, momentum=0.9)

for epoch in range(num_epochs):  # loop over the dataset multiple times

    running_loss = 0.0
    for i, data in enumerate(dataloader, 0):
        # get the inputs; data is a list of [inputs, labels]
        inputs, labels = data

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()

    val_data = next(iter(val_loader))
    y_pred = net(val_data[0])
    val_loss = criterion(y_pred, val_data[1])

    print('[epoch %d] loss: %.3f validation loss: %.3f' %
          (epoch + 1, running_loss / len(dataloader), val_loss))
    running_loss = 0.0

print('Finished Training')