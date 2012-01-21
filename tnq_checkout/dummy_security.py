from peak.rules import when
from nagare.security import common
import nagare.ide.security

class SecurityManager(nagare.ide.security.Authentication, common.Rules):
    def set_config(self, config_filename, conf, error):
        pass

    @when(common.Rules.has_permission, (object,))
    def _(self, user, perm, subject):
        return True
