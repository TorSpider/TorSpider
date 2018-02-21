from html.parser import HTMLParser


class ParseLinks(HTMLParser):
    # Parse given HTML for all a.href links.
    def __init__(self):
        HTMLParser.__init__(self)
        self.output_list = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.output_list.append(dict(attrs).get('href'))


class ParseTitle(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.match = False
        self.title = ''

    def handle_starttag(self, tag, attributes):
        self.match = True if tag == 'title' else False

    def handle_data(self, data):
        if self.match:
            self.title = data
            self.match = False


class FormParser(HTMLParser):
    ''' Here's the format of the FormParser's output (list of dictionaries):
        [{
            'action': 'page.html',
            'method': 'get/put',
            'target': 'whatever',
            'text_fields': {
                'name': 'default value'
            },
            'radio_buttons': {
                'name': ['values']
            },
            'checkboxes': {
                'name': ['values']
            },
            'dropdowns': {
                'name': ['values']
            },
            'text_areas': {
                'name': 'default value'
            },
            'dates': [names],
            'datetimes': [names],
            'months': [names],
            'numbers': [names],
            'ranges': [names],
            'times': [names],
            'weeks': [names]
        }]
        There's one list entry per form on the page.
    '''
    def __init__(self):
        HTMLParser.__init__(self)
        self.found = False
        self.forms = []
        self.text_area = False
        self.selecting = False
        self.reset_fields()

    def handle_starttag(self, tag, attrs):
        if(tag == 'form'):
            # We're starting a fresh form.
            self.reset_fields()
            self.form.append(('action', dict(attrs).get('action')))
            self.form.append(('method', dict(attrs).get('method')))
            self.form.append(('target', dict(attrs).get('target')))
        elif(tag == 'textarea'):
            # We're starting a text area.
            self.text_area_name = dict(attrs).get('name')
            self.text_area = True
            self.text_area_value = ''
        elif(tag == 'select'):
            # We're starting a selection.
            self.selecting = True
            self.select_name = dict(attrs).get('name')
            self.select_options = []
        elif(tag == 'option'):
            # It's part of a select field.
            self.select_options.append(dict(attrs).get('value'))
        elif(tag == 'input'):
            input_type = dict(attrs).get('type')
            input_name = dict(attrs).get('name')
            try:
                input_value = dict(attrs).get('value')
            except Exception as e:
                input_value = 'none'
            if(self.found is True and input_type != 'submit'):
                if(input_type == 'text'
                   or input_type == 'password'
                   or input_type == 'email'
                   or input_type == 'search'
                   or input_type == 'tel'
                   or input_type == 'url'):
                    # Add the text field and its default value to the dict.
                    self.text_fields[input_name] = input_value
                elif(input_type == 'date'):
                    # It's a date.
                    self.dates.append(input_name)
                elif(input_type == 'datetime-local'):
                    # It's a datetime-local.
                    self.datetimes.append(input_name)
                elif(input_type == 'month'):
                    # It's a month.
                    self.months.append(input_name)
                elif(input_type == 'number'):
                    # It's a number.
                    self.numbers.append(input_name)
                elif(input_type == 'range'):
                    # It's a range.
                    self.ranges.append(input_name)
                elif(input_type == 'time'):
                    # It's a time.
                    self.times.append(input_name)
                elif(input_type == 'week'):
                    # It's a week.
                    self.weeks.append(input_name)
                elif(input_type == 'checkbox'):
                    if(input_name in self.checkboxes.keys()):
                        # The checkbox already exists. Add its value.
                        self.checkboxes[input_name].append(input_value)
                    else:
                        # The checkbox doesn't exist. Create it.
                        self.checkboxes[input_name] = [input_value]
                elif(input_type == 'radio'):
                    if(input_name in self.radio_buttons.keys()):
                        # The radio button already exists, add its value.
                        self.radio_buttons[input_name].append(input_value)
                    else:
                        # The radio button doesn't exist. Create it.
                        self.radio_buttons[input_name] = [input_value]

    def handle_data(self, data):
        if(self.text_area is True):
            # We're looking at the text area data.
            self.text_area_value = data.strip()

    def handle_endtag(self, tag):
        if(tag == 'form'):
            # Closing out a form.
            self.found = False
            self.form.append(('text_fields', self.text_fields))
            self.form.append(('radio_buttons', self.radio_buttons))
            self.form.append(('checkboxes', self.checkboxes))
            self.form.append(('dropdowns', self.dropdowns))
            self.form.append(('text_areas', self.text_areas))
            self.form.append(('dates', self.dates))
            self.form.append(('datetimes', self.datetimes))
            self.form.append(('months', self.months))
            self.form.append(('numbers', self.numbers))
            self.form.append(('ranges', self.ranges))
            self.form.append(('times', self.times))
            self.form.append(('weeks', self.weeks))
            self.forms.append(self.form)
        elif(tag == 'textarea'):
            # Closing out a text area.
            self.text_area = False
            self.text_areas[self.text_area_name] = self.text_area_value
            self.text_area_name = ''
        elif(tag == 'select'):
            # Closing out a selection.
            self.dropdowns[self.select_name] = self.select_options
            self.select_name = ''
            self.select_options = []
            self.selecting = False

    def reset_fields(self):
        self.found = True
        self.form = []
        self.select_options = []
        self.text_fields = {}
        self.text_area_value = ''
        self.radio_buttons = {}
        self.checkboxes = {}
        self.dropdowns = {}
        self.text_areas = {}
        self.dates = []
        self.datetimes = []
        self.months = []
        self.numbers = []
        self.ranges = []
        self.times = []
        self.weeks = []
