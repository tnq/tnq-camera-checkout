from tnq_checkout.mail import sendDigestEmail, sendEquipmentDueEmails

OPTIONS = { "digest" : sendDigestEmail,
            "due"    : sendEquipmentDueEmails }

import sys

if len(sys.argv) > 1 and sys.argv[1] in OPTIONS.keys():
    OPTIONS[sys.argv[1]]()

else:
    print "No command given!"
    print "Available commands:"
    print OPTIONS.keys()

