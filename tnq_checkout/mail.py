from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var
from .models import *

from smtplib import SMTP

def sendCheckoutConfirmEmail(staph_user,manboard_user,equipment):
    from_name = 'H.R.H. Grogo'
    from_email = 'hrhgrogo@mit.edu'
    subject = '[Technique Checkouts] Confirmation of Checkout'
    headers = """From: %s <%s>\nTo: %s <%s>\nCc: %s <%s>\nSubject: %s\n\n""" % (from_name,from_email,
                                       staph_user.full_name,staph_user.email,
                                       manboard_user.full_name,manboard_user.email,
                                       subject)
    message = """Hello %s,

You've checked out the following equipment from Technique:

============================================================

%s

============================================================

Laters,
--H.R.H. Grogo

P.S. %s was the manboard member who checked it out for you.""" % (
        staph_user.first_name,
        "\n".join(e.full_name for e in equipment),
        manboard_user.full_name)
    connection = SMTP()
    connection.connect("outgoing.mit.edu")
    connection.sendmail(from_email, ", ".join((staph_user.email,manboard_user.email)), headers+message)
    connection.close()