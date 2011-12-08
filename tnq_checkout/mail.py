from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var
from .models import *

from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from itertools import groupby

from_name = "H.R.H. Grogo"
from_email = "tnq-checkouts@mit.edu"
host = "outgoing.mit.edu"

def _prettify_date(date):
    return date.strftime("%A, %B %d at %I:%M %p")

def sendEquipmentDueEmails():
    active_checkouts = Checkout.query.filter(Checkout.date_in == None).order_by(Checkout.user).all()

    for user, group in groupby(active_checkouts, lambda x: x.user):
        user_checkouts = list(group)
        user_checkouts.sort(key=lambda x: x.date_due) # Can this be taken care of by SQL alchemy?  With groupby mess it up?

        #If the user has any due checkouts, email them
        if user_checkouts[0].date_due.date() <= datetime.datetime.now().date():
            due = [c for c in user_checkouts if c.date_due.date() <= datetime.datetime.now().date()]
            not_due = [c for c in user_checkouts if c not in due]

            due_equipment_table = _makeCheckoutTable(due)

            if not_due:
                not_due_equipment_table = _makeCheckoutTable(not_due)
                not_due_equipment_table['HTML'] = "You also have the following equipment for a little while longer:<br />%s<br />" % not_due_equipment_table['HTML']
                not_due_equipment_table['TEXT'] = "\nYou also have the following equipment for a little while longer:\n%s" % not_due_equipment_table['TEXT']
            else:
                not_due_equipment_table = {'HTML' : "", 'TEXT' : ""}

            html = """   
Hello {name},<br />
<br />
You have some equipment due today!  Please return the following items:<br />

{due_equipment_table}<br />
<br />
{not_due_equipment_table}
If you have any questions just reply to this email.<br />
<br />
Thanks, and keep taking pictures!<br />
-- H.R.H. Grogo
            """.format( name=user.first_name, 
                        due_equipment_table = due_equipment_table['HTML'],
                        not_due_equipment_table = not_due_equipment_table['HTML'] )

            text = """Hello {name},

You have some equipment due today!  Please return the following items:

{due_equipment_table}{not_due_equipment_table}

If you have any questions just reply to this email.

Thanks, and keep taking pictures!

-- H.R.H. Grogo
""".format( name=user.first_name, 
            due_equipment_table = due_equipment_table['TEXT'],
            not_due_equipment_table = not_due_equipment_table['TEXT'] )

            msg = MIMEMultipart('alternative')

            msg['Subject'] = '[Technique Checkouts] Equipment Due'
            msg['From'] = "tnq-checkouts@mit.edu"
            msg['To'] = "%s <%s>" % (user.full_name, user.email)
            text_part = MIMEText(text,'plain')
            html_part = MIMEText(html,'html')
            msg.attach(text_part)
            msg.attach(html_part)
            sendMessage(from_email, [user.email, "tnq-checkouts@mit.edu"], msg.as_string())

def _makeCheckoutTable(checkouts):
    """
    Accepts a list of Checkout objects, and returns a dictionary of text representations.

    The 'HTML' styling is of the form

    <tr><td>Equipment Name</td><td>Date Due</td></tr> {{newline}}

    The Date Due field will either have the date due or "OVERDUE!  Return immediately!"

    while the 'TEXT' styling is something like

   -- Nikon SB-900 Speedlight DIFFUSER        |	*Return by Friday, October 14 at 06:49 PM*

    """
    
    html = "<table><tr><th>Equipment Name</th><th>Date Due</th></tr>"
    text = ""

    for c in checkouts:
        if c.date_due < datetime.datetime.now():
            date_string = "OVERDUE!  Return Immediately!"
            date_string_text = date_string
        else:
            date_string = _prettify_date(c.date_due)
            date_string_text = "*Return by: %s*" % date_string

        html += "<tr><td>%s</td><td>%s</td></tr>\n" % (c.equipment.full_name, date_string)
        text += "-- %s|\t%s\n" % (c.equipment.full_name.ljust(40), date_string)

    html += "</table>"

    return {'HTML' : html, 'TEXT' : text }        

def sendDigestEmail():
    equipment = Equipment.query.join(Equipment.current_checkout).filter(Equipment.current_checkout != None).order_by(Checkout.date_due).all()
    msg = MIMEMultipart('alternative')

    #If anything is actually checked out
    if equipment:
        intro = "Hello TNQ PhotoEds,<br /><br />The following equipment is currently checked out:<br /><br />"
        html = intro + "<table><tr><th>Equipment Name</th><th>Equipment Model</th><th>Checker-Outer</th><th>Date Due</th></tr>\n"
        text = intro.replace("<br />", "\n")
        
        for e in equipment:
            if e.pet_name:
                name = e.pet_name
            else:
                name = e.barcode_id
            html += "<tr><td>%s</td><td>%s %s</td><td>%s</td><td>%s</td></tr>\n" %(name, e.brand, e.model, e.current_checkout.user.full_name, _prettify_date(e.current_checkout.date_due))
            text += "%s\t\t(%s %s)\t\t%s\t\t%s\n" %(name, e.brand, e.model, e.current_checkout.user.full_name, _prettify_date(e.current_checkout.date_due))

        outro = "<br /><br />This message powered by your friendly neighborhood Nagare script."
        html += "</table>" + outro
        text += outro.replace("<br />", "\n")

    else:
        html = "Hello TNQ PhotoEds,<br /><br />Nothing is currently checked out!  Go hassle some peeps to take more pictures."
        text = html.replace("<br />", "\n")

    msg['Subject'] = '[Technique Checkouts] Checkout Digest'
    msg['From'] = "tnq-checkouts@mit.edu"
    msg['To'] = "tnq-checkouts@mit.edu"
    text_part = MIMEText(text,'plain')
    html_part = MIMEText(html,'html')
    msg.attach(text_part)
    msg.attach(html_part)
    sendMessage(from_email, ["tnq-checkouts@mit.edu"], msg.as_string())

def sendCheckoutEmail(staph_user,manboard_user,equipment_list):
    checkouts = staph_user.checkouts_active
    current_checkouts = [c for c in checkouts if c.equipment in equipment_list]
    old_checkouts = [c for c in checkouts if c.equipment not in equipment_list and c.date_due > datetime.datetime.now()]
    expired_checkouts = [c for c in checkouts if c.equipment not in equipment_list and c.date_due <= datetime.datetime.now()]


    intro = "Hello %s,<br /><br />You've checked out the following equipment from Technique:<br /><br />" % (staph_user.first_name)
    text = intro.replace("<br />", "\n")
    html = intro + "\n<table><tr><th>Equipment Name</th><th>Due Date</th></tr>\n"

    for c in current_checkouts:
        html += "<tr><td>%s</td>\n<td>%s</td></tr>\n" % (c.equipment.full_name, _prettify_date(c.date_due))
        text += "-- %s|\t*Return by %s*\n" % (c.equipment.full_name.ljust(40), _prettify_date(c.date_due))

    if old_checkouts or expired_checkouts:
        midtro = "You also have the following equipment checked out -- please remember to get these in on time:"
        html += "</table><br />" + midtro + "<br /><table><tr><th>Equipment Name</th><th>Due Date</th></tr>\n"
        text += "\n" + midtro + "\n\n"

        for c in old_checkouts:
            html += "<tr><td>%s</td><td>%s</td></tr>\n" % (c.equipment.full_name, _prettify_date(c.date_due))
            text += "-- %s|\t*Return by %s*\n" % (c.equipment.full_name.ljust(40), _prettify_date(c.date_due))

        for c in expired_checkouts:
            html += "<tr><td>%s</td><td>OVERDUE - Return immediately!</td></tr>\n" % (c.equipment.full_name,)
            text += "-- %s|\t*OVERDUE - Return immediately!*\n" % (c.equipment.full_name.ljust(40),)

    outro = "If you have any questions, please reply to this email.<br /><br />All the best, and keep taking photos!<br />--%s" %(from_name,)
    if staph_user != manboard_user:
        outro += "<br /><br />P.S. %s was the manboard member who checked your equipment out." % (manboard_user.full_name,)

    html += "</table><br />" + outro
    text += "\n" + outro.replace("<br />", "\n") 

    msg = MIMEMultipart('alternative')
    msg['Subject'] = '[Technique Checkouts] Confirmation of Checkout'
    msg['From'] = "%s <%s>" % (from_name, from_email)
    msg['To'] = "%s <%s>" % (staph_user.full_name, staph_user.email)
    msg['CC'] = "%s <%s>" % (manboard_user.full_name, manboard_user.email)

    text_part = MIMEText(text,'plain')
    html_part = MIMEText(html,'html')
    msg.attach(text_part)
    msg.attach(html_part)

    sendMessage(from_email, [staph_user.email, manboard_user.email], msg.as_string())

def sendCheckinEmail(equipment_list,staph_user=None,old_user=None,manboard_user=None):
    checkouts = [c for c in old_user.checkouts_active if c.equipment not in equipment_list]

    intro = "The following equipment was just checked in%s:<br /><br />" %(" by " + staph_user.full_name if staph_user else "")

    returning_users = []

    html = intro + "<table><tr><th>Equipment Name</th></tr>"
    text = intro.replace("<br />", "\n")
    
    for e in equipment_list:
        html += "<tr><td>%s</td></tr>\n" % (e.full_name, )
        text += "-- %s\n" % (e.full_name, )

    html += "</table>"

    if checkouts:
        midtro = "You still have the following equipment checked out:"
        text += "\n%s\n" %midtro
        html += "<br />" + midtro + "<br /><br /><table>\n<tr><th>Equipment Name</th><th>Date Due</th></tr>\n"
        
        for c in checkouts:
            html += "<tr><td>%s</td><td>%s</td></tr>\n" % (c.equipment.full_name, _prettify_date(c.date_due))
            text += "-- %s|\t*Return by %s*\n" % (c.equipment.full_name.ljust(40), _prettify_date(c.date_due))
        html += "</table>"

    if manboard_user and staph_user != manboard_user:
        midtro = "The supervising manboard member was %s.<br /><br />" %(manboard_user.full_name)
        html += "<br />" + midtro
        text += "\n" + midtro.replace("<br />", "\n")

    outro = "-- %s" %(from_name,)
    html += "<br /><br />" + outro
    text += "\n\n" + outro 

    msg = MIMEMultipart('alternative')
    msg['Subject'] = '[Technique Checkouts] Successful Equipment Check In'
    msg['From'] = "%s <%s>" % (from_name, from_email)

    if old_user:
        msg['To'] = "%s <%s>" % (old_user.full_name, old_user.email)
        to_addresses = [old_user.email]
    else:
        msg['To'] = "%s <%s>" % (from_name, from_email)
        to_addresses = []

    if manboard_user:
        msg['CC'] = "%s <%s>" % (manboard_user.full_name, manboard_user.email,)
        to_addresses.append(manboard_user.email)

    text_part = MIMEText(text,'plain')
    html_part = MIMEText(html,'html')
    msg.attach(text_part)
    msg.attach(html_part)

    sendMessage(from_email, to_addresses, msg.as_string())

def sendMessage(from_addresses, to_addresses, message_string):
    connection = SMTP()
    connection.connect(host)
    connection.sendmail(from_addresses, [from_email] + to_addresses, message_string)
    connection.close()
