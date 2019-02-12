import random
import os
import subprocess
import glados
import discord


LATEX_FRAMEWORK = r"""
\documentclass[varwidth=true]{standalone}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{color}
\usepackage[usenames,dvipsnames,svgnames,table]{xcolor}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{esint}
\usepackage{listings}
\usepackage{mathtools}
\usepackage{trfsigns}
\usepackage{mathrsfs}
\usepackage{mathtools}
%\usepackage{skull}
\usepackage{siunitx}
%\usepackage[american,europeanvoltages]{circuitikz}

% Required for tikz plots
\usepackage{pgfplots}
\pgfplotsset{compat=newest}
\usetikzlibrary{plotmarks}
\usetikzlibrary{arrows.meta}
\usepgfplotslibrary{patchplots}
\usepackage{grffile}

\sisetup{output-exponent-marker=\ensuremath{\mathrm{E}}}

\DeclarePairedDelimiter\ceil{\lceil}{\rceil}
\DeclarePairedDelimiter\floor{\lfloor}{\rfloor}
\DeclarePairedDelimiter\abs{\lvert}{\rvert}%
\DeclarePairedDelimiter\norm{\lVert}{\rVert}%

% Swap the definition of \abs* and \norm*, so that \abs
% and \norm resizes the size of the brackets, and the
% starred version does not.
\makeatletter
\let\oldabs\abs
\def\abs{\@ifstar{\oldabs}{\oldabs*}}
%
\let\oldnorm\norm
\def\norm{\@ifstar{\oldnorm}{\oldnorm*}}
\makeatother

%\newcommand{\knochen}[0]{\fourier}
\renewcommand{\L}[1]{\mathscr{L}\left\{#1\right\}}
\newcommand{\F}[1]{\mathscr{F}\left\{#1\right\}}

\newcommand{\rz}[1]{
    \begin{pmatrix}
        \cos{#1} & -\sin{#1} & 0 \\
        \sin{#1} & \cos{#1} & 0 \\
        0 & 0 & 1 \\
    \end{pmatrix}
}
\newcommand{\ry}[1]{
    \begin{pmatrix}
        \cos{#1} & 0 & \sin{#1} \\
        0 & 1 & 0 \\
        -\sin{#1} & 0 & \cos{#1} \\
    \end{pmatrix}
}
\newcommand{\rx}[1]{
    \begin{pmatrix}
        1 & 0 & 0 \\
        0 & \cos{#1} & -\sin{#1} \\
        0 & \sin{#1} & \cos{#1} \\
    \end{pmatrix}
}

\begin{document}
{\color{White}
__DATA__}
\end{document}
"""

MATH_ENV = r"""
\begin{align*}
__DATA__
\end{align*}
"""

CIRCUIT_ENV = r"""
\begin{circuitikz}
__DATA__
\end{circuitikz}
"""

class LaTeX(glados.Module):

    def __init__(self, bot, full_name):
        super(LaTeX, self).__init__(bot, full_name)
        self.__out_folder = 'tex'
        self.__latex_blacklist = ("\\write18",
                                  "\\input",
                                  "\\include",
                                  "{align*}",
                                  "\\loop",
                                  "\\repeat",
                                  "\\csname",
                                  "\\endcsname")
        self.__last_messages = dict()  # map username to message objects

    @staticmethod
    def math(latex_code):
        return LATEX_FRAMEWORK.replace('__DATA__', MATH_ENV).replace('__DATA__', latex_code)
    @staticmethod
    def circuit(latex_code):
        return LATEX_FRAMEWORK.replace('__DATA__', CIRCUIT_ENV).replace('__DATA__', latex_code)

    def generate_image(self, latex, gen_func):

        num = str(random.randint(0, 2 ** 31))
        latex_file = os.path.join(self.__out_folder, num + '.tex')
        dvi_file   = os.path.join(self.__out_folder, num + '.dvi')
        png_file   = os.path.join(self.__out_folder, num + '1.png')
        latex_cmd  = ['latex',
                      '-no-shell-escape',
                      '-interaction', 'nonstopmode',
                      '-halt-on-error',
                      '-file-line-error',
                      '-output-directory=' + self.__out_folder,
                      latex_file]
        dvipng_cmd = ['dvipng', '-q*', '-D', '200', '-T', 'tight', '-bg', 'Transparent', '-o', png_file, dvi_file]

        with open(latex_file, 'w') as tex:
            latex = gen_func(latex)
            tex.write(latex)
            tex.flush()
            tex.close()

        try:
            glados.log('executing latex: {}'.format(latex_cmd))
            subprocess.check_output(latex_cmd)
        except subprocess.CalledProcessError as e:
            latex_cmd_output = '\n'.join(str(e.output).split('\\n'))
            glados.log(latex_cmd_output)
            errors = [x.strip() for x in str(e.output).split('\\n') if x.startswith('!') or '.tex:' in x]
            lines = [int(x) - 2 for error in errors for x in error.split(':') if x.isdigit()]
            latexlines = [x for n, x in enumerate(latex.split('\n')) if n in lines]
            errormsg = "Error: {0}\n{1}".format('\n'.join([x.strip() for x in str(e.output).split('\\n') if x.startswith('!') or '.tex:' in x]),
                                         '\n'.join(latexlines))
            glados.log('Failed. Latex output: {0}\nGenerated error message: {1}'.format(latex_cmd_output, errormsg))
            return False, errormsg

        subprocess.call(dvipng_cmd)

        return True, png_file

    @glados.Module.command('math', '<latex code>', 'Render latex math code. The code you provide is placed between \\begin{align} and \\end{align}.')
    async def math_cmd(self, message, content):
        if any(x in content for x in self.__latex_blacklist):
            glados.log('LaTeX: Blacklisted commands detected!\n'
                       '  Author: {0}\n  Message: {1}\n  Server: {2}\n  Channel: {3}'.format(
                message.author.name,
                message.content,
                message.server.name,
                message.channel.name
            ))
            await self.client.send_message(message.channel, "Error: Trying to be naughty, are we?")
            return

        # check if this is an edited message
        if message.edited_timestamp:
            last_msg = self.__last_messages.pop(message.author.id, None)
            if last_msg is not None and last_msg[0].id == message.id:
                await self.client.delete_message(last_msg[1])

        # troll Cul
        if message.author.id == '113128686969958400' and random.random() < 0.02:
            content = "\\color{pink} \\text{CulDeVu  loves dongers}"

        fn = self.generate_image(content, self.math)

        if not fn[0]:
            await self.client.send_message(message.channel, fn[1])
            return
        if os.path.getsize(fn[1]) > 0:
            try:
                self.__last_messages[message.author.id] = (
                    message,
                    await self.client.send_file(message.channel, fn[1])
                )
            except discord.errors.Forbidden:
                error = 'Error: Insufficient permissions to send file files to channel #{}'.format(message.channel.name)
                glados.log(error)
                await self.client.send_message(message.channel, error)

    @glados.Module.command('circuit', '<latex code>', 'Render latex math code. The code you provide is placed between \\begin{align} and \\end{align}.')
    async def circuit_cmd(self, message, content):
        if any(x in content for x in self.__latex_blacklist):
            glados.log('LaTeX: Blacklisted commands detected!\n'
                       '  Author: {0}\n  Message: {1}\n  Server: {2}\n  Channel: {3}'.format(
                message.author.name,
                message.content,
                message.server.name,
                message.channel.name
            ))
            await self.client.send_message(message.channel, "Error: Trying to be naughty, are we?")
            return

        # check if this is an edited message
        if message.edited_timestamp:
            last_msg = self.__last_messages.pop(message.author.id, None)
            if last_msg is not None and last_msg[0].id == message.id:
                await self.client.delete_message(last_msg[1])

        # troll Cul
        if message.author.id == '113128686969958400' and random.random() < 0.02:
            content = "\\color{pink} \\text{CulDeVu  loves dongers}"

        fn = self.generate_image(content, self.circuit)

        if not fn[0]:
            await self.client.send_message(message.channel, fn[1])
            return
        if os.path.getsize(fn[1]) > 0:
            try:
                self.__last_messages[message.author.id] = (
                    message,
                    await self.client.send_file(message.channel, fn[1])
                )
            except discord.errors.Forbidden:
                error = 'Error: Insufficient permissions to send file files to channel #{}'.format(message.channel.name)
                glados.log(error)
                await self.client.send_message(message.channel, error)

