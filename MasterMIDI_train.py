from __future__ import absolute_import, division, print_function

from MIDI import *

import os, sys, argparse
import urllib

import tflearn
from tflearn.data_utils import *

import pickle

parser = argparse.ArgumentParser(description=
    'Pass a text file to generate LSTM output')

parser.add_argument('-p', '--path', help=
    'Path to MIDI files.',
    required=False, nargs=1, type=str)
parser.add_argument('-t','--temp', help=
    'Defaults to displaying multiple temperature outputs which is suggested.' +
    ' If temp is specified, a value of 0.0 to 2.0 is recommended.' +
    ' Temperature is the novelty or' +
    ' riskiness of the generated output.  A value closer to 0 will result' +
    ' in output closer to the input, so higher is riskier.', 
    required=False, nargs=1, type=float)
parser.add_argument('-l','--length', help=
    'Optional length of text sequences to analyze.  Defaults to 25.',
    required=False, default=25, nargs=1, type=int)
parser.add_argument('-g', '--generate', help=
    'Optional length of text to generate at the end of each epoch. Defaults to 600.',
    required=False, default=600, nargs=1, type=int)
parser.add_argument('-e', '--epochs', help=
    'Number of epochs to train. Default is 50.',
    required=False, default=50, nargs=1, type=int)
parser.add_argument('-v', '--validationset', help=
    'Percent of dataset to use as validation. Default is 0.0',
    required=False, default=0.0, nargs=1, type=float)
parser.add_argument('-b', '--batchsize', help=
    'Size of batches to train network. Default is 128',
    required=False, default=128, nargs=1, type=int)
parser.add_argument('-d', '--dropout', help=
    'Dropout rate after each layer. Defaults to 0.5',
    required=False, default=0.5, nargs=1, type=float)
parser.add_argument('-s', '--layers', help=
    'Number of LSTM layers to use. Defaults to 3',
    required=False, default=3, nargs=1, type=int)
parser.add_argument('-n', '--nodes', help=
    'Number of LSTM nodes per layer. Defaults to 128',
    required=False, default=128, nargs=1, type=int)

args = vars(parser.parse_args())

#name the model after the lowest directory name
dir_split = args['path'][0].split('/')
if dir_split[-1] == '':
    model_name = dir_split[-2]
else:
    model_name = dir_split[-1]

#make working directory
working_dir = '/'.join(dir_split[:-2]) + '/' + model_name + '_data/'
if not os.path.exists(working_dir):
    os.makedirs(working_dir)

#turns byte values (0-127) into a hex string of length 2
def hexify(num):
    return str(hex(num))[2:]

#build the huge hex dump from hell
score_hex_string = ''
for filename in os.listdir(args['path'][0]):
    with open(args['path'][0] + filename, 'rb') as f:
        score = midi2score(f.read())
    
    prev_time = 0
    for event in score[1]:
        if event[0] == 'note':
            dtime = event[1] - prev_time
            
            dtime_hex = hexify(dtime)
            duration_hex = hexify(event[2])
            note_hex = hexify(event[4])
            velocity_hex = hexify(event[5])
            
            score_hex_string += dtime_hex + duration_hex + note_hex + velocity_hex
            
            prev_time = event[1]
    score_hex_string += '00ffcc00' #long pause between songs
#hex dump from hell completed

#now put that hell text in a file
hell_text_name = 'HEX_' + model_name.upper() + '.TXT'
with open(working_dir + hell_text_name, 'w') as hex_text:
    hex_text.write(score_hex_string)

#argument handling
if args['temp'] and args['temp'][0] is not None:
    temp = min(2.0, max(0.0, args['temp'][0]))
    print("Temperature set to", temp)
else:
    print("Will display multiple temperature outputs")

if args['length'] is not 25:
    maxlen = max(1, args['length'][0]) # default 25 is set in .add_argument above if not set by user
    print("Sequence max length set to ", maxlen)
else:
    maxlen = args['length']

if args['generate'] is not 600: 
    genlen = max(1, args['generate'][0]) # default 600 is set in .add_argument above if not set by user
    print("Generate length set to ", genlen)
else:
    genlen = args['generate']

if args['epochs'] is not 50: 
    epochs = max(1, args['epochs'][0]) # default 50 is set in .add_argument above if not set by user
    print("Epochs set to ", epochs)
else:
    epochs = args['epochs']

if args['validationset'] is not 0.1: 
    valid_set = min(0.5, max(0.0, args['validationset'][0])) # default 0.1 is set in .add_argument above if not set by user
    print("Validation set set to ", valid_set)
else:
    valid_set = args['validationset']

if args['batchsize'] is not 128: 
    bat_size = max(1, args['batchsize'][0]) # default 128 is set in .add_argument above if not set by user
    print("Batch size set to ", bat_size)
else:
    bat_size = args['batchsize']
    
if args['dropout'] is not 0.5: 
    dropout = max(0, min(1, args['dropout'][0])) # default 0.5 is set in .add_argument above if not set by user
    print("Dropout rate set to", dropout)
else:
    dropout = args['dropout']

if args['layers'] is not 3: 
    layers = max(1, args['layers'][0]) # default 3 is set in .add_argument above if not set by user
    print("Number of layers set to", layers)
else:
    layers = args['layers']

if args['nodes'] is not 128: 
    nodes = max(1, args['nodes'][0]) # default 128 is set in .add_argument above if not set by user
    print("Number of nodes per layer set to", nodes)
else:
    nodes = args['nodes']

#make the 'semi-redundant sequences', or samples, if you like
X, Y, char_idx = \
    textfile_to_semi_redundant_sequences(working_dir + hell_text_name,
                                         seq_maxlen=maxlen,
                                         redun_step=3)

#the time has come to assemble the brain
brain = tflearn.input_data([None, maxlen, len(char_idx)])
for layer in range(layers):
    if layer < layers - 1:
        brain = tflearn.lstm(brain, nodes, return_seq=True)
    else:
        brain = tflearn.lstm(brain, nodes)

    brain = tflearn.dropout(brain, dropout)
    
brain = tflearn.fully_connected(brain, len(char_idx), activation='softmax')
brain = tflearn.regression(brain, optimizer='adam',
                           loss='categorical_crossentropy',
                           learning_rate=0.001)

master_brain = tflearn.SequenceGenerator(brain,
                                         dictionary=char_idx,
                                         seq_maxlen=maxlen,
                                         clip_gradients=5.0,
                                         checkpoint_path=working_dir + 'model_'+ model_name)

'''
#now we see if the user wanted to load a model
if len(args['model']) > 0:
        m.load(args['model'][0])
'''

#save the dictionary file
with open(working_dir + model_name + '_dict.pkl', 'wb') as dictfile:
    pickle.dump(char_idx, dictfile)

'''
#make a function to convert it back
def hell_hex_to_midi_bytes(hell_hex):
'''

for epoch in range(epochs):
    #train
    master_brain.fit(X,
                     Y,
                     validation_set=valid_set,
                     batch_size=bat_size,
                     n_epoch=1,
                     run_id=model_name)

    #do test outputs
    seed = ''
    print('-- TESTING --')
    if args['temp'] is not None:
        temp = args['temp'][0]
        print('-- Test with temperature of',
              temp,
              '--')
        hell_hex = master_brain.generate(genlen,
                                         temperature=temp,
                                         seq_seed=seed)

        print(hell_hex)

        '''
        outfile_name = str(epoch + 1) + '_' + str(temp).replace('.', '-') + '.TXT'
        with open(working_dir + outfile_name, 'wt') as outfile:
            outfile.write(hell_hex)
        '''

        score = [96]
        previous_time = 0

        for x in range(len((hell_hex) // 8)):
            note = list(bytearray.fromhex(hell_hex[x * 4 : (x + 1) * 4]))
            score.append(['note', previous_time, note[1], 1, note[2], note[3]])
            previous_time += note[0]

        midi = score2midi(score)
        outfile_name = str(epoch + 1) + '_' + str(temp).replace('.', '-') + '.MID'
        with open(working_dir + outfile_name, 'wb') as outfile:
            outfile.write(midi)

        print('Saved to file', outfile_name)

        
    else:
        for x in range(2 * 4):
            #for 8 samples
            temp = (x + 1) * 0.25
            print('-- Test with temperature of',
                  temp, '--')
            hell_hex = master_brain.generate(genlen,
                                             temperature=temp,
                                             seq_seed=seed)

            print(hell_hex)
            
            outfile_name = str(epoch + 1) + '_' + str(temp).replace('.', '-') + '.TXT'
            with open(working_dir + outfile_name, 'wt') as outfile:
                outfile.write(hell_hex)

            print('Saved to file', outfile_name)

            

    brain_name = 'n{}_l{}_e{}_{}.BRAIN'.format(model_name.upper(),
                                               nodes,
                                               layers,
                                               str(epoch + 1))
    master_brain.save(working_dir + brain_name)

    print('Saved brain to file', brain_name)








