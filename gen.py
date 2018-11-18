#! /usr/bin/python3
import mido, argparse

tick_skip = 1

parser = argparse.ArgumentParser(description=
    'Use a brain to generate a MIDI file.\nUsage: python3 gen.py -b brain_path -l length -f midi_filename')
parser.add_argument('-b', '--brain', help =
    'Path to brain files.',
    required = True, nargs = 1, type = str)
parser.add_argument('-l', '--length', help =
    'Length of MIDI to generate.',
    required = True, nargs = 1, type = int)
parser.add_argument('-f', '--file', help =
    'File to save to.',
    required = True, nargs = 1, type = str)
parser.add_argument('-t', '--temp', help =
    'Temperature of output. (Default = 1.0)',
    required = False, defalut = 1.0, nargs = 1, type = float)
args = vars(parser.parse_args())

#generate text
from textgenrnn import textgenrnn

textgen = textgenrnn(weights_path = args['brain'][0] + "/weights.hdf5",
                     vocab_path = args['brain'][0] + "/vocab.json",
                     config_path = args['brain'][0] + "/config.json")

text = textgen.generate(max_gen_length = args['length'][0],
                        return_as_list = True,
                        temperature = arge['temp'][0])[0]

#make a few helper functions
def midi_to_ascii(midi_note):
        if midi_note in range(21, 108 + 1):
            return chr(midi_note + 15)
        else:
            return False

def ascii_to_midi(char):
    return ord(char) - 15

#convert
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
if len(notes_on) > 0:
    for note_midi in notes_on:
        midi_track.append(mido.Message('note_off',
                                           note = note_midi,
                                           velocity = 0,
                                           time = dtick))

midi.save(args['file'][0])
print('Saved to "{}"'.format(args['file'][0]))
