
class Title(object):
    def __init__(self, title):
        self.title = title

    def to_inp(self):
        """Return run period as an inp string."""
        # standard holidays should be exposed.
        return 'TITLE\n' \
            '    LINE-1           = *{}*\n'.format(self.title) + \
            '    ..'

    def __repr__(self):
        return self.to_inp()
