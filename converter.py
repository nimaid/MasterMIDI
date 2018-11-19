import mido

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

#convert
def text_to_midi(text):
    split_text = text.split(' ')
    midi = mido.MidiFile()
    midi_track = mido.MidiTrack()
    midi.tracks.append(midi_track)
    midi_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(60)))

    previous_frame = ''
    notes_on = set()
    for text_frame in split_text:
        frame_split = text_frame.split('!')
        #print(frame_split)

        time = None
        try:
            time = decode(frame_split[0])
        except:
            time = 0

        note = None
        try:
            note = ascii_to_midi(frame_split[1])
        except:
            note = '$' #lowest note

        velocity = None
        try:
            velocity = decode(frame_split[2])
        except:
            velocity = 0

        #print("Time: {}, Note: {}, Velocity: {}".format(time, note, velocity))

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
