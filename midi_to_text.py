#! /usr/bin/python3
import mido, argparse, os

tick_skip = 1

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

    print() #just to break the files up on the output

    if continue_conversion:
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
        huge_ascii_text += ' ' * (tick_skip * 64) #just add a second or two of silence between files


#now put that hellish text in a file
with open(args['file'][0], 'w') as text_file:
    text_file.write(huge_ascii_text)
print('Saved to {}'.format(args['file'][0]))

#get that monster out of RAM!
del huge_ascii_text
del song_ascii
