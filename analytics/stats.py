

class Statistics(object):

    def __init__(self):
        # The number of submitted identifies/tracks
        self.submitted = 0

        # The number of identifies submitted
        self.identifies = 0
        # The number of tracks submitted
        self.tracks = 0
        # The number of aliases
        self.aliases = 0

        # The number of actions to be successful
        self.successful = 0
        # The number of actions to fail
        self.failed = 0

        # The number of flushes to happen
        self.flushes = 0
