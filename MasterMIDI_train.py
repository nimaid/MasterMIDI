from __future__ import absolute_import, division, print_function

import mido

import os, sys, argparse
import urllib

import numpy as np

import tflearn
from tflearn.data_utils import *

import pickle

parser = argparse.ArgumentParser(description=
    'For help, sorry you\'re fucked.')

parser.add_argument('-p', '--path', help=
    'Path to MIDI files.',
    required = False, nargs = 1, type=str)
parser.add_argument('-t','--temp', help=
    'Defaults to displaying multiple temperature outputs which is suggested.' +
    ' If temp is specified, a value of 0.0 to 2.0 is recommended.' +
    ' Temperature is the novelty or' +
    ' riskiness of the generated output.  A value closer to 0 will result' +
    ' in output closer to the input, so higher is riskier.', 
    required = False, nargs = 1, type=float)
parser.add_argument('-l','--length', help=
    'Optional length of text sequences to analyze.  Defaults to 25.',
    required = False, default = 25, nargs = 1, type = int)
parser.add_argument('-g', '--generate', help=
    'Optional length of text to generate at the end of each epoch. Defaults to 600.',
    required = False, default = 600, nargs = 1, type = int)
parser.add_argument('-e', '--epochs', help=
    'Number of epochs to train. Default is 50.',
    required = False, default = 50, nargs = 1, type = int)
parser.add_argument('-v', '--validationset', help=
    'Percent of dataset to use as validation. Default is 0.0',
    required = False, default = 0.0, nargs = 1, type = float)
parser.add_argument('-b', '--batchsize', help=
    'Size of batches to train network. Default is 128',
    required = False, default = 128, nargs = 1, type = int)
parser.add_argument('-d', '--dropout', help=
    'Dropout rate after each layer. Defaults to 0.5',
    required = False, default = 0.5, nargs = 1, type = float)
parser.add_argument('-s', '--layers', help=
    'Number of LSTM layers to use. Defaults to 3',
    required = False, default = 3, nargs = 1, type = int)
parser.add_argument('-n', '--nodes', help=
    'Number of LSTM nodes per layer. Defaults to 128',
    required = False, default = 128, nargs = 1, type = int)
parser.add_argument('-f', '--frameskip', help=
    'Number of ticks to progress every tick. Defaults to 128',
    required = False, default = 128, nargs = 1, type = int)
parser.add_argument('-r', '--reportrate', help=
    'Number of epochs between test output. Default is 10',
    required = False, default = 10, nargs = 1, type = int)

args = vars(parser.parse_args())

#argument feedback and handling
if args['temp'] and args['temp'][0] is not None:
    temp = min(2.0, max(0.0, args['temp'][0]))
    print("Temperature set to", temp)
else:
    print("Will display a range of temperature outputs")

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

if args['frameskip'] is not 128: 
    tick_skip = max(1, args['frameskip'][0]) # default 128 is set in .add_argument above if not set by user
    print("Number of ticks per tick set to", tick_skip)
else:
    tick_skip = args['frameskip']

if args['reportrate'] is not 10: 
    report_rate = max(1, args['reportrate'][0]) # default 10 is set in .add_argument above if not set by user
    print("Number of epochs between reports set to", report_rate)
else:
    report_rate = args['reportrate']

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

midi_dir = '/'.join(dir_split[:-1]) + '/'

#make a few helper functions
def midi_to_ascii(midi_note):
        if midi_note in range(21, 108 + 1):
            return chr(midi_note + 15)
        else:
            return False

def ascii_to_midi(char):
    return ord(char) - 15

#build the huge ASCII dump from hell
huge_ascii_text = ''
current_file = 0
for filename in os.listdir(args['path'][0]):
    current_file += 1
    print('Converting file {} out of {}: "{}"...'.format(current_file,
                                                         len(os.listdir(args['path'][0])),
                                                         filename))
    midi = mido.MidiFile(midi_dir + filename)
    merged_midi = mido.merge_tracks(midi.tracks)

    #make a list of relevant events, in form [note_state, note, delay_before]
    midi_list = []
    gathered_delta = 0
    for event in merged_midi:
        if not event.is_meta:
            is_off = False
            
            if event.type == 'note_on':
                if event.velocity != 0:
                    midi_list.append([True,
                                      event.note,
                                      event.time + gathered_delta])
                    gathered_delta = 0
                else:
                    is_off = True
                
            elif event.type == 'note_off':
                is_off = True
                
            else:
                gathered_delta += event.time

            if is_off:
                midi_list.append([False,
                                  event.note,
                                  event.time + gathered_delta])
                gathered_delta = 0
        else:
            gathered_delta += event.time

    #calculate total time
    total_time = 0
    for event in midi_list:
        total_time += event[2]

    #now, convert that list into text!
    song_ascii = ''
    midi_is_on = {midi_to_ascii(x): False for x in range(21, 108 + 1)}
    run_time = 0
    current_event = 0
    for tick in range(0, total_time, tick_skip):
        #now, we do the fun part, make a packet!
        packet_text = ''
        keep_running = True
        while(keep_running):
            event = midi_list[current_event]
            run_time += event[2]
            #print('Current step: {}ms \t Current time: {}ms'.format(time_ms, running_total_ms))
            if run_time > tick:
                #if our current event is in the next packet
                run_time -= event[2] #since we didn't use the time yet
                keep_running = False
            else:
                is_on = event[0]
                note_char = midi_to_ascii(event[1])
                
                if note_char != False:
                    #if it was in range
                    if is_on:
                        midi_is_on[note_char] = True
                    else:
                        midi_is_on[note_char] = False
                else:
                    print('Warning! Skipping out of range note...')

                current_event += 1

        #after all events for this step are processed, make text
        for note in midi_is_on:
            if midi_is_on[note]:
                packet_text += note

        #sort the letters
        packet_text = ''.join(sorted(packet_text))

        song_ascii += packet_text + ' '

    huge_ascii_text += song_ascii

#now put that hellish text in a file
hell_text_name = model_name + '_ascii_dump.txt'
with open(working_dir + hell_text_name, 'w') as text_file:
    text_file.write(huge_ascii_text)
print('Saved to {}'.format(hell_text_name))

#get that moster out of RAM!
del huge_ascii_text
del song_ascii

#make the 'semi-redundant sequences', or samples, if you like
X, Y, char_dict = \
    textfile_to_semi_redundant_sequences(working_dir + hell_text_name,
                                         seq_maxlen=maxlen,
                                         redun_step=3)

#the time has come to assemble the brain
brain = tflearn.input_data([None, maxlen, len(char_dict)])
for layer in range(layers):
    if layer < layers - 1:
        brain = tflearn.lstm(brain, nodes, return_seq = True)
    else:
        brain = tflearn.lstm(brain, nodes)

    brain = tflearn.dropout(brain, dropout)
    
brain = tflearn.fully_connected(brain, len(char_dict), activation = 'softmax')
brain = tflearn.regression(brain, optimizer = 'adam',
                           loss = 'categorical_crossentropy',
                           learning_rate = 0.001)

master_brain = tflearn.SequenceGenerator(brain,
                                         dictionary=char_dict,
                                         seq_maxlen=maxlen,
                                         clip_gradients=5.0,
                                         checkpoint_path=working_dir + 'model_'+ model_name)

#function to generate text
def text_gen(brain, length, temp, seed=''):
    print('-- Test with temperature of {} --'.format(temp))
    
    out_text = brain.generate(length, temperature=temp, seq_seed=seed)

    print(out_text)
    return out_text

#function for output file names
def out_name(epoch, temp):
    return 'E{}_T{}'.format(epoch + 1, temp)

#function to save text as MIDI file
def save_text_as_midi(text, directory, output_name):
    full_name = directory + output_name + '.mid'
    
    split_text = text.split(' ')
    dtick = 0
    midi = mido.MidiFile()
    midi_track = mido.MidiTrack()
    midi.tracks.append(midi_track)
    previous_frame = ''
    for text_frame in split_text:
        text_frame = ''.join(set(text_frame)) #remove repeats
        dtick += tick_skip
        for note_char in text_frame:
            if note_char not in previous_frame:
                #if it's a new note turning on
                midi_track.append(mido.Message('note_on',
                                               note = ascii_to_midi(note_char),
                                               velocity = 64,
                                               time = dtick))
                dtick = 0

        for prev_note_char in previous_frame:
            if prev_note_char not in text_frame:
                #if it's an old note turning off
                midi_track.append(mido.Message('note_off',
                                               note = ascii_to_midi(note_char),
                                               velocity = 0,
                                               time = dtick))
                dtick = 0
        previous_frame = text_frame

    midi.save(full_name)
    print('Saved to "{}"'.format(output_name + '.mid'))

for epoch in range(epochs):
    master_brain.fit(X,
                     Y,
                     validation_set = valid_set,
                     batch_size = bat_size,
                     n_epoch = report_rate,
                     run_id = model_name)


    #do test outputs
    print('-- TESTING --')
    if args['temp'] is not None:
        temp = args['temp'][0]
        
        test_text = text_gen(master_brain, genlen, temp)
        outfile_name = out_name(epoch, temp)
        save_text_as_midi(test_text, working_dir, outfile_name)
    else:
        for x in range(2 * 4):
            #for 8 samples
            temp = (x + 1) * 0.25
            
            test_text = text_gen(master_brain, genlen, temp)
            outfile_name = out_name(epoch, temp)
            save_text_as_midi(test_text, working_dir, outfile_name)

    #save the current model
    brain_name = '{}_e{}.brain'.format(model_name, str(epoch + 1))
    master_brain.save(working_dir + brain_name)
    print('Saved brain as "{}"'.format(brain_name))
    
    brain_settings_name = brain_name + '.settings'
    brain_settings = {'model_name' : model_name,
                      'tick_skip' : tick_skip,
                      'nodes' : nodes,
                      'layers' : layers,
                      'char_dict' : char_dict}
    with open(working_dir + brain_settings_name, 'wb') as settings_file:
        pickle.dump(brain_settings, settings_file)
    print('Saved brain settings as "{}"'.format(brain_settings_name))





