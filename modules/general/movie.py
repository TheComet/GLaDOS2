# coding=utf-8
"""
imdb.py - Sopel Movie Information Module
Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.
This module relies on omdbapi.com
"""
import glados
import requests
import json


class Movie(glados.Module):

    def get_help_list(self):
        return [
            glados.Help('movie/imdb', '<title>', 'Searches for the movie on IMDB')
        ]

    @glados.Module.commands('movie', 'imdb')
    def movie(self, message, movie):
        """
        Returns some information about a movie, like Title, Year, Rating, Genre and IMDB Link.
        """
        if movie == '':
            await self.provide_help('imdb', message)
            return

        movie = movie.rstrip()
        uri = "http://www.omdbapi.com/"
        data = requests.get(uri, params={'t': movie}, timeout=30).json()
        if data['Response'] == 'False':
            if 'Error' in data:
                response = '[MOVIE] %s' % data['Error']
                response += '\n**I am looking for a movie API, this one has gone private! If you know of one, let TheComet know about it!**'
            else:
                glados.log(
                    'Got an error from the OMDb api, search phrase was {0}; data was {1}'.format(movie, str(data)))
                response = '[MOVIE] Got an error from OMDbapi'
        else:
            response = '[MOVIE] Title: ' + data['Title'] + \
                      ' | Year: ' + data['Year'] + \
                      ' | Rating: ' + data['imdbRating'] + \
                      ' | Genre: ' + data['Genre'] + \
                      ' | IMDB Link: http://imdb.com/title/' + data['imdbID']
        await self.client.send_message(message.channel, response)
