from qw.base import QwError
import qw.github
import qw.service

def get_service(conf: object = None) -> qw.service.Service:
    if conf is None:
        conf = qw.service.get_configuration()
    name = conf.get("service", None)
    if name is None:
        msg = "Configuration is corrupt. Please run `qw init`"
        raise QwError(
            msg,
        )
    if name == str(qw.service.Service.github):
        return qw.service.Service(conf)
    msg = f"Do not know how to connect to the {name} service!"
    raise QwError(
        msg,
    )
