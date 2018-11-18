#! /usr/bin/python3
import argparse
import converter

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

midi = converter.text_to_midi(text)

midi.save(args['file'][0])
print('Saved to "{}"'.format(args['file'][0]))
