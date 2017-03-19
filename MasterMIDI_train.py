from __future__ import absolute_import, division, print_function

import mido

import os, sys, argparse
import urllib

import numpy as np

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
parser.add_argument('-t', '--timestep', help=
    'Length (ms) of MIDI conversion quantize step. Defaults to 0.1',
    required=False, default=0.1, nargs=1, type=float)

args = vars(parser.parse_args())

#argument feedback and handling
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

if args['validationset'] is not 0.0: 
    valid_set = min(0.5, max(0.0, args['validationset'])) # default 0.0 is set in .add_argument above if not set by user
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

if args['timestep'][0] is not 0.25:
    time_step = max(0.0, args['timestep'][0]) # default 0.1 is set in .add_argument above if not set by user
    print("Time (ms) per step set to", nodes)
else:
    time_step = args['timestep']

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
    
#build the huge ASCII dump from hell
huge_ascii_text = ''
for filename in os.listdir(args['path'][0]):
    midi = mido.MidiFile(working_dir + filename)

    #make a list of relevant events, in form [note_state, note, delay_before]
    midi_list = []
    gathered_delta = 0
    for event in midi:
        if not event.is_meta:
            if event.type == 'note_on':
                midi_list.append([1,
                                  event.note,
                                  event.time + gathered_delta])
            elif event.type == 'note_off':
                midi_list.append([0,
                                  event.note,
                                  event.time + gathered_delta])
                gathered_delta = 0
            else:
                gathered_delta += event.time
        else:
            gathered_delta += event.time

    #now, convert that into text!
    charset = [chr(x) for x in range(ord('z') - 88 + 1, ord('z') + 1)]
    def midi_to_ascii(midi_note):
        if midi_note in range(21, 107 + 1):
            return chr(midi_note + 15)
        else:
            return False
            
    song_ascii = ''
    for 
    
    
    

#now put that hellish text in a file
hell_text_name = model_name + '_ascii_dump.txt'
with open(working_dir + hell_text_name, 'w') as text_file:
    text_file.write(huge_ascii_text)

'''
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

#save the dictionary file
with open(working_dir + model_name + '_dict.pkl', 'wb') as dictfile:
    pickle.dump(char_idx, dictfile)

#function to generate text
def text_gen(brain, length, temp, seed=''):
    print('-- Test with temperature of {} --'.format(temp))
    
    out_text = brain.generate(length, temperature=temp, seq_seed=seed)

    print(out_text)
    return out_text

#function for output file names
def out_name(epoch, temp):
    return 'E{}_T{}.txt'.format(epoch + 1, temp)
'''

#function to save text as MIDI file
def save_text_as_midi(text, directory, output_name):
    full_name = directory + output_name + '.mid'
    
    #HERE WE CONVERT BACK
    
    print('Saved to {}'.format(output_name))

'''
for epoch in range(epochs):
    master_brain.fit(X,
                     Y,
                     validation_set=valid_set,
                     batch_size=bat_size,
                     n_epoch=1,
                     run_id=model_name)


    #do test outputs
    print('-- TESTING --')
    if args['temp'] is not None:
        temp = args['temp'][0]
        
        test_text = text_gen(master_brain, genen, temp)
        outfile_name = out_name(epoch, temp)
        save_text_as_midi(text_text, working_dir, outfile_name)
    else:
        for x in range(2 * 4):
            #for 8 samples
            temp = (x + 1) * 0.25
            
            test_text = text_gen(master_brain, genen, temp)
            outfile_name = out_name(epoch, temp)
            save_text_as_midi(text_text, working_dir, outfile_name)

    brain_name = 'n{}_l{}_e{}_{}.BRAIN'.format(model_name.upper(),
                                               nodes,
                                               layers,
                                               str(epoch + 1))
    master_brain.save(working_dir + brain_name)

    print('Saved brain to file', brain_name)
'''





