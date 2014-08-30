from __future__ import with_statement

import os
import datetime
from nagare import presentation, component, util, var, log
from .models import *
from .barcode import *
import mail

from itertools import groupby

def equipment_icon(h, equip_type):
    return h.img(src="/static/tnq_checkout/images/icons/%s.svg" % (equip_type),
                 class_="icon")

class TaskSelector(object):
    """ TaskSelector provides the choice to either "borrow" or "return" equipment
    """
    def __init__(self):
        self.scan = component.Component(ScanBarcode([]))

@presentation.render_for(TaskSelector)
def render(self, h, comp, *args):
    self.scan.on_answer(lambda _: comp.answer(_))
    h << self.scan
    with h.div(class_='task-selector ui-helper-clearfix'):
        with h.div(class_='borrow'):
            h << h.a('borrow').action(lambda: comp.answer("borrow"))
        with h.div(class_='return'):
            h << h.a('return').action(lambda: comp.answer("return"))
    return h.root


class Confirm(object):
    """Display a confirmation message, with buttons
    """
    def __init__(self, msg, buttons = ["ok"]):
        """Initialization

        In:
          - ``msg`` -- message to display
        """
        self.msg = msg
        self.buttons = buttons

@presentation.render_for(Confirm)
def render(self, h, comp, *args):
    """The view is a simple form with the text and multiple submit buttons

    In:
      - ``h`` -- the renderer
      - ``comp`` -- the component
      - ``model`` -- the name of the view

    Return:
      - a tree
    """
    with h.form(class_="confirm"):
        h << h.div(self.msg, class_="message")
        for i, button in enumerate(self.buttons):
            h << h.input(type='submit', value=button, class_="button-%s"%(i)).action(lambda i=i: comp.answer(i))
    return h.root

class ItemList(object):
    """ Displays a list of items
    """
    def get_items(self):
        return range(1,4)

    def render_item(self, h, comp, item):
        h << h.a(item).action(lambda item=item: comp.answer(item))

class UserList(ItemList):
    """ Displays a list of TNQ users
    """
    def get_items(self):
        return User.query.order_by(User.last_name, User.first_name)

    def render_item(self, h, comp, u):
        h << h.a(u.first_name + " " + u.last_name).action(lambda u=u: comp.answer(u))

@presentation.render_for(ItemList)
def render(self, h, comp, *args):
    items = self.get_items()

    h.head.javascript_url('/static/tnq_checkout/scripts/scrollview.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/vanillaos.js')
    
    with h.div(class_="scrollview-container",scrollviewbars="none",scrollviewmode="table",scrollviewenabledscrollx="no"):
        with h.div(class_="scrollview-content"):
            for item in items:
                with h.div(class_="scrollview-item"):
                    self.render_item(h, comp, item)
    return h.root

class SelectStaph(object):
    def __init__(self, manboard_name):
        self.scan = component.Component(ScanUserBarcode(["<strong>%s</strong> is checking out equipment for..."%(manboard_name),"Select staph below or scan MIT ID"]))
        self.list = component.Component(UserList())

@presentation.render_for(SelectStaph)
def render(self, h, comp, *args):
    self.scan.on_answer(comp.answer)
    self.list.on_answer(comp.answer)
    with h.div(class_="vpane"):
        h << self.scan
    with h.div(class_="vpane"):
        h << self.list

    return h.root

class SelectEquipment(object):
    def __init__(self, manboard=None, staph=None):
        self.manboard = manboard
        self.staph = staph
        self.scan = component.Component(ScanEquipmentBarcode())
        self.equipment = []
        self.scan.on_answer(self.scan_equipment)

    def scan_equipment(self, equipment):
        self.add_equipment(equipment)

    def add_equipment(self, equipment):
        if equipment not in self.equipment:
            self.equipment.insert(0, equipment)

    def remove_equipment(self, equipment):
        if equipment in self.equipment:
            self.equipment.remove(equipment)

    def set_equipment(self, equipment):
        self.equipment = list(equipment)

class UnselectEquipment(SelectEquipment):
    def __init__(self, manboard=None, staph=None):
        super(UnselectEquipment, self).__init__(manboard, staph)
        self.all_equipment = []

    def scan_equipment(self, equipment):
        # Track the full set of equipment for inventory purposes.
        self.all_equipment.append(equipment)
        # Remove from the display list.
        self.remove_equipment(equipment)

@presentation.render_for(SelectEquipment, model="borrow")
@presentation.render_for(SelectEquipment, model="confirm")
@presentation.render_for(SelectEquipment, model="overdue")
@presentation.render_for(SelectEquipment, model="return")
@presentation.render_for(UnselectEquipment, model="inventory")
def render(self, h, comp, model, *args):
    if model == "overdue":
        with h.div(class_="message message-1 confirm"):
            h << "%s has the following OVERDUE equipment:" % (self.staph.first_name)
    elif model == "confirm":
        with h.div(class_="message message-1 confirm"):
            h << "%s has checked out:" % (self.staph.first_name)
    else:
        if model == "return":
            prompt = [" ", "scan equipment to return"]
        elif model == "inventory":
            prompt = ["scan equipment to inventory"]
        else:
            prompt = ["<strong>%s</strong> is checking out equipment." % (self.manboard.full_name),
                      "scan equipment"]

            if self.staph and self.manboard != self.staph:
                prompt[0] = prompt[0][:-1] + " for <strong>%s</strong>." % (self.staph.full_name)
        self.scan().messages = prompt
        h << self.scan
    
    h.head.javascript_url('/static/tnq_checkout/scripts/scrollview.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/vanillaos.js')
    
    # FIX ME
    if model == "confirm":
        h.head.css_url('/static/tnq_checkout/styles/hide-cancel.css')
    
    with h.div(class_="scrollview-container equipment%s" % (' '+model if model else ''),
               scrollviewbars="none",
               scrollviewmode="table",
               scrollviewenabledscrollx="no"):
        with h.div(class_="scrollview-content"):
            for e in self.equipment:
                with h.div(class_="scrollview-item scrollview-disabledrag ui-helper-clearfix"):
                    if model != "inventory":
                        h << equipment_icon(h, e.equip_type)
                    with h.div(class_="name"):
                        h << e.brand
                        if e.model:
                            h << " "
                            h << e.model
                        if e.pet_name:
                            h << h.strong("(%s)" % (e.pet_name))
                    if model == "overdue":
                        with h.div(class_="due"):
                            h << h.strong("Due: ")
                            h << e.current_checkout.date_due.strftime("%m/%d")
                    elif model == "confirm":
                        with h.div(class_="due"):
                            h << h.strong("Due: ")
                            h << e.checkout_hours/24
                            h << " day%s" % ('' if e.checkout_hours == 24 else 's')
                    elif model != "inventory":
                        h << h.a("X",class_="ex").action(lambda e=e: self.remove_equipment(e))
    with h.div(class_="finish-checkout"):
        if model == "overdue":
            a = h.a("Continue Anyway")
        elif model == "confirm":
            a = h.a("Okay")
        elif model == "return":
            a = h.a("Return Equipment")
        elif model == "inventory":
            a = h.a("Finish Inventory")
        else:
            a = h.a("Finish Checkout")
        a.set("onClick", """this.innerHTML = "Processing..."; this.className = "active_link"; old = this.clicked; this.clicked = true; return old != true;""")
        h << a.action(lambda: comp.answer(self.equipment))

    return h.root

class RootView(component.Task):
    def go(self, comp):
        while True:
            task = comp.call(TaskSelector())
            if task == "borrow":
                comp.call(TaskWrapper("borrow", component.Component(BorrowTask())))
            elif task == "return":
                comp.call(TaskWrapper("return", component.Component(ReturnTask())))
            elif task == "TNQ_INV":
                comp.call(TaskWrapper("inventory", component.Component(InventoryTask())))

class BorrowTask(component.Task):
    def go(self, comp):
        manboard_user = comp.call(ScanUserBarcode(["Scan manboard member's barcode", "Typically, the barcode on the back of an MIT ID card."]), model="manboard")
        if not manboard_user.is_manboard():
            comp.call(Confirm("You must be a manboard member to authorize a checkout."))
        else:
            staph_user = comp.call(SelectStaph(manboard_user.full_name))

            old_checkouts = staph_user.checkouts_overdue
            if old_checkouts:
                old_checkout_equipment = [c.equipment for c in old_checkouts]
                old_checkout_equipment_select = SelectEquipment(manboard_user, staph_user)
                old_checkout_equipment_select.set_equipment(old_checkout_equipment)
                comp.call(old_checkout_equipment_select, model="overdue")

            active_restrictions = staph_user.restrictions_active
            if active_restrictions:
                choice = comp.call(Confirm("%s is prohibited from checking out equipment until %s. Are you sure you wish to override this?" %
                                           (staph_user.full_name, active_restrictions[0].date_end),
                                           buttons=["Cancel", "Override"]
                                           ))
                if not choice:
                    return

            equipment_select = SelectEquipment(manboard_user, staph_user)
            checkout_ready = False
            equipment_to_checkin = []
            while not checkout_ready:
                items = comp.call(equipment_select, model="borrow")
                checkout_ready = True
                for item in items:
                    existing_checkout = item.current_checkout
                    if existing_checkout:
                        choice = 0;
                        if staph_user != existing_checkout.user:
                            choice = comp.call(Confirm("%s is currently checked out to %s. Do you want to check it in for them?" %
                                                   (item.full_name,existing_checkout.user.full_name),
                                                   buttons=["Yes", "No"]))
                        if choice == 0:
                            equipment_to_checkin.append(item)
                        else:
                            equipment_select.remove_equipment(item)
                            checkout_ready = False

            # Complete old checkouts
            return_equipment(equipment_to_checkin, by_user=staph_user, by_manboard_user=manboard_user)

            for item in items:
                checkout = Checkout()
                checkout.user = staph_user
                checkout.equipment = item
                checkout.manboard_member = manboard_user
                checkout.date_out = datetime.datetime.now()
                checkout.date_due = checkout.date_out + datetime.timedelta(hours=item.checkout_hours)
            if items:
                mail.sendCheckoutEmail(staph_user, manboard_user, items)
            comp.call(equipment_select, model="confirm")

def return_equipment(equipment, by_user=None, by_manboard_user=None):
    actually_returned_items = [e for e in equipment if e.current_checkout]

    key_func = lambda x: x.current_checkout.user
    sorted_items = sorted(actually_returned_items, key=key_func)

    users_to_penalize = set()

    for item in actually_returned_items:
        if item.current_checkout.date_due + datetime.timedelta(hours=24) < datetime.datetime.now():
            users_to_penalize.add(item.current_checkout.user)

    for user in users_to_penalize:
        restriction = UserRestriction()
        restriction.user = user
        restriction.date_start = datetime.datetime.now()
        restriction.date_end = datetime.datetime.now() + datetime.timedelta(days=7)

    for user, group in groupby(sorted_items, key_func):
        mail.sendCheckinEmail(list(group), old_user=user, staph_user=by_user, manboard_user=by_manboard_user)

    for item in actually_returned_items:
        item.current_checkout.date_in = datetime.datetime.now()

class ReturnTask(component.Task):
    def go(self, comp):
        returned_items = comp.call(SelectEquipment(), model="return")

        return_equipment(returned_items)

class EquipmentTypeList(ItemList):
    def get_items(self):
        return [_ for (_,) in session.query(Equipment.equip_type.distinct())]

    def render_item(self, h, comp, item):
        h << h.a([equipment_icon(h, item),
                  item]).action(lambda item=item: comp.answer(item))

class InventoryTask(component.Task):
    def go(self, comp):
        manboard_user = comp.call(ScanUserBarcode(["Scan manboard member's barcode", "Typically, the barcode on the back of an MIT ID card."]), model="manboard")
        if not manboard_user.is_manboard():
            comp.call(Confirm("You must be a manboard member to perform an inventory."))
        else:
            equip_type = comp.call(EquipmentTypeList())
            unselect_equipment = UnselectEquipment(manboard_user)

            all_equipment = list(Equipment.query.filter_by(equip_type=equip_type, status="ACTIVE"))

            in_equipment = set(e for e in all_equipment if not e.current_checkout)
            out_equipment = set(e for e in all_equipment if e.current_checkout)

            unselect_equipment.set_equipment(in_equipment)

            missing_equipment = set(comp.call(unselect_equipment, model="inventory"))

            found_equipment = set(unselect_equipment.all_equipment)

            # In case we found something that was checked out, check it in.
            return_equipment(found_equipment, by_manboard_user=manboard_user)

            in_equipment -= missing_equipment

            out_equipment -= found_equipment
            in_equipment += found_equipment

            mail.sendInventoryEmail(manboard_user, equip_type, missing_equipment, out_equipment, in_equipment)

class TaskWrapper(object):
    def __init__(self, label, body):
        self.label = label
        self.body = body
        #self.body.on_answer(lambda r:self.answer(r))

@presentation.render_for(TaskWrapper)
def render(self, h, comp, *args):
    if not self.body._channel:
        self.body._channel = comp._channel
    with h.div(id='header',class_=self.label+" ui-helper-clearfix"):
        h << h.a("cancel").action(lambda: comp.answer())
        h << h.div(self.label, class_="task")
    h << self.body

    return h.root

class Tnq_checkout(object):
    def __init__(self):
        self.body = component.Component(RootView())


@presentation.render_for(Tnq_checkout)
def render(self, h, *args):
    h.head.css_url('/static/tnq_checkout/styles/jquery-ui-core.css')
    h.head.css_url('/static/tnq_checkout/styles/base.css')
    h.head.javascript_url('https://ajax.googleapis.com/ajax/libs/jquery/1.6.0/jquery.min.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/scrollview.js')
    h.head.javascript_url('/static/tnq_checkout/scripts/vanillaos.js')
    h.head << h.head.title('Technique Checkout')

    with h.div(id='content'):
        h << self.body

    return h.root

# ---------------------------------------------------------------

app = Tnq_checkout
