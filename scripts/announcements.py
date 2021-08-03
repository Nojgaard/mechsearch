import sys


class BColors:
    # ANSI codes
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'

    ENDC = '\033[0m'
    NORMAL = '\033[0m'


def color(acolor: str, string: str) -> str:
    return getattr(BColors, acolor) + string + BColors.ENDC


def message(print_this: str, c: str = "NORMAL", verbose: int = 1, end: str = "\n", function_name: str = None,
            lead_symbol: str = "#", verbose_level_threshold: int = 1):
    """
    A function for priting messages.
    :param print_this: Message to print
    :param c: print color
    :param verbose: verbose
    :param verbose_level_threshold: This hurdle needs to be overcome in oder to get verbose
    :param end: end argument of the print() function
    :param function_name: For referring to a function name
    :param lead_symbol: Symbol prepended to the message
    """

    if verbose is None:
        return None

    if verbose < verbose_level_threshold:
        return None

    if isinstance(print_this, list) is True:
        print_this = " ".join(map(str, print_this))
    elif isinstance(print_this, str) is not True:
        print_this = str(print_this)

    if function_name is not None:
        print_this = f"{function_name}(): {print_this}"

    if lead_symbol != "":
        lead_symbol = f"{lead_symbol} "

    lines = print_this.splitlines()
    if len(lines) == 1:
        print(f"{lead_symbol}{color(c, print_this)}", end=end)
    elif len(lines) > 1:
        for line_id, line in enumerate(lines):
            if function_name is not None:
                if line_id == 0:
                    print(f"{lead_symbol}{color(c, line)}")
                else:
                    print(f"{lead_symbol}{color(c, ' ' * (len(function_name) + 4) + line)}")
            else:
                print(f"{lead_symbol}{color(c, line)}")


def warning_m(print_this: str, c: str = "YELLOW", verbose: int = 1, function_name: str = None,
              verbose_threshold: int = 1):
    message(print_this,
            c=c,
            lead_symbol="@",
            verbose=verbose,
            function_name=function_name,
            verbose_level_threshold=verbose_threshold)


def error_m(print_this: str, c: str = "RED", function_name: str = None):
    message(print_this, c=c, lead_symbol="!", verbose=True, function_name=function_name)
    print(color(c, "Aborting!"))
    sys.exit()


def locator(number: int, c: str = "RED"):
    message(f"\n{'$'*20}", c=c, lead_symbol="")
    message(f"${number:^18d}$", lead_symbol="", c=c)
    message(f"{'$'*20}\n", c=c, lead_symbol="")


def bool_color(this: bool) -> str:
    if this:
        return color("GREEN", f"{this}")
    elif not this:
        return color("RED", f"{this}")
