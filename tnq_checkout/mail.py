from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var
from .models import *

from smtplib import SMTP
from email.mime.text import MIMEText

def prettify_date(date):
    return date.strftime("%A, %B %d at %I:%M %p")

class TNQEmail(object):
    def __init__(self):
        self.from_name = "H.R.H. Grogo"
        self.from_email = "tnq-checkouts@mit.edu"
        self.host = "outgoing.mit.edu"

    def sendCheckoutEmail(self,staph_user,manboard_user,equipment_list):
        checkouts = [c for c in staph_user.checkouts if not c.date_in]
        current_checkouts = [c for c in checkouts if c.equipment in equipment_list]
        old_checkouts = [c for c in checkouts if c.equipment not in equipment_list and c.date_due > datetime.datetime.now()]
        expired_checkouts = [c for c in checkouts if c.equipment not in equipment_list and c.date_due <= datetime.datetime.now()]
        message = "Hello %s," % (staph_user.first_name)
        message = message + """
You've checked out the following equipment from Technique:
%s
""" % ("\n".join("-" + c.equipment.full_name + " | Return by %s" % (prettify_date(c.date_due)) for c in current_checkouts))
        if old_checkouts:
            message = message + """
You also have the following equipment checked out---please remember to get these in on time:
%s
""" % ("\n".join("-" + c.equipment.full_name + " | Return by %s" % (prettify_date(c.date_due)) for c in old_checkouts))
        if expired_checkouts:
            message = message + """
You also have the following equipment checked out---please remember to get these in on time:
%s
""" % ("\n".join("-" + c.equipment.full_name + " | Return by %s" % (prettify_date(c.date_due)) for c in expired_checkouts))
        message = message + """
If you have any questions, please reply to this email.

All the best, and keep taking photos!
--%s

P.S. %s was the manboard member who checked your equipment out.""" % (self.from_name, manboard_user.full_name)
        msg = MIMEText(message)
        msg['Subject'] = '[Technique Checkouts] Confirmation of Checkout'
        msg['From'] = "%s <%s>" % (self.from_name,self.from_email)
        msg['To'] = "%s <%s>" % (staph_user.full_name,staph_user.email)
        msg['CC'] = "%s <%s>" % (manboard_user.full_name,manboard_user.email)
        self.sendMessage(self.from_email, ", ".join((staph_user.email,manboard_user.email)), msg.as_string())

    def sendCheckinEmail(self,equipment_list,staph_user=None,manboard_user=None):
        message = """The following equipment was just checked in%s:

%s """ % ("","")

    def sendMessage(self,from_addresses,to_addresses,message_string):
        connection = SMTP()
        connection.connect(self.host)
        connection.sendmail(from_addresses, to_addresses, message_string)
        connection.close()
