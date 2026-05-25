from cuid import cuid
from functools import partial
from charidfield import CharIDField as _CUIDCharIdField


CharIDField = partial(
    _CUIDCharIdField,
    default=cuid,
    max_length=40,
    help_text="cuid-format identifier for this entity."
)
