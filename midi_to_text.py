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
        if midi_note in range(19, 111 + 1):
            return chr(midi_note + 15)
        else:
            return False

def ascii_to_midi(char):
    return ord(char) - 15

def encode(number):
    alphabet = '"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'

    if not isinstance(number, int):
        raise TypeError('number must be an integer')

    base93 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base93 = alphabet[i] + base93

    return sign + base93

def decode(number):
    alphabet = '"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'

    if not isinstance(number, str):
        raise TypeError('number must be a string')

    base10 = 0

    try:
        for i in range(len(number)):
            val = alphabet.find(number[i])
            val *= pow(len(alphabet), len(number) - i - 1)
            base10 += val
    except:
        raise TypeError('number contains invalid characters')

    return base10

#build the huge ASCII dump from hell
text_file = open(args['file'][0], 'w')
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
                packet_ascii = encode(note[2]) #time before
                packet_ascii += '!'
                packet_ascii += midi_to_ascii(note[1]) #note
                packet_ascii += '!'
                packet_ascii += encode(note[0]) #velocity

                song_ascii += packet_ascii
                song_ascii += ' '
            except:
                print('ERROR WHILE CONVERTING NOTE {}, SKIPPING...'.format(note))

        text_file.write(song_ascii)
        text_file.flush()
        os.fsync(text_file.fileno())
    print() #just to break the files up on the output

text_file.close()
