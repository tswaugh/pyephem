#!/usr/bin/env python

import sys, unittest
from glob import glob
from sets import Set

class TestError(Exception):
    pass

# Work backwords from the `test' directory in which this script sits
# to find where the distutils have placed the new module; note that
# this attempt to file the `lib.*' directory will fail if the user has
# created several by building the module for several architectures.

(build_lib,) = glob(sys.path[0] + '/../build/lib.*')
sys.path.insert(0, build_lib)

# Now we can import the module.

import ephem
from ephem import *
#import test_ephem

class MyTestCase(unittest.TestCase):
    def assertRaises(self, exception, callable, *args):
        try:
            unittest.TestCase.assertRaises(self, exception, callable, *args)
        except AssertionError:
            raise AssertionError, ('%r failed to raise %s with arguments %r'
                                   % (callable, exception, args))

#print dir(ephem)
#print ephem.Date, ephem.Body
#sys.exit(0)

class angles(unittest.TestCase):
    def setUp(self):
        self.d = degrees(1.5)
        self.h = hours(1.6)

    def test_degrees_constructor(self):
        self.assertEqual(self.d, degrees('85:56:37.20937064454'))
    def test_degrees_float_value(self):
        self.assertEqual(self.d, 1.5)
    def test_degrees_string_value(self):
        self.assertEqual(str(self.d), '85:56:37.21')

    def test_hours_constructor(self):
        self.assertEqual(self.h, hours('6:06:41.579333023612'))
    def test_hours_float_value(self):
        self.assertEqual(self.h, 1.6)
    def test_hours_string_value(self):
        self.assertEqual(str(self.h), '6:06:41.58')

#
#

class dates(unittest.TestCase):
    def setUp(self):
        self.date = Date('2004/09/04 00:17:15.8')

    def test_date_constructor(self):
        std = ('2004/09/04 00:17:15.8',)
        pairs = [std, ('2004.67489614324023472',),
                 std, ('2004/9/4.0119884259259257',),
                 std, ('2004/9/4 0.28772222222222221',),
                 std, ('2004/9/4 0:17.263333333333332',),
                 std, ('2004/9/4 0:17:15.8',),
                 ('2004',), ((2004,),),
                 ('2004/09',), ((2004, 9),),
                 std, ((2004, 9, 4.0119884259259257),),
                 std, ((2004, 9, 4, 0.28772222222222221),),
                 std, ((2004, 9, 4, 0, 17.263333333333332),),
                 std, ((2004, 9, 4, 0, 17, 15.8),),
                 ]
        for i in range(0, len(pairs), 2):
            args1, args2 = pairs[i:i+2]
            d1, d2 = Date(*args1), Date(*args2)
            self.assert_(-1e-15 < (d1 / d2 - 1) < 1e-15,
                         'dates not equal:\n %r = date%r\n %r = date%r'
                         % (d1.tuple(), args1, d2.tuple(), args2))

    def test_date_string_value(self):
        self.assertEqual(str(self.date), '2004/9/4 00:17:15')

    def test_date_triple_value(self):
        self.assertEqual(self.date.triple(), (2004, 9, 4.0119884259256651))

    def test_date_triple_value(self):
        self.assertEqual(self.date.tuple(),
                         (2004, 9, 4, 0, 17, 15.799999977461994))

# fixed

satellite_attributes = ('sublat', 'sublong', 'elevation',
                        'range', 'range_velocity', 'eclipsed')

attribute_list = (
    (Body, False,
     ('ra', 'dec', 'elong', 'mag', 'size')),
    (Body, True,
     ('az', 'alt', 'apparent_ra', 'apparent_dec',
      'circumpolar', 'neverup', 'rise_time', 'rise_az',
      'transit_time', 'transit_alt', 'set_time', 'set_az')),
    (Planet, False,
     ('hlong', 'hlat', 'sun_distance', 'earth_distance', 'phase')),
    (Moon, False,
     ('colong', 'subsolar_lat', 'libration_lat', 'libration_long')),
    (Saturn, False,
     ('earth_tilt', 'sun_tilt')),
    )

# Return a dictionary whose keys are all known body attributes,
# and whose values are the exceptions we expect to receive for
# trying to access each attribute from the given body, or the
# value True for attributes which should not raise exceptions.

def predict_attributes(body, was_computed, was_given_observer):
    predictions = {}
    for bodytype, needs_observer, attrs in attribute_list:
        for attr in attrs:
            if not isinstance(body, bodytype):
                predictions[attr] = AttributeError
            elif not was_computed:
                predictions[attr] = RuntimeError
            elif needs_observer and not was_given_observer:
                predictions[attr] = RuntimeError
            else:
                predictions[attr] = None
    return predictions

#

class bodies(MyTestCase):
    def setUp(self):
        self.date = Date('1955/05/21')

        self.obs = obs = Observer()
        obs.lat, obs.long, obs.elev = '33:45:10', '-84:23:37', 320.0
        obs.date = '1997/2/15'

    # Try accessing each attribute in attribute_list from the given
    # body, recording the exceptions we receive in a dictionary, and
    # storing True for attributes whose access raises no exception.

    def measure_attributes(self, body):
        attributes = {}
        for bodytype, needs_observer, attrs in attribute_list:
            for attr in attrs:
                try:
                    getattr(body, attr)
                except:
                    attributes[attr] = sys.exc_info()[1]
                else:
                    attributes[attr] = None
        return attributes

    # Use the above two functions to predict which attributes of the
    # given body should be accessible, and then test to see whether
    # the reality matches our prediction.

    def compare_attributes(self, body, was_computed, was_given_observer):
        p = predict_attributes(body, was_computed, was_given_observer)
        t = self.measure_attributes(body)
        for a in Set(p).union(t):
            if p[a] is None and t[a] is None:
                continue
            if p[a] and isinstance(t[a], p[a]):
                continue
            if was_computed:
                if was_given_observer:
                    adjective = 'topo'
                else:
                    adjective = 'geo'
                adjective += 'centrically computed'
            else:
                adjective = 'uncomputed'
            raise TestError('accessing %s of %s %s '
                            'raised %r "%s" instead of %r'
                            % (a, adjective, body,
                               t[a], t[a].args[0], p[a]))

    def run(self, body):
        self.compare_attributes(body, False, False)
        body.compute()
        self.compare_attributes(body, True, False)
        body.compute(self.obs)
        self.compare_attributes(body, True, True)
        body.compute()
        self.compare_attributes(body, True, False)

    def test_Planets(self):
        for init in (Mercury, Venus, Mars, Jupiter, Saturn,
                     Uranus, Neptune, Pluto, Sun, Moon):
            self.run(init())

    # For each flavor of user-definable body, 

    def build(self, bodytype, line, attributes):

        # Build one body from the Ephem-formatted entry.

        bl = readdb(line)

        # Build another body by setting the attributes on a body.

        ba = bodytype()
        for attribute, value in attributes.iteritems():
            try:
                setattr(ba, attribute, value)
            except TypeError:
                raise TestError, ('cannot modify attribute %s of %r: %s'
                                  % (attribute, ba, sys.exc_info()[1]))
        if not isinstance(bl, bodytype):
            raise TestError, ('ephem database entry returned type %s'
                              ' rather than type %s' % (type(bl), bodytype))

        # Now, compare the bodies to see if they are equivalent.
        # First test whether they present the right attributes.

        self.run(bl), self.run(ba)

        # Check whether they appear in the same positions.

        for circumstance in self.date, self.obs:
            is_observer = isinstance(circumstance, Observer)
            bl.compute(circumstance), ba.compute(circumstance)
            attrs = [ a for (a,e)
                      in predict_attributes(bl, 1, is_observer).items()
                      if not e ]
            for attr in attrs:
                vl, va = getattr(bl, attr), getattr(ba, attr)
                if isinstance(vl, float):
                    vl, va = str(float(vl)), str(float(va))
                #print attr, vl, va
                if vl != va:
                    raise TestError, ("%s item from line returns %s for %s"
                                      " but constructed object returns %s"
                                      % (type(bl), vl, attr, va))

    def test_FixedBody(self):
        self.build(
            bodytype=FixedBody,
            line='Achernar,f|V|B3,1:37:42.9,-57:14:12,0.46,2000',
            attributes = {'name': 'Achernar',
                          '_ra': '1:37:42.9', '_dec': '-57:14:12',
                          'mag': 0.46, '_epoch': '2000'})

    def test_EllipticalBody(self):
        self.build(
            bodytype=EllipticalBody,
            line=('C/1995 O1 (Hale-Bopp),e,89.3918,282.4192,130.8382,'
                  '186.4302,0.0003872,0.99500880,0.0000,'
                  '03/30.4376/1997,2000,g -2.0,4.0'),
            attributes = {'name': 'Hale-Bopp', '_inc': 89.3918,
                          '_Om': 282.4192, '_om': 130.8382,
                          '_a': 186.4302, '_e': 0.99500880, '_M': 0.0000,
                          '_cepoch': '1997/03/30.4376', '_epoch': '2000',
                          '_size': 0, '_g': -2.0, '_k': 4.0
                          })

    #def test_sanity(self):
    #    s = Sun()
    #    s.compute(self.obs)
    #    


class riset(MyTestCase):
    def setUp(self):
        self.obs = obs = Observer()
        obs.lat, obs.long, obs.elev = '33:45:10', '-84:23:37', 320.0
        obs.date = '1997/2/15'

        self.polaris = readdb('Polaris,f|M|F7,2:31:48.704,89:15:50.72,2.02,2000')
        self.rigel = readdb('Rigel,f|M|B8,5:14:32.3,-8:12:6,0.12,2000')

if __name__ == '__main__':
    unittest.main()

sys.exit(0)

line=('C/1995 O1 (Hale-Bopp),e,89.3918,282.4192,130.8382,'
      '186.4302,0.0003872,0.99500880,0.0000,'
      '03/30.4376/1997,2000,g -2.0,4.0')
bopp = readdb(line)
for a in dir(bopp):
    try:
        print a, getattr(bopp, a)
    except:
        print a, '---'