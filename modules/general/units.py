# coding=utf-8
"""
units.py - Unit conversion module for Sopel
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Copyright © 2013, Dimitri Molenaars, <tyrope@tyrope.nl>
Licensed under the Eiffel Forum License 2.
"""
import glados
import re

find_temp = re.compile('(-?[0-9]*\.?[0-9]*)[ °]*(K|C|F)', re.IGNORECASE)
find_length = re.compile('([0-9]*\.?[0-9]*)[ ]*(mile[s]?|mi|inch|in|foot|feet|ft|yard[s]?|yd|(?:milli|centi|kilo|)meter[s]?|[mkc]?m|ly|light-year[s]?|au|astronomical unit[s]?|parsec[s]?|pc)', re.IGNORECASE)
find_mass = re.compile('([0-9]*\.?[0-9]*)[ ]*(lb|lbm|pound[s]?|ounce|oz|(?:kilo|)gram(?:me|)[s]?|[k]?g)', re.IGNORECASE)


def f_to_c(temp):
    return (float(temp) - 32) * 5 / 9


def c_to_k(temp):
    return temp + 273.15


def c_to_f(temp):
    return (9.0 / 5.0 * temp + 32)


def k_to_c(temp):
    return temp - 273.15


class Units(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('temp', '<100F/C/K>', 'Converts between all 3 units of temperature'),
            glados.Help('distance', '<42m/cm/km/miles/inch/feet/yards/ly/au/parsec>', 'Converts between units of distance'),
            glados.Help('weight', '<kg/g/lb/pounds/oz/ounces>', 'Convert between units of weight')
        ]

    @glados.Module.commands('temp')
    async def temperature(self, message, arg):
        """
        Convert temperatures
        """
        try:
            source = find_temp.match(arg).groups()
        except (AttributeError, TypeError):
            await self.client.send_message(message.channel, "That's not a valid temperature.")
            return
        unit = source[1].upper()
        numeric = float(source[0])
        celsius = 0
        if unit == 'C':
            celsius = numeric
        elif unit == 'F':
            celsius = f_to_c(numeric)
        elif unit == 'K':
            celsius = k_to_c(numeric)

        kelvin = c_to_k(celsius)
        fahrenheit = c_to_f(celsius)
        await self.client.send_message(message.channel, "{:.2f}°C = {:.2f}°F = {:.2f}K".format(celsius, fahrenheit, kelvin))


    @glados.Module.commands('length', 'distance')
    async def distance(self, message, arg):
        """
        Convert distances
        """
        try:
            source = find_length.match(arg).groups()
        except (AttributeError, TypeError):
            await self.client.send_message(message.channel, "That's not a valid length unit.")
            return
        unit = source[1].lower()
        numeric = float(source[0])
        meter = 0
        if unit in ("meters", "meter", "m"):
            meter = numeric
        elif unit in ("millimeters", "millimeter", "mm"):
            meter = numeric / 1000
        elif unit in ("kilometers", "kilometer", "km"):
            meter = numeric * 1000
        elif unit in ("miles", "mile", "mi"):
            meter = numeric / 0.00062137
        elif unit in ("inch", "in"):
            meter = numeric / 39.370
        elif unit in ("centimeters", "centimeter", "cm"):
            meter = numeric / 100
        elif unit in ("feet", "foot", "ft"):
            meter = numeric / 3.2808
        elif unit in ("yards", "yard", "yd"):
            meter = numeric / (3.2808 / 3)
        elif unit in ("light-year", "light-years", "ly"):
            meter = numeric * 9460730472580800
        elif unit in ("astronomical unit", "astronomical units", "au"):
            meter = numeric * 149597870700
        elif unit in ("parsec", "parsecs", "pc"):
            meter = numeric * 30856776376340068

        if meter >= 1000:
            metric_part = '{:.2f}km'.format(meter / 1000)
        elif meter < 0.01:
            metric_part = '{:.2f}mm'.format(meter * 1000)
        elif meter < 1:
            metric_part = '{:.2f}cm'.format(meter * 100)
        else:
            metric_part = '{:.2f}m'.format(meter)

        # Shit like this makes me hate being an American.
        inch = meter * 39.37
        foot = int(inch) // 12
        inch = inch - (foot * 12)
        yard = foot // 3
        mile = meter * 0.000621371192

        if yard > 500:
            stupid_part = '{:.2f} miles'.format(mile)
        else:
            parts = []
            if yard >= 100:
                parts.append('{} yards'.format(yard))
                foot -= (yard * 3)

            if foot == 1:
                parts.append('1 foot')
            elif foot != 0:
                parts.append('{:.0f} feet'.format(foot))

            parts.append('{:.2f} inches'.format(inch))

            stupid_part = ', '.join(parts)

        await self.client.send_message(message.channel, '{} = {}'.format(metric_part, stupid_part))

    @glados.Module.commands('weight', 'mass')
    async def mass(self, message, arg):
        """
        Convert mass
        """
        if 'your' in arg and 'mom' in arg:
            await self.client.send_message(message.channel, 'Too large to weigh')
            return

        try:
            source = find_mass.match(arg).groups()
        except (AttributeError, TypeError):
            await self.client.send_message(message.channel, "That's not a valid mass unit.")
            return
        unit = source[1].lower()
        numeric = float(source[0])
        metric = 0
        if unit in ("gram", "grams", "gramme", "grammes", "g"):
            metric = numeric
        elif unit in ("kilogram", "kilograms", "kilogramme", "kilogrammes", "kg"):
            metric = numeric * 1000
        elif unit in ("lb", "lbm", "pound", "pounds"):
            metric = numeric * 453.59237
        elif unit in ("oz", "ounce"):
            metric = numeric * 28.35

        if metric >= 1000:
            metric_part = '{:.2f}kg'.format(metric / 1000)
        else:
            metric_part = '{:.2f}g'.format(metric)

        ounce = metric * .035274
        pound = int(ounce) // 16
        ounce = ounce - (pound * 16)

        if pound > 1:
            stupid_part = '{} pounds'.format(pound)
            if ounce > 0.01:
                stupid_part += ' {:.2f} ounces'.format(ounce)
        else:
            stupid_part = '{:.2f} oz'.format(ounce)

        await self.client.send_message(message.channel, '{} = {}'.format(metric_part, stupid_part))
