from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var
from .models import *

from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from_name = "H.R.H. Grogo"
from_email = "tnq-checkouts@mit.edu"
host = "outgoing.mit.edu"

def _prettify_date(date):
    return date.strftime("%A, %B %d at %I:%M %p")

def sendDigestEmail():
    equipment = Equipment.query.join(Equipment.current_checkout).filter(Equipment.current_checkout != None).order_by(Checkout.date_due).all()
    msg = MIMEMultipart('alternative')

    intro = "Hello TNQ PhotoEds,\n\nThe following equipment is currently checked out:\n\n"
    html = intro + "<table><tr><th>Equipment Name</th><th>Equipment Model</th><th>Checker-Outer</th><th>Date Due</th></tr>\n"
    text = intro 
    
#Add logic here if no equipment is checked out

    for e in equipment:
        if e.pet_name:
            name = e.pet_name
        else:
            name = e.barcode_id
        html += "<tr><td>%s</td><td>%s %s</td><td>%s</td><td>%s</td></tr>\n" %(name, e.brand, e.model, e.current_checkout.user.full_name, _prettify_date(e.current_checkout.date_due))
        text += "%s\t\t(%s %s)\t\t%s\t\t%s\n" %(name, e.brand, e.model, e.current_checkout.user.full_name, _prettify_date(e.current_checkout.date_due))

    html += "</table>This message powered by your friendly neighborhood Nagare script."
    text += "This message powered by your friendly neighborhood Nagare script."

    msg['Subject'] = '[Technique Checkouts] Checkout Digest'
    msg['From'] = "technique@mit.edu"
    msg['To'] = "tnq-checkouts@mit.edu"
    part1 = MIMEText(text,'plain')
    part2 = MIMEText(html,'html')
    msg.attach(part1)
    msg.attach(part2)
    sendMessage(from_email, ["tnq-checkouts@mit.edu"], msg.as_string())

def sendCheckoutEmail(staph_user,manboard_user,equipment_list):
    checkouts = staph_user.checkouts_active
    current_checkouts = [c for c in checkouts if c.equipment in equipment_list]
    old_checkouts = [c for c in checkouts if c.equipment not in equipment_list and c.date_due > datetime.datetime.now()]
    expired_checkouts = [c for c in checkouts if c.equipment not in equipment_list and c.date_due <= datetime.datetime.now()]
    message = "Hello %s,\n" % (staph_user.first_name)
    message = message + """
You've checked out the following equipment from Technique:
%s
""" % ("\n".join("-- " + c.equipment.full_name + "    |    *Return by %s*" % (_prettify_date(c.date_due)) for c in current_checkouts))
    if old_checkouts:
        message = message + """
You also have the following equipment checked out---please remember to get these in on time:
%s
""" % ("\n".join("-- " + c.equipment.full_name + "    |    Return by %s" % (_prettify_date(c.date_due)) for c in old_checkouts))
    if expired_checkouts:
        message = message + """
**The following equipment is expired--this is not good:**
%s
""" % ("\n".join("-- " + c.equipment.full_name + "    |    *Was supposed to be returned by %s*" % (_prettify_date(c.date_due)) for c in expired_checkouts))
    message = message + """
If you have any questions, please reply to this email.

All the best, and keep taking photos!
--%s

P.S. %s was the manboard member who checked your equipment out.""" % (from_name, manboard_user.full_name)
    msg = MIMEText(message)
    msg['Subject'] = '[Technique Checkouts] Confirmation of Checkout'
    msg['From'] = "%s <%s>" % (from_name, from_email)
    msg['To'] = "%s <%s>" % (staph_user.full_name, staph_user.email)
    msg['CC'] = "%s <%s>" % (manboard_user.full_name, manboard_user.email)
    sendMessage(from_email, [staph_user.email, manboard_user.email], msg.as_string())

def sendCheckinEmail(equipment_list,staph_user=None,manboard_user=None):
    message = """The following equipment was just checked in%s:

%s 
%s""" % (" by "+staph_user.full_name if staph_user else "",
     "\n".join("-" + e.full_name for e in equipment_list),
     "\nThe supervising manboard member was " + manboard_user.full_name if manboard_user and staph_user != manboard_user else "")
    message = message + """

--%s""" % (from_name)
    msg = MIMEText(message)
    msg['Subject'] = '[Technique Checkouts] Successful Equipment Check In'
    msg['From'] = "%s <%s>" % (from_name, from_email)
    if staph_user:
        msg['To'] = "%s <%s>" % (staph_user.full_name, staph_user.email)
        msg['CC'] = "%s <%s>" % (manboard_user.full_name, manboard_user.email)
    else:
        msg['To'] = "%s <%s>" % (from_name, from_email)
    sendMessage(from_email, [staph_user.email, manboard_user.email] if staph_user else [], msg.as_string())

def sendMessage(from_addresses, to_addresses, message_string):
    connection = SMTP()
    connection.connect(host)
    connection.sendmail(from_addresses, [from_email] + to_addresses, message_string)
    connection.close()
