from typing import Iterable, Type

from loguru import logger

from qw.design_stages._base import DesignBase
from qw.design_stages.categories import RemoteItemType

class _Check:
    def __init__(
        self,
        func,
        **kwargs,
    ) -> None:
        self.func = func
        self.title = kwargs.get('title', func.__name__)
        self.description = kwargs.get('description', func.__doc__)
        self.fail_title = kwargs.get('fail_title', func.__name__)
        self.fail_item = kwargs.get('fail_item', None)

    def apply_to(self, obj: DesignBase, **kwargs) -> list[str]:
        """
        Run the check against the argument.

        :param obj: An object of a subclass of DesignBase.
        :return: list of strings to be displayed to the user describing failures.
        """
        r = self.func(obj, **kwargs)
        if not bool(r):
            return []
        title = self.fail_title.format(obj)
        if self.fail_item is None:
            if isinstance(r, str):
                return [title, r]
            return [title]
        if isinstance(r, str):
            return [title, self.fail_item.format(r)]
        if not isinstance(r, Iterable):
            return [title]
        out = [title]
        for item in r:
            out.append(self.fail_item.format(item))
        return out


_CHECKS: dict[str, _Check] = {}


class CheckResult:
    """
    Results from checking.
    
    Has the following public properties:
    :prop failures: human-readable failure list
    :prop object_count: the number of objects tested
    :prop check_count: the total number of checks run on all objects
    """
    def __init__(self, failures, object_count, check_count):
        self.failures = failures
        self.object_count = object_count
        self.check_count = check_count


def run_checks(
    stages: list[Type[DesignBase]],
    issues: set[int] | None=None,
    prs: set[int] | None=None,
    **kwargs,
) -> CheckResult:
    """
    Run checks against design stages.

    :issues: Set of issue numbers to check.
    :prs: Set of PR numbers to check.
    :return: List of error strings. Will be empty if no errors.
    """
    class_dict_args: dict[str, dict[int, Type[DesignBase]]] = {}
    for stage_class in DesignBase.__subclasses__():
        class_dict_args[stage_class.plural] = {}
    # Create the arguments the checks might use
    for stage in stages:
        d = class_dict_args[stage.plural][stage.internal_id] = stage
    # Find the stages we actually want to test
    wanted: list[DesignBase] = []
    if prs is None and issues is None:
        wanted = stages
        logger.debug("All stages ({})", len(wanted))
    else:
        if prs is None:
            prs = set()
        if issues is None:
            issues = set()
        for stage in stages:
            if stage.remote_item_type == RemoteItemType.REQUEST:
                if stage.internal_id in prs:
                    wanted.append(stage)
            else:
                if stage.internal_id in issues:
                    wanted.append(stage)
    # Run the checks
    count = 0
    result: list[str] = []
    for stage in wanted:
        logger.debug("Checking {} {}", stage.__class__.__name__, stage.internal_id)
        for check in _CHECKS.get(stage.__class__.__name__, []):
            logger.debug(".. Check {}", check.title)
            count += 1
            result.extend(check.apply_to(stage, **class_dict_args))
    return CheckResult(result, len(wanted), count)


def check(title: str, fail_title: str, **kwargs):
    """
    Decorate f so that it is a check to be run with `qw check`

    The function should return a Falsey value if the check passes, or
    a Truthy value if the check fails.

    The user will see the fail_title if the check fails, formatted with the
    single argument that is the DesignBase object that caused the failure,
    so you can use interpolations such as {0.title} in your string.

    If fail_item is provided and the check returns a string, fail_item will
    be printed formatted with this returned string.

    If fail_item is provided and the check returns an iterable (that is not
    a string) fail_item will be printed formatted with each item of the
    iteration in turn.

    If fail_item is not provided and a string is returned the string will
    be printed as well as fail_title.

    The wrapped function will accept, as arguments, the object under
    scrutiny followed by keyword arguments like user_needs, requirements
    and design_outputs that pass dicts mapping internal ids to the
    DesignBase objects found.

    :param title: Human-readable name of the check.
    :param fail_title: The description that the user will get if the check
    fails.
    :param fail_item: A further piece of the failure description describing
    each sub-failure.
    :param description: Human-readable description of the check; if not
    provided, the functions docstring will be used.
    """
    def decorator(f):
        class_name = f.__qualname__.split('.')[0]
        if class_name not in _CHECKS:
            _CHECKS[class_name] = []
        _CHECKS[class_name].append(_Check(
            f,
            title=title,
            fail_title=fail_title,
            **kwargs,
        ))
        return f
    return decorator
