import random
import os
import subprocess
import glados
import discord


LATEX_FRAMEWORK = r"""
\documentclass[varwidth=true]{standalone}
\usepackage{amsmath}
\usepackage{color}
\usepackage[usenames,dvipsnames,svgnames,table]{xcolor}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{esint}
\usepackage{listings}
\usepackage{mathtools}

\DeclarePairedDelimiter\ceil{\lceil}{\rceil}
\DeclarePairedDelimiter\floor{\lfloor}{\rfloor}

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
{\color{orange}
\begin{align*}
__DATA__
\end{align*}}
\end{document}
"""


class LaTeX(glados.Module):

    def __init__(self, settings):
        super(LaTeX, self).__init__(settings)

        self.__out_folder = 'tex'
        self.__latex_blacklist = ("\\write18",
                                  "\\input",
                                  "\\include",
                                  "{align*}",
                                  "\\loop",
                                  "\\repeat",
                                  "\\csname",
                                  "\\endcsname")

    def get_help_list(self):
        return [
            glados.Help('math', '<latex code>', 'Render latex math code')
        ]

    def generate_image(self, latex):

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
            latex = LATEX_FRAMEWORK.replace('__DATA__', latex)
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

    @glados.Module.commands('math')
    def on_message(self, client, message, content):

        if content == '':
            yield from self.provide_help('math', client, message)
            return

        if any(x in content for x in self.__latex_blacklist):
            glados.log('LaTeX: Blacklisted commands detected!\n'
                       '  Author: {0}\n  Message: {1}\n  Server: {2}\n  Channel: {3}'.format(
                message.author.name,
                message.content,
                message.server.name,
                message.channel.name
            ))
            yield from client.send_message(message.channel, "Error: Trying to be naughty, are we?")
            return

        # troll dsm
        #if message.author.name == "dsm":
        #    content = "!tex \\color{pink} \\text {dsm loves dongers}"

        fn = self.generate_image(content)

        if not fn[0]:
            yield from client.send_message(message.channel, fn[1])
            return
        if os.path.getsize(fn[1]) > 0:
            try:
                yield from client.send_file(message.channel, fn[1])
            except discord.errors.Forbidden:
                error = 'Error: Insufficient permissions to send file files to channel #{}'.format(message.channel.name)
                glados.log(error)
                yield from client.send_message(message.channel, error)
