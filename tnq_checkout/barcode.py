from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var
from .models import *

class ScanBarcode(object):
    def __init__(self, messages=[]):
        self.messages = messages
    def handle_scan(self, comp, barcode):
        pass

class ScanUserBarcode(ScanBarcode):
    def handle_scan(self, comp, barcode):
        user = User.get_by(barcode_id=barcode)
        if user:
            comp.answer(user)

class ScanEquipmentBarcode(ScanBarcode):
    def handle_scan(self, comp, barcode):
        equip = Equipment.get_by(barcode_id=barcode)
        if equip:
            comp.answer(equip)

@presentation.render_for(ScanBarcode)
@presentation.render_for(ScanUserBarcode, model="manboard")
def render(self, h, comp, model, *args):
    r = var.Var()
    h << h.script('''$(function(){
                    $('#barcodeInput').focus();
                    });''', type='text/javascript')
    if model == "manboard":
        h << h.img(src="/static/tnq_checkout/images/mitcard.png", alt="mit card", id="id-card")
    with h.form(class_=model if model else "barcode"):
        for i,m in enumerate(self.messages):
            h << h.div(h.parse_htmlstring(m, fragment=True), class_="message message-"+str(i))
        h << h.input(id='barcodeInput',type='text').action(r),
        h << h.input(type='submit', value='Send',class_="hidden-action").action(lambda: self.handle_scan(comp, r())),
    return h.root
