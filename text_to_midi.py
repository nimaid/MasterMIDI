#! /usr/bin/python3
import mido, argparse

parser = argparse.ArgumentParser(description=
    'Convert text file into a MIDI file.\nUsage: python3 text_to_midi.py -t text_file -f midi_filename')
parser.add_argument('-t', '--text', help =
    'Path to text file.',
    required = True, nargs = 1, type = str)
parser.add_argument('-f', '--file', help =
    'File to save to.',
    required = True, nargs = 1, type = str)
args = vars(parser.parse_args())

#load text
text = None
with open(args['text'][0]) as f:
    text = f.read()

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
midi = mido.MidiFile()
midi_track = mido.MidiTrack()
midi.tracks.append(midi_track)
previous_frame = ''
notes_on = set()
for text_frame in split_text:
    frame_split = text_frame.split('!')

    time = int(frame_split[0])
    note = ascii_to_midi(frame_split[1])
    state = 'note_off'
    if frame_split[2] == '1':
        state = 'note_on'

    print("Note={}, State={}, Time={}".format(note, state, time))
    midi_track.append(mido.Message(state,
                                   note = note,
                                   velocity = 64,
                                   time = time))


midi.save(args['file'][0])
print('Saved to "{}"'.format(args['file'][0]))
