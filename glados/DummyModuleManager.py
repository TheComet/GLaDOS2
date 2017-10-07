from .module import Module


class DummyModuleManager(Module):

    def is_blacklisted(self, mod):
        return True
