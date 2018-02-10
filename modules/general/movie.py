# coding=utf-8
"""
imdb.py - Sopel Movie Information Module
Copyright © 2012-2013, Elad Alfassa, <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.
This module relies on omdbapi.com
"""
import glados
import requests


class Movie(glados.Module):
    @glados.Module.command('movie', '<title>', 'Searches for the movie on IMDB')
    @glados.Module.command('imdb', '', '')
    async def movie(self, message, movie):
        """
        Returns some information about a movie, like Title, Year, Rating, Genre and IMDB Link.
        """

        movie = movie.rstrip()
        uri = "http://www.theapache64.com/movie_db/search"
        data = requests.get(uri, params={'keyword': movie}, timeout=10).json()
        if data['error']:
            response = data['message']
        else:
            data = data['data']
            response = 'Title: ' + data.get('name', '?') + '\n' + \
                      ' | Year: ' + data.get('year', '?') + '\n' + \
                      ' | Rating: ' + data.get('rating', '?') + '\n' + \
                      ' | Genre: ' + data.get('genre', '?') + '\n' + \
                      ' | Plot: ' + data.get('plot', '?') + '\n' + \
                      ' | IMDB Link: http://www.imdb.com/title/' + data['imdb_id']
        await self.client.send_message(message.channel, response)
