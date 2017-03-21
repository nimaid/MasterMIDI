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

parser.add_argument('-b', '--brain', help =
    'Path to the brain.zip file.',
    required = True, nargs = 1, type = str)
parser.add_argument('-t','--temp', help =
    'Defaults to displaying multiple temperature outputs which is suggested.' +
    ' If temp is specified, a value of 0.0 to 2.0 is recommended.' +
    ' Temperature is the novelty or' +
    ' riskiness of the generated output.  A value closer to 0 will result' +
    ' in output closer to the input, so higher is riskier.', 
    required = False, nargs = 1, type = float)
parser.add_argument('-g', '--generate', help =
    'Length of text to generate at the end of each epoch. Defaults to 5000.',
    required = False, default = 5000, nargs = 1, type = int)

args = vars(parser.parse_args())

#argument feedback and handling
if args['temp'] and args['temp'][0] is not None:
    temp = min(2.0, max(0.0, args['temp'][0]))
    print("Temperature set to", temp)
else:
    print("Will produce a range of temperature outputs")

if args['generate'] is not 5000: 
    genlen = max(1, args['generate'][0]) # default 5000 is set in .add_argument above if not set by user
    print("Generate length set to ", genlen)
else:
    genlen = args['generate']

#name the model after the lowest directory name
dir_split = args['brain'][0].split('/')
if dir_split[-1] == '':
    _ = dir_split.pop()

model_name = dir_split[-1]

#make working directory
working_dir = '/'.join(dir_split[:-2]) + '/outputs/'
if not os.path.exists(working_dir):
    os.makedirs(working_dir)

#make temporary directory
temp_dir = '/'.join(dir_split[:-2]) + '/temp/'
if not os.path.exists(working_dir):
    os.makedirs(working_dir)

#UNZIP *_brain.zip INTO temp_dir

#UNPICKLE *.brain.settings IN temp_dir

#SET PICKLE CONTENTS TO GLOBAL VARIABLES

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

#LOAD *.brain FROM temp_dir INTO master_brain

#function to generate text
def text_gen(brain, length, temp, seed=''):
    print('Creating a MIDI file with {} characters and  a temperature of {}...'.format(temp))
    
    out_text = brain.generate(length, temperature=temp, seq_seed=seed)

    print(out_text)
    return out_text

#function for output file names
def out_name(epoch, temp):
    return 'E{}_T{}_L{}'.format(epoch + 1, temp, genlen)

#little helper function for decoding
def ascii_to_midi(char):
    return ord(char) - 15

#function to save text as MIDI file
def save_text_as_midi(text, directory, output_name):
    full_name = directory + output_name + '.mid'
    
    split_text = text.split(' ')
    dtick = 0
    midi = mido.MidiFile()
    midi_track = mido.MidiTrack()
    midi.tracks.append(midi_track)
    previous_frame = ''
    notes_on = set()
    for text_frame in split_text:
        text_frame = ''.join(set(text_frame)) #remove repeats
        dtick += tick_skip
        for note_char in text_frame:
            note_midi = ascii_to_midi(note_char)
            if note_char not in previous_frame:
                #if it's a new note turning on
                midi_track.append(mido.Message('note_on',
                                               note = note_midi,
                                               velocity = 64,
                                               time = dtick))
                notes_on.add(note_midi)
                dtick = 0

        for prev_note_char in previous_frame:
            if prev_note_char not in text_frame:
                #if it's an old note turning off
                midi_track.append(mido.Message('note_off',
                                               note = note_midi,
                                               velocity = 0,
                                               time = dtick))
                notes_on.discard(note_midi)
                dtick = 0
        previous_frame = text_frame

    #if there are notes still on, turn them off
    if len(note_on) > 0:
        for note_midi in notes_on:
            midi_track.append(mido.Message('note_off',
                                               note = note_midi,
                                               velocity = 0,
                                               time = dtick))
        
    midi.save(full_name)
    print('Saved to "{}"'.format(output_name + '.mid'))


#do test outputs
if args['temp'] is not None:
    temp = args['temp'][0]
    
    test_text = text_gen(master_brain, genlen, temp)
    outfile_name = out_name(report_epoch, temp)
    save_text_as_midi(test_text, working_dir, outfile_name)
else:
    for x in range(2 * 4):
        #for 8 samples
        temp = (x + 1) * 0.25
        
        test_text = text_gen(master_brain, genlen, temp)
        outfile_name = out_name(report_epoch, temp)
        save_text_as_midi(test_text, working_dir, outfile_name)





