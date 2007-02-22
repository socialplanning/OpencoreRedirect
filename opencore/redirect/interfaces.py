from zope.interface.common.mapping import IReadMapping, IWriteMapping

class IRedirectMapping(IReadMapping, IWriteMapping):
    """ a mapping object for paths """

    def __getitem__(key):
        """Get a value for a key(a path)

        A KeyError is raised if there is no value for the key.

        interpolates path into a qualified address
        """
