from utils.path import DATA_PATH
from model4FL.mnist import *
from torchvision import datasets
from torchvision.transforms import ToTensor
import torch
from rich.progress import Progress
import pytest

isdownloaded = not (DATA_PATH.exists())
mnist_dataset = {}
mnist_dataset["training"] = datasets.MNIST(
    root="data", train=True, download=isdownloaded, transform=ToTensor()
)
mnist_dataset["test"] = datasets.MNIST(root="data", train=False, transform=ToTensor())

batch_size = 64
trainloader = torch.utils.data.DataLoader(
    mnist_dataset["training"], batch_size=batch_size, shuffle=True, num_workers=2
)

testloader = torch.utils.data.DataLoader(
    mnist_dataset["test"], batch_size=batch_size, shuffle=False, num_workers=2
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
nclasses = len(mnist_dataset["training"].classes)
model = Model(nclasses).to(device)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def test_forward():
    sample, _ = mnist_dataset["training"][0]
    model(sample.unsqueeze(0))


def test_loss():
    i, (sample, label) = next(enumerate(trainloader))
    prediction = model(sample)
    criterion = extras["criterion"]()

    loss = criterion(prediction, label.to(device))


def test_backpropagation():
    i, (samples, labels) = next(enumerate(trainloader))
    prediction = model(samples)
    optimizer = extras["optimizer"](model.parameters())

    criterion = extras["criterion"]()
    loss = criterion(prediction, labels.to(device))

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()


@pytest.mark.slow
def test_train():
    num_epochs = 5
    optimizer = extras["optimizer"](model.parameters())
    criterion = extras["criterion"]()

    size = len(mnist_dataset["training"])
    with Progress(auto_refresh=False) as progress:
        nsteps = size * num_epochs // batch_size
        task = progress.add_task("Training ...", total=nsteps)
        for epoch in range(num_epochs):
            correct = 0
            total = 0
            for i, (samples, labels) in enumerate(trainloader):
                predictions = model(samples)
                loss = criterion(predictions, labels.to(device))

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                _, predicted = torch.max(predictions.data, 1)
                total += labels.size(0)
                correct += (predicted == labels.to(device)).sum().item()

                progress.advance(task)
                progress.refresh()

            accuracy = 100 * correct / total

    assert accuracy > 90
