# https://towardsdatascience.com/learning-reinforcement-learning-reinforce-with-pytorch-5e8ad7fc7da0

import torch
from torch import nn
from torch.nn import functional as F

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Estimator(nn.Module):

    NHIDDEN = 128

    def __init__(self, ninput, noutput):
        self.input = nn.Linear(ninput, self.NHIDDEN)
        self.output = nn.Linear(self.NHIDDEN, noutput)

    def forward(self, x):
        x = x.to(device)
        x = F.relu(self.input(x))
        return F.softmax(self.output(x))


def discount_rewards(rewards, gamma=0.99):
    r = np.array([gamma**i * rewards[i] for i in range(len(rewards))])
    # Reverse the array direction for cumsum and then
    # revert back to the original order
    r = r[::-1].cumsum()[::-1]
    return r - r.mean()


def reinforce(
    env, policy_estimator, num_episodes=2000, batch_size=10, gamma=0.99
):  # Set up lists to hold results
    total_rewards = []
    batch_rewards = []
    batch_actions = []
    batch_states = []
    batch_counter = 1

    # Define optimizer
    optimizer = optim.Adam(policy_estimator.network.parameters(), lr=0.01)

    action_space = np.arange(env.action_space.n)
    ep = 0
    while ep < num_episodes:
        s_0 = env.reset()
        states = []
        rewards = []
        actions = []
        done = False
        while done == False:
            # Get actions and convert to numpy array
            action_probs = policy_estimator.predict(s_0).detach().numpy()
            action = np.random.choice(action_space, p=action_probs)
            s_1, r, done, _ = env.step(action)

            states.append(s_0)
            rewards.append(r)
            actions.append(action)
            s_0 = s_1

            # If done, batch data
            if done:
                batch_rewards.extend(discount_rewards(rewards, gamma))
                batch_states.extend(states)
                batch_actions.extend(actions)
                batch_counter += 1
                total_rewards.append(sum(rewards))

                # If batch is complete, update network
                if batch_counter == batch_size:
                    optimizer.zero_grad()
                    state_tensor = torch.FloatTensor(batch_states)
                    reward_tensor = torch.FloatTensor(batch_rewards)
                    # Actions are used as indices, must be
                    # LongTensor
                    action_tensor = torch.LongTensor(batch_actions)

                    # Calculate loss
                    logprob = torch.log(policy_estimator.predict(state_tensor))
                    selected_logprobs = (
                        reward_tensor
                        * torch.gather(logprob, 1, action_tensor).squeeze()
                    )
                    loss = -selected_logprobs.mean()

                    # Calculate gradients
                    loss.backward()
                    # Apply gradients
                    optimizer.step()

                    batch_rewards = []
                    batch_actions = []
                    batch_states = []
                    batch_counter = 1

                avg_rewards = np.mean(total_rewards[-100:])
                # Print running average
                print(
                    "\rEp: {} Average of last 100:"
                    + "{:.2f}".format(ep + 1, avg_rewards),
                    end="",
                )
                ep += 1

    return total_rewards
