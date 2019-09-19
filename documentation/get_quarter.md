# Get Quarter 

The `get_quarter` method returns the current quarter(s) at UW based on the current date.

### Import

```python
from uwtools import get_quarter

or

import uwtools.get_quarter
```

### Args

Arg | Type | Default | Description
--- | --- | --- | ---
`filter_` | `bool` | `False` | Filters out the A and B terms of Summer Quarter if necessary if `True` otherwise does not.
`type_` | `str` | `'current'` | `'current'`: Get the current quarter at UW.<br/>`'upcoming'`: Get the upcoming quarter at UW.

### Returns

The following calls to `get_quarter` will yield the corresponding results:

Parameters | Date| Result
--- | --- | ---
`filter_=False`<br/>`type_='current'` | June 30, 2019 | SUM, SUMA, SUMB
`filter_=True`<br/>`type_='current'` | June 30, 2019 | SUM
`filter_=True`<br/>`type_='upcoming'` | June 30, 2019 | AUT