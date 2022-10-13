
class Title(object):
    def __init__(self, title):
        self.title = title

    def to_inp(self) -> str:
        """Return run period as an inp string."""
        # standard holidays should be exposed.
        return 'TITLE\n' \
            '    LINE-1           = *{}*\n'.format(self.titel) + \
            '    ..'

    def __repr__(self) -> str:
        return self.to_inp()
