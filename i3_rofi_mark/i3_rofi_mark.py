import json
import logging
import argparse
import subprocess

LOGGER = logging.getLogger()


def rofi_prompt(prompt, choices, values=None, non_empty_reply=False):
    p = subprocess.Popen(
        ['rofi', '-dmenu', '-p', prompt],
        stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    choice_string = '\n'.join(choices)
    reply, _ = p.communicate(choice_string.encode('utf8'))
    reply_value = reply.strip().decode('utf8')
    if non_empty_reply:
        assert reply_value, "Expect non-empty reply value."
    if values is not None:
        try:
            reply_idx = choices.index(reply_value)
            return values[reply_idx]
        except ValueError:
            # If not found in values, return as is.
            pass
    return reply_value


def get_marks():
    marks = json.loads(subprocess.check_output(
        ["i3-msg", "-t", 'get_marks'], stderr=subprocess.PIPE))
    return marks


def mark_window(mark):
    subprocess.check_call(
        ["i3-msg", "-t", "command", "mark {}".format(mark)])


def select_window(mark):
    command = ['i3-msg', '-t', 'command',
               '[con_mark="^{}$"] focus'.format(mark)]
    LOGGER.debug('Running: %r', command)
    subprocess.check_call(command)


def unmark(mark):
    subprocess.check_call(
        ["i3-msg", "-t", "command", "unmark {}".format(mark)])


def build_parser():
    parser = argparse.ArgumentParser(description='', prog='i3-rofi-mark')
    parser.add_argument('--debug', action='store_true',
                        help='Include debug output (to stderr)')
    parser.add_argument('--prefix', type=str, help='Show or add this prefix')
    parsers = parser.add_subparsers(dest='command')
    parsers.required = True
    mark_parser = parsers.add_parser('mark')
    goto_parser = parsers.add_parser('goto')
    goto_parser = parsers.add_parser('unmark')
    return parser


def main():
    args = build_parser().parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    marks = get_marks()
    if args.command == 'goto':
        if args.prefix is not None:
            marks = [mark[args.prefix:]
                     for mark in get_marks() if mark.startswith(args.prefix)]

        LOGGER.debug('marks: %r', marks)
        window = rofi_prompt("Goto", marks, non_empty_reply=True)
        if args.prefix is not None:
            window = args.prefix + window
        LOGGER.debug('Selecting window %r', window)
        select_window(window)
    elif args.command == 'mark':
        mark = rofi_prompt("Mark Window", marks, non_empty_reply=True)
        if args.prefix is not None:
            mark = args.prefix + mark
        LOGGER.debug('Marking with %r', mark)
        mark_window(mark)
    elif args.command == 'unmark':
        if args.prefix is not None:
            marks = [mark[len(args.prefix):]
                     for mark in get_marks() if mark.startswith(args.prefix)]

        mark = rofi_prompt(
            "Remove Mark", ["(Remove All)"] + marks, values=[""] + marks, non_empty_reply=True)
        if args.prefix:
            mark = args.prefix + mark
        unmark(mark)
    else:
        raise ValueError(args.command)


if __name__ == "__main__":
    main()
