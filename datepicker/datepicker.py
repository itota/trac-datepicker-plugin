# Copyright (c) 2010, Takashi Ito
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the authors nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import re
from trac.core import *
from trac.config import Option, IntOption, ListOption, BoolOption, Configuration
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, add_stylesheet, ITemplateProvider
from genshi.builder import tag
from genshi.filters.transform import Transformer


class DatepickerModule(Component):

    implements(ITemplateProvider, ITemplateStreamFilter)

    target_path = Option('datepicker', 'target_path', '^/(ticket|newticket|report/)')
    target_fields = ListOption('datepicker', 'target_fields')

    button_image_path = 'datepicker/css/images/calendar.gif'
    option_map = dict([(x.lower(), x) for x in [
        'altField',
        'altFormat',
        'appendText',
        'beforeShow',
        'beforeShowDay',
        'buttonImage',
        'buttonImageOnly',
        'buttonText',
        'calculateWeek',
        'changeMonth',
        'changeYear',
        'constrainInput',
        'dateFormat',
        'defaultDate',
        'duration',
        'gotoCurrent',
        'hideIfNoPrevNext',
        'maxDate',
        'minDate',
        'navigationAsDateFormat',
        'numberOfMonths',
        'onChangeMonthYear',
        'onClose',
        'onSelect',
        'shortYearCutoff',
        'showAnim',
        'showButtonPanel',
        'showCurrentAtPos',
        'showMonthAfterYear',
        'showOn',
        'showOptions',
        'showOtherMonths',
        'stepBigMonths',
        'stepMonths',
        'yearRange',
    ]])

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('datepicker', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    def get_options(self, req, id):
        if not hasattr(self, 'datepicker_options'):
            ex = ['target_path', 'target_fields']
            options = dict(filter(lambda x: not (x[0] in ex or '.' in x[0]), self.config.options('datepicker')))
            # check if buttonImage needs to be added
            has_image = options.get('buttonimage')
            need_image = options.get('showon') in ('"button"', '"both"')
            # add button image if needed
            if need_image and not has_image:
                options['buttonImage'] = '"%s"' % req.href.chrome(self.button_image_path)
            # check individual options
            ext_options = filter(lambda x: '.' in x[0], self.config.options('datepicker'))
            ext_keys = set(map(lambda x: x[0].split('.', 1)[0], ext_options))
            # save options
            self.datepicker_options = {}
            for k in self.target_fields:
                if k in ext_keys:
                    tmp = dict(options)
                    ext_options = filter(lambda x: x[0].startswith(k), ext_options)
                    ext_options = dict([(x.split('.', 1)[1], y) for x, y in ext_options])
                    tmp.update(ext_options)
                else:
                    tmp = options
                self.datepicker_options[k] = ', '.join(['%s: %s' % (self.option_map.get(x, x), y) for x, y in tmp.items()])
        return self.datepicker_options.get(id)

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        # compile pattern
        if not hasattr(self, 'pattern'):
            self.pattern = re.compile(self.target_path)
        # check if the path matches
        if self.pattern.match(req.path_info):
            add_stylesheet(req, 'datepicker/css/ui.core.css')
            add_stylesheet(req, 'datepicker/css/ui.theme.css')
            add_stylesheet(req, 'datepicker/css/ui.datepicker.css')
            add_script(req, 'datepicker/js/jquery.ui.core.js')
            add_script(req, 'datepicker/js/jquery.ui.datepicker.js')
            lines = '\n'.join(['  $("#%s").datepicker({%s});' % (x, self.get_options(req, x)) for x in self.target_fields])
            code = 'jQuery(document).ready(function($) {\n%s\n});' % lines
            script = tag.script(code, type='text/javascript')
            return stream | Transformer('head').append(script)
        else:
            return stream

