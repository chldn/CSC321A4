"""
Minimal character-level Vanilla RNN model. Written by Andrej Karpathy (@karpathy)
BSD License
"""
import numpy as np
import cPickle as pickle

import numpy as np

a = np.load(open("char-rnn-snapshot.npz"))
Wxh = a["Wxh"] 
Whh = a["Whh"]
Why = a["Why"]
bh = a["bh"]
by = a["by"]
mWxh, mWhh, mWhy = a["mWxh"], a["mWhh"], a["mWhy"]
mbh, mby = a["mbh"], a["mby"]
chars, data_size, vocab_size, char_to_ix, ix_to_char = a["chars"].tolist(), a["data_size"].tolist(), a["vocab_size"].tolist(), a["char_to_ix"].tolist(), a["ix_to_char"].tolist()


# data I/O
data = open('input.txt', 'r').read() # should be simple plain text file
chars = list(set(data))
#data_size, vocab_size = len(data), len(chars)
print 'data has %d characters, %d unique.' % (data_size, vocab_size)
#char_to_ix = { ch:i for i,ch in enumerate(chars) }
#ix_to_char = { i:ch for i,ch in enumerate(chars) }

# hyperparameters
hidden_size = 250 # size of hidden layer of neurons
seq_length = 25 # number of steps to unroll the RNN for
learning_rate = 1e-1

# model parameters
#Wxh = np.random.randn(hidden_size, vocab_size)*0.01 # input to hidden
#Whh = np.random.randn(hidden_size, hidden_size)*0.01 # hidden to hidden
#Why = np.random.randn(vocab_size, hidden_size)*0.01 # hidden to output
#bh = np.zeros((hidden_size, 1)) # hidden bias
#by = np.zeros((vocab_size, 1)) # output bias

def lossFun(inputs, targets, hprev):
  """
  inputs,targets are both list of integers.
  hprev is Hx1 array of initial hidden state
  returns the loss, gradients on model parameters, and last hidden state
  """
  xs, hs, ys, ps = {}, {}, {}, {}
  hs[-1] = np.copy(hprev)
  loss = 0
  temp = 0.9
  alpha = 1./temp
  # forward pass
  for t in xrange(len(inputs)):
    xs[t] = np.zeros((vocab_size,1)) # encode in 1-of-k representation
    xs[t][inputs[t]] = 1
    hs[t] = np.tanh(np.dot(Wxh, xs[t]) + np.dot(Whh, hs[t-1]) + bh) # hidden state
    ys[t] = np.dot(Why, hs[t]) + by # unnormalized log probabilities for next chars
    ps[t] = np.exp((alpha)*ys[t]) / np.sum(np.exp((alpha)*ys[t])) # probabilities for next chars
    loss += -np.log(ps[t][targets[t],0]) # softmax (cross-entropy loss)
  # backward pass: compute gradients going backwards

  dWxh, dWhh, dWhy = np.zeros_like(Wxh), np.zeros_like(Whh), np.zeros_like(Why)
  dbh, dby = np.zeros_like(bh), np.zeros_like(by)
  dhnext = np.zeros_like(hs[0])
  for t in reversed(xrange(len(inputs))):
    dy = np.copy(ps[t])
    dy[targets[t]] -= 1 # backprop into y
    dWhy += np.dot(dy, hs[t].T)
    dby += dy
    dh = np.dot(Why.T, dy) + dhnext # backprop into h
    dhraw = (1 - hs[t] * hs[t]) * dh # backprop through tanh nonlinearity
    dbh += dhraw
    dWxh += np.dot(dhraw, xs[t].T)
    dWhh += np.dot(dhraw, hs[t-1].T)
    dhnext = np.dot(Whh.T, dhraw)
  for dparam in [dWxh, dWhh, dWhy, dbh, dby]:
    np.clip(dparam, -5, 5, out=dparam) # clip to mitigate exploding gradients
  return loss, dWxh, dWhh, dWhy, dbh, dby, hs[len(inputs)-1]

def sample(h, seed_ix, n):
  """ 
  sample a sequence of integers from the model 
  h is memory state, seed_ix is seed letter for first time step
  """

  x = np.zeros((vocab_size, 1))
  x[seed_ix] = 1
  ixes = []
  temp = 1
  print("Temperature: ", temp)
  alpha = 1./temp
  for t in xrange(n):
    h = np.tanh(np.dot(Wxh, x) + np.dot(Whh, h) + bh)
    y = np.dot(Why, h) + by
    p = np.exp((alpha)*y) / np.sum(np.exp((alpha)*y))
    ix = np.random.choice(range(vocab_size), p=p.ravel())
    x = np.zeros((vocab_size, 1))
    x[ix] = 1
    ixes.append(ix)
    # if ':' == ix_to_char[ixes[-2]]:
    #   print np.argmax(h)
  return ixes

def get_key_weights(x, Wxh, h, Why):
  # get max 10 indices of (Wxh*x) from input x = ':'OHE
  wxh_max_idxes = (np.abs(np.dot(Wxh, x)).T).argsort()[0][-10:] # array([170, 185, 114,  95, 187, 100, 208,  43,  73, 242])
  wxh_maxes = {i:Wxh[:,9][i] for i in wxh_max_idxes} # gets values of Wxh 
  # wxh_maxes = {100: 4.8291898683713592, 73: -5.0570966540231206, 170: -4.1043252012334079, 43: -5.0123830835306142, 242: -7.8725814225256752, 208: -4.8843477232065506, 114: 4.2650028601838068, 185: 4.1733393419101619, 187: 4.5475188498323647, 95: -4.49315921659234}
  
  #get max 10 indices of (Why*h) going into the '\n' character
  newline_Ws = Why[0,:].reshape((250,1)).T
  nlWs_h = (newline_Ws *h.T)
  nlWsh_max_idxes = (np.abs(nlWs_h)).argsort()[0][-10:]  # array([143, 170, 114, 185, 108, 166, 187, 210,  73, 100])
  nlWsh_maxes = {i:(Why[0,:][i], (Why[0,:][i]*h[i])[0])  for i in nlWsh_max_idxes} 
  # nlWsh_maxes = {100: 2.6727123603897232, 166: -1.7058694844876847, 73: -2.244658975368536, 170: -1.2923192028088104, 108: 1.4269114887069017, 210: -2.1593540170222068, 143: -1.8318692082250172, 114: 1.3415086080491887, 185: 1.3977953774511229, 187: 2.0301543133308124}
  
  intersxn = {}
  for key in wxh_maxes:
    if key in nlWsh_maxes:
      if (wxh_maxes[key]*nlWsh_maxes[key][1] > 0):
        intersxn[key] = (wxh_maxes[key], nlWsh_maxes[key],)
  
  return intersxn
  
  
  
  
  

def sample_starter(starter, h, seed_ix, n):
  '''
  Given a starter string starter, complete the string
  h is memory state, seed_ix is seed letter for first time step
  '''
  starter_ixes = []
  for char in starter:
    starter_ixes.append(char_to_ix[char])
  x = np.zeros((vocab_size, 1))
  x[starter_ixes[0]] = 1
  ixes = [starter_ixes[0]]
  temp = 0.8
  alpha = 1./temp
  print "Temperature: ", temp

  #   
  # for t in range(len(starter_ixes)-1):    
  #   h = np.tanh(np.dot(Wxh, x) + np.dot(Whh, h) + bh)
  #   y = np.dot(Why, h) + by
  #   p = np.exp((alpha)*y) / np.sum(np.exp((alpha)*y))
  #   x = np.zeros((vocab_size, 1))
  #   x[ix] = 1
  #   ixes.append(ix)
  
  for t in xrange(n):
    h = np.tanh(np.dot(Wxh, x) + np.dot(Whh, h) + bh)
    y = np.dot(Why, h) + by
    p = np.exp((alpha)*y) / np.sum(np.exp((alpha)*y))
    if t < len(starter_ixes) - 1:
      # print "t: ", t, "len(starter_ixes: ", len(starter_ixes)
      ix = starter_ixes[t+1]
    else:
      ix = np.random.choice(range(vocab_size), p=p.ravel())
      key_weights = get_key_weights(x, Wxh, h, Why) # {idx:(Wxh, (Why, Why*h)) }
      print('{idx:(Wxh, (Why, Why*h))}')
      print(key_weights)
    print("t: ", t)
    print( "argmax(h) (after tanh)", np.argmax(h))
    print( "np.argmax(np.dot(Wxh, x))", np.argmax(np.dot(Wxh, x)))
    print( "(Wxh*x)[max_index]", np.dot(Wxh, x)[np.argmax(h)])
    print( "np.argmax(np.dot(Whh, h))", np.argmax(np.dot(Whh, h)))
    print( "(Whh*h)[max_index]", np.dot(Whh, h)[np.argmax(h)])
    x = np.zeros((vocab_size, 1))
    x[ix] = 1
    ixes.append(ix)
  return ixes
  

n, p = 0, 0
mWxh, mWhh, mWhy = np.zeros_like(Wxh), np.zeros_like(Whh), np.zeros_like(Why)
mbh, mby = np.zeros_like(bh), np.zeros_like(by) # memory variables for Adagrad
smooth_loss = -np.log(1.0/vocab_size)*seq_length # loss at iteration 0
while (n == 0):
  # prepare inputs (we're sweeping from left to right in steps seq_length long)
  if p+seq_length+1 >= len(data) or n == 0: 
    hprev = np.zeros((hidden_size,1)) # reset RNN memory
    p = 0 # go from start of data
  inputs = [char_to_ix[ch] for ch in data[p:p+seq_length]]
  targets = [char_to_ix[ch] for ch in data[p+1:p+seq_length+1]]

  # sample from the model now and then
  if n % 100 == 0:
    # part 1
    print "Part 1"
    sample_ix = sample(hprev, inputs[0], 200)
    txt = ''.join(ix_to_char[ix] for ix in sample_ix)
    print '----\n %s \n----' % (txt, )    
    # part 2
    print "Part 2"
    starter = ":::::::::::::::"
    sample_ix = sample_starter(starter, hprev, inputs[0], 20)
    txt = ''.join(ix_to_char[ix] for ix in sample_ix)
    print "Sample starter string: ", starter
    print '----\n %s \n----' % (txt, )

  # forward seq_length characters through the net and fetch gradient
  loss, dWxh, dWhh, dWhy, dbh, dby, hprev = lossFun(inputs, targets, hprev)
  smooth_loss = smooth_loss * 0.999 + loss * 0.001
  if n % 100 == 0: print 'iter %d, loss: %f' % (n, smooth_loss) # print progress
  
  # perform parameter update with Adagrad
  for param, dparam, mem in zip([Wxh, Whh, Why, bh, by], 
                                [dWxh, dWhh, dWhy, dbh, dby], 
                                [mWxh, mWhh, mWhy, mbh, mby]):
    mem += dparam * dparam
    param += -learning_rate * dparam / np.sqrt(mem + 1e-8) # adagrad update

  p += seq_length # move data pointer
  n += 1 # iteration counter 