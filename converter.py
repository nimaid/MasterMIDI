import mido

#make a few helper functions
def midi_to_ascii(midi_note):
        if midi_note in range(21, 108 + 1):
            return chr(midi_note + 15)
        else:
            return False

def ascii_to_midi(char):
    return ord(char) - 15

#convert
def text_to_midi(text):
    split_text = text.split(' ')
    midi = mido.MidiFile()
    midi_track = mido.MidiTrack()
    midi.tracks.append(midi_track)
    previous_frame = ''
    notes_on = set()
    for text_frame in split_text:
        frame_split = text_frame.split('!')

        time = None
        try:
            time = int(frame_split[0])
        except:
            time = 0

        note = None
        try:
            note = ascii_to_midi(frame_split[1])
        except:
            note = '$' #lowest note

        velocity = None
        try:
            velocity = int(frame_split[2])
        except:
            velocity = 0

        state = 'note_off'
        if velocity != '0':
            state = 'note_on'

        try:
            midi_track.append(mido.Message(state,
                                           note = note,
                                           velocity = velocity,
                                           time = time))
        except:
            print('ERROR WHILE CONVERTING NOTE {}, SKIPPING...'.format(text_frame))
    return midi
