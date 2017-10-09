
import sys
import pickle

test_level = (
        (
            ('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'),
            ('~~~~....?.........................................~~~~~'),
            ('~~.......%%%%%%%%%%%%%%%%%%%.......................~~~~'),
            ('~~.......%d____u%..%_______%..?.....................~~~'),
            ('~~..?....%%%%@%%%..%#%%%%%%%.................<.......~~'),
            ('~~.......%______%..%__%____%.........................~~'),
            ('~~.......%______%..%#%%%%#%%.............~~..........~~'),
            ('~~.......%______%......................~~~~~~~.......~~'),
            ('~~?......%%%%%#%%.....................~~~~~~~~.......~~'),
            ('~~~~~~~.................<.............~~~~~~~....>...~~'),
            ('~~~~~~~~...............................~~~~~~........~~'),
            ('~~~~~~~~....................?..........~~~..........~~~'),
            ('~~~.?.............?.....>..............~~~..........~~~'),
            ('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'),
            ('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'),
            ('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'),
            ('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'),
            ('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        ),
    )

with open(sys.argv[1], 'wb') as outfile:
    pickle.dump(test_level, outfile)