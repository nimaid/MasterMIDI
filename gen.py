#! /usr/bin/python3
import argparse
import converter

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
    required = False, default = 1.0, nargs = 1, type = float)
args = vars(parser.parse_args())

#generate text
from textgenrnn import textgenrnn

textgen = textgenrnn(weights_path = args['brain'][0] + "/weights.hdf5",
                     vocab_path = args['brain'][0] + "/vocab.json",
                     config_path = args['brain'][0] + "/config.json")

text = textgen.generate(max_gen_length = args['length'][0],
                        return_as_list = True,
                        temperature = args['temp'])[0]

midi = converter.text_to_midi(text)

midi.save(args['file'][0])
print('Saved to "{}"'.format(args['file'][0]))
