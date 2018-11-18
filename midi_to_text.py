#! /usr/bin/python3
import mido, argparse, os

parser = argparse.ArgumentParser(description=
    'Convert all MIDI files in a directory to a text dump.\nUsage: python3 midi_to_text.py -p path_to_midi_files -f text_filename')
parser.add_argument('-p', '--path', help =
    'Path to MIDI files.',
    required = True, nargs = 1, type = str)
parser.add_argument('-f', '--file', help =
    'File to save to.',
    required = True, nargs = 1, type = str)
args = vars(parser.parse_args())

#name the model after the lowest directory name
dir_split = args['path'][0].split('/')
if dir_split[-1] == '':
    _ = dir_split.pop()

model_name = dir_split[-1]

#midi directory
midi_dir = '/'.join(dir_split) + '/'

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
    continue_conversion = True
    try:
        midi = mido.MidiFile(midi_dir + filename)
        merged_midi = mido.merge_tracks(midi.tracks)
    except:
        print('^^^^^^^^ABOVE FILE CONTAINED ERRORS. SKIPPING...^^^^^^^^')
        continue_conversion = False

    if continue_conversion:
        #make a list of relevant events, in form [velocity, note, delay_before]
        midi_list = []
        gathered_delta = 0
        for event in merged_midi:
            if not event.is_meta:
                is_off = False

                if event.type == 'note_on':
                    if event.velocity != 0:
                        midi_list.append([event.velocity,
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
                    midi_list.append([0,
                                      event.note,
                                      event.time + gathered_delta])
                    gathered_delta = 0
            else:
                gathered_delta += event.time

        #now, convert that list into text!
        song_ascii = ''
        for note in midi_list:
            try:
                packet_ascii = str(note[2]) #time before
                packet_ascii += '!'
                packet_ascii += midi_to_ascii(note[1]) #note
                packet_ascii += '!'
                packet_ascii += str(note[0]) #velocity

                song_ascii += packet_ascii
                song_ascii += ' '
            except:
                print('ERROR WHILE CONVERTING NOTE {}, SKIPPING...'.format(note))

        huge_ascii_text += song_ascii
        huge_ascii_text += '2000!a!0 ' #just add two seconds of silence between files

        print() #just to break the files up on the output

#now put that hellish text in a file
with open(args['file'][0], 'w') as text_file:
    text_file.write(huge_ascii_text.strip())
print('Saved to {}'.format(args['file'][0]))

#get that monster out of RAM!
del huge_ascii_text
del song_ascii
