"""
This is really a minimalistic SSH shell client for specific cases.
It uses an interactive shell but is geared towards automation.

A suitable case is to use this client to communicate with
strange environments, like a VyOS or chopped rbash envs.

By meanhero@gmail.com
"""

import re
import paramiko


class AutoShell:

    def __init__(self, host, user, psw, port=22):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=psw, port=port)

        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

        self.execute("date")

    def __del__(self):
        self.ssh.close()

    def execute(self, cmd):
        """
        Execute command on remote server over SSH

        @param cmd: (str) string shell command or multiple

        @return: ([type]), [description]
        """

        out = []
        err = []
        rc = 0

        cmd = cmd.strip('\n')
        cmd = cmd.strip('\\')

        if not cmd:
            return  rc, out, err

        self.stdin.write(cmd + '\n')
        finish = 'endOfBuffer. Retcode'
        echo_cmd = 'echo {} $?'.format(finish)
        self.stdin.write(echo_cmd + '\n')
        self.stdin.flush()

        for line in self.stdout:
            # if str(line).startswith(cmd) or str(line).startswith(echo_cmd):
            #     # up for now filled with shell junk from stdin
            #     out = []
            if str(line).startswith(finish):
                # our finish command ends with the exit status
                exit_status = int(str(line).rsplit(' ', 1)[1])
                if exit_status:
                    # stderr is combined with stdout.
                    # thus, swap sherr with shout in a case of failure.
                    err = out
                    out = []
                break
            else:
                # get rid of 'coloring and formatting' special characters
                out.append(re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).
                             replace('\b', '').replace('\r', ''))

        # first and last lines of shout/sherr contain a prompt
        if out and echo_cmd in out[-1]:
            out.pop()
        if out and cmd in out[0]:
            out.pop(0)
        if err and echo_cmd in err[-1]:
            err.pop()
        if err and cmd in err[0]:
            err.pop(0)

        return  rc, out, err
