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
        try:
            frame_split = text_frame.split('!')

            time = int(frame_split[0])
            note = ascii_to_midi(frame_split[1])
            velocity = int(frame_split[2])
            state = 'note_off'
            if velocity != '0':
                state = 'note_on'

            midi_track.append(mido.Message(state,
                                           note = note,
                                           velocity = velocity,
                                           time = time))
        except:
            print('The following packet contained erroes: {}'.format(text_frame))
    return midi
