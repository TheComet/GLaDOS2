# coding=utf-8
# Copyright 2008, Sean B. Palmer, inamidst.com
# Copyright 2012, Elsie Powell, embolalia.com
# Licensed under the Eiffel Forum License 2.
import glados
import os
import json
import urllib.request
import urllib.parse
import xmltodict
import random


def woeid_search(query):
    """
    Find the first Where On Earth ID for the given query. Result is the etree
    node for the result, so that location data can still be retrieved. Returns
    None if there is no result, or the woeid field is empty.
    """
    glados.log('woeid_search for: "{}"'.format(query))
    query = urllib.parse.quote('select * from geo.places where text="{}"'.format(query))
    query = 'http://query.yahooapis.com/v1/public/yql?q=' + query
    glados.log('Request: {}'.format(query))
    body = urllib.request.urlopen(query).read()
    parsed = xmltodict.parse(body).get('query')
    results = parsed.get('results')
    if results is None or results.get('place') is None:
        return None
    if type(results.get('place')) is list:
        return results.get('place')[0]
    return results.get('place')


def get_cover(parsed):
    try:
        condition = parsed['channel']['item']['yweather:condition']
    except KeyError:
        return 'unknown'
    text = condition['@text']
    # code = int(condition['code'])
    # TODO parse code to get those little icon thingies.
    return text


def get_temp(parsed):
    try:
        condition = parsed['channel']['item']['yweather:condition']
        temp = int(condition['@temp'])
    except (KeyError, ValueError):
        return 'unknown'
    f = round((temp * 1.8) + 32, 2)
    return (u'%d\u00B0C (%d\u00B0F)' % (temp, f))


def get_humidity(parsed):
    try:
        humidity = parsed['channel']['yweather:atmosphere']['@humidity']
    except (KeyError, ValueError):
        return 'unknown'
    return "Humidity: %s%%" % humidity


def get_wind(parsed):
    try:
        wind_data = parsed['channel']['yweather:wind']
        kph = float(wind_data['@speed'])
        m_s = float(round(kph / 3.6, 1))
        speed = int(round(kph / 1.852, 0))
        degrees = int(wind_data['@direction'])
    except (KeyError, ValueError):
        return 'unknown'

    if speed < 1:
        description = 'Calm'
    elif speed < 4:
        description = 'Light air'
    elif speed < 7:
        description = 'Light breeze'
    elif speed < 11:
        description = 'Gentle breeze'
    elif speed < 16:
        description = 'Moderate breeze'
    elif speed < 22:
        description = 'Fresh breeze'
    elif speed < 28:
        description = 'Strong breeze'
    elif speed < 34:
        description = 'Near gale'
    elif speed < 41:
        description = 'Gale'
    elif speed < 48:
        description = 'Strong gale'
    elif speed < 56:
        description = 'Storm'
    elif speed < 64:
        description = 'Violent storm'
    else:
        description = 'Hurricane'

    if (degrees <= 22.5) or (degrees > 337.5):
        degrees = u'\u2193'
    elif (degrees > 22.5) and (degrees <= 67.5):
        degrees = u'\u2199'
    elif (degrees > 67.5) and (degrees <= 112.5):
        degrees = u'\u2190'
    elif (degrees > 112.5) and (degrees <= 157.5):
        degrees = u'\u2196'
    elif (degrees > 157.5) and (degrees <= 202.5):
        degrees = u'\u2191'
    elif (degrees > 202.5) and (degrees <= 247.5):
        degrees = u'\u2197'
    elif (degrees > 247.5) and (degrees <= 292.5):
        degrees = u'\u2192'
    elif (degrees > 292.5) and (degrees <= 337.5):
        degrees = u'\u2198'

    return description + ' ' + str(m_s) + 'm/s (' + degrees + ')'


class Weather(glados.Module):
    counter = 0
    def __init__(self, server_instance, full_name):
        super(Weather, self).__init__(server_instance, full_name)

        self.woeid_db = dict()
        self.woeid_db_file = os.path.join(self.local_data_dir, 'woeid_db.json')
        self.__load_locations()

    def __load_locations(self):
        if os.path.isfile(self.woeid_db_file):
            self.woeid_db = json.loads(open(self.woeid_db_file).read())

    def __update_location(self, author, location):
        self.woeid_db[author.lower()] = location
        with open(self.woeid_db_file, 'w') as f:
            f.write(json.dumps(self.woeid_db))

    @glados.Module.command('weather', '[location]', 'Returns the weather. If the location is not specified, then your '
                           'location (from .setlocation) is used')
    async def weather(self, message, location):
        """.weather location - Show the weather at the given location."""

        # Troll Oberon
        if message.author.id == '212714897606180864':
            msgs = [
                "IT'S FUCKING COLD OK",
                "Unknown command - did you spell it right?",
                "https://i.imgur.com/bQOiAJj.jpg",
                "Tonight's Forecast: Dark",
                "https://vignette.wikia.nocookie.net/uncyclopedia/images/9/9d/Weather-silly-eyes2.gif",
                "https://i.imgur.com/EFlH21H.png",
                "There are Canadians",
                "https://i.imgur.com/SzGtXjN.jpg"
            ]
            self.counter += 1
            if self.counter >= len(msgs):
                self.counter = 0
            return await self.client.send_message(message.channel, msgs[self.counter])

        woeid = ''
        author = message.author.name
        key = author.lower()
        if location == '':
            try:
                woeid = self.woeid_db[key]
            except KeyError:
                await self.client.send_message(message.channel, "I don't know where you live. " +
                               'Give me a location, like .weather London, or tell me where you live by saying .setlocation London, for example.')
                return
        else:
            location = location.strip()
            try:
                woeid = self.woeid_db[location.lower()]  # assume location is a user first
            except KeyError:
                first_result = woeid_search(location)
                if first_result is not None:
                    woeid = first_result.get('woeid')

        if not woeid:
            await self.client.send_message(message.channel, "I don't know where that is.")
            return

        query = urllib.parse.quote('select * from weather.forecast where woeid="{}" and u=\'c\''.format(woeid))
        query = 'http://query.yahooapis.com/v1/public/yql?q=' + query
        glados.log('Request: {}'.format(query))

        body = urllib.request.urlopen(query).read()
        parsed = xmltodict.parse(body).get('query')
        results = parsed.get('results')
        if results is None:
            await self.client.send_message(message.channel, "No forecast available. Try a more specific location.")
            return
        location = results.get('channel').get('title')
        cover = get_cover(results)
        temp = get_temp(results)
        humidity = get_humidity(results)
        wind = get_wind(results)
        await self.client.send_message(message.channel, u'%s: %s, %s, %s, %s' % (location, cover, temp, humidity, wind))

    @glados.Module.command('setlocation', '<location>', 'Sets your location. The .weather command can use your '
                           'location to look up weather.')
    async def update_woeid(self, message, location):
        """Set your default weather location."""
        if location == '':
            await self.provide_help('setlocation', message)
            return

        first_result = woeid_search(location)
        if first_result is None:
            await self.client.send_message(message.channel, "I don't know where that is.")
            return

        woeid = first_result.get('woeid')

        author = message.author.name
        self.__update_location(author, woeid)

        neighborhood = first_result.get('locality2') or ''
        if neighborhood:
            neighborhood = neighborhood.get('#text') + ', '
        city = first_result.get('locality1') or ''
        # This is to catch cases like 'Bawlf, Alberta' where the location is
        # thought to be a "LocalAdmin" rather than a "Town"
        if city:
            city = city.get('#text')
        else:
            city = first_result.get('name')
        state = first_result.get('admin1').get('#text') or ''
        country = first_result.get('country').get('#text') or ''

        await self.client.send_message(message.channel, 'I now have you at WOEID %s (%s%s, %s, %s)' %
                                            (woeid, neighborhood, city, state, country))

    @glados.Module.command('location', '[user]', 'Returns the location of a user, or your location if no user was '
                                              'specified.')
    async def get_woeid(self, message, user):
        if user == '':
            user = message.author.name

        try:
            woeid = self.woeid_db[user.lower()]

            query = urllib.parse.quote('select * from weather.forecast where woeid="{}" and u=\'c\''.format(woeid))
            query = 'http://query.yahooapis.com/v1/public/yql?q=' + query
            glados.log('Request: {}'.format(query))

            body = urllib.request.urlopen(query).read()
            parsed = xmltodict.parse(body).get('query')
            results = parsed.get('results')

            if results is None:
                await self.client.send_message(message.channel, 'Couldn\'t look up location. The WOEID of {} is: {}'.format(user, woeid))
                return

            location = results.get('channel').get('title')
            await self.client.send_message(message.channel, 'Location of {} is {}'.format(user, location))
        except KeyError:
            await self.client.send_message(message.channel, 'No location set. You can use .setlocation to set one')
